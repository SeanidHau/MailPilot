from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from app import cli
from app.core.config import settings
from app.db.base import Base

runner = CliRunner()


@pytest.fixture
def cli_db(monkeypatch):
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db_url = f"sqlite:///{db_path}"

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    monkeypatch.setattr(settings, "database_url", db_url)
    monkeypatch.setattr(cli, "engine", engine)
    monkeypatch.setattr(cli, "SessionLocal", SessionLocal)

    # Initialize schema for SQLite tests.
    cli._ensure_schema()

    try:
        yield db_path
    finally:
        engine.dispose()
        Path(db_path).unlink(missing_ok=True)


def _alembic_version() -> str | None:
    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        try:
            row = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            return row[0] if row else None
        finally:
            conn.commit()


def test_seed_creates_demo_data(cli_db):
    result = runner.invoke(
        cli.app, ["seed", "--email", "demo@test.dev", "--password", "demo123"]
    )
    assert result.exit_code == 0, result.output
    assert "Demo user: demo@test.dev" in result.output
    assert "Imported emails: 8" in result.output
    assert "Classified emails: 8" in result.output
    assert "Summarized emails: 8" in result.output
    assert "Generated drafts: 3" in result.output


def test_seed_no_ai(cli_db):
    result = runner.invoke(
        cli.app,
        [
            "seed",
            "--email",
            "demo@test.dev",
            "--password",
            "demo123",
            "--no-ai",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Imported emails: 8" in result.output
    assert "Classified emails: 8" not in result.output
    assert "Summarized emails: 8" not in result.output


def test_seed_is_idempotent(cli_db):
    first = runner.invoke(
        cli.app, ["seed", "--email", "demo@test.dev", "--password", "demo123"]
    )
    assert first.exit_code == 0

    second = runner.invoke(
        cli.app, ["seed", "--email", "demo@test.dev", "--password", "demo123"]
    )
    assert second.exit_code == 0, second.output
    assert "Imported emails: 0" in second.output
    assert "Generated drafts: 0" in second.output
    assert "Extracted reminders: 0" in second.output


def test_reset_applies_migrations_and_seeds(cli_db):
    seed_result = runner.invoke(
        cli.app, ["seed", "--email", "demo@test.dev", "--password", "demo123"]
    )
    assert seed_result.exit_code == 0

    reset_result = runner.invoke(
        cli.app,
        [
            "reset",
            "--yes",
            "--seed",
            "--email",
            "demo@test.dev",
            "--password",
            "demo123",
        ],
    )
    assert reset_result.exit_code == 0, reset_result.output
    assert "Database reset complete (Alembic migrations applied)" in reset_result.output
    assert "Demo data seeded after reset" in reset_result.output
    assert "Imported emails: 8" in reset_result.output
    assert _alembic_version() is not None


def test_reset_refuses_non_local_database(monkeypatch):
    monkeypatch.setattr(
        settings, "database_url", "postgresql://user:pass@prod.example.com:5432/mailpilot"
    )
    result = runner.invoke(cli.app, ["reset", "--yes"])
    assert result.exit_code == 1
    assert "non-local database" in result.output


def test_reset_force_allows_non_local_database(monkeypatch):
    monkeypatch.setattr(
        settings, "database_url", "postgresql://user:pass@prod.example.com:5432/mailpilot"
    )
    # --force bypasses the localhost check, but the database does not exist so the
    # command will fail at the connection step. The safety gate itself must pass.
    result = runner.invoke(cli.app, ["reset", "--yes", "--force"])
    assert result.exit_code != 0
    assert "non-local database" not in result.output


def test_reset_prompt_without_yes(cli_db):
    result = runner.invoke(cli.app, ["reset"])
    assert result.exit_code != 0
    assert "Aborted" in result.output or "Error" in result.output


@pytest.mark.skipif(
    not os.environ.get("MAILPILOT_TEST_POSTGRES_URL"),
    reason="Set MAILPILOT_TEST_POSTGRES_URL to run PostgreSQL integration tests",
)
def test_reset_postgresql_schema_has_migration_indexes(monkeypatch):
    """Verify that reset on PostgreSQL produces a schema consistent with migrations.

    This catches regressions where reset bypasses Alembic and omits PostgreSQL-only
    objects such as partial indexes defined in migration scripts.
    """
    pg_url = os.environ["MAILPILOT_TEST_POSTGRES_URL"]
    monkeypatch.setattr(settings, "database_url", pg_url)

    engine = create_engine(pg_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(cli, "engine", engine)
    monkeypatch.setattr(cli, "SessionLocal", SessionLocal)

    result = runner.invoke(cli.app, ["reset", "--yes", "--seed", "--no-ai"])
    assert result.exit_code == 0, result.output
    assert _alembic_version() is not None

    with engine.connect() as conn:
        inspector = inspect(conn)
        indexes = {idx["name"] for idx in inspector.get_indexes("emails")}
        assert "ix_emails_provider_dedup" in indexes, (
            "PostgreSQL reset is missing the partial index from migration "
            "a1a8a121593b_add_sync_dedup_index"
        )

    engine.dispose()
