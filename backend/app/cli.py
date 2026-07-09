from __future__ import annotations

import logging
from pathlib import Path

import typer
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from sqlalchemy import make_url, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.models import Draft, Email, Reminder, User
from app.db.session import SessionLocal, engine
from app.services.auth_service import register_user
from app.services.draft_service import generate_draft
from app.services.email_service import classify_email, import_mock_emails, summarize_email
from app.services.reminder_service import extract_reminders

logger = logging.getLogger("mailpilot.cli")

app = typer.Typer(help="MailPilot backend management CLI")

DEFAULT_DEMO_EMAIL = "demo@mailpilot.dev"
DEFAULT_DEMO_PASSWORD = "demo123"


class UnsafeDatabaseError(typer.Exit):
    pass


def _get_alembic_config() -> AlembicConfig:
    """Build an Alembic config pointing at the current DATABASE_URL."""
    alembic_ini = Path(__file__).parent.parent / "alembic.ini"
    if not alembic_ini.exists():
        # Fallback: assume the command is run from the project root.
        alembic_ini = Path("alembic.ini")
    cfg = AlembicConfig(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def _run_migrations(command: str, revision: str) -> None:
    cfg = _get_alembic_config()
    if command == "upgrade":
        alembic_command.upgrade(cfg, revision)
    elif command == "downgrade":
        alembic_command.downgrade(cfg, revision)
    else:
        raise ValueError(f"Unknown migration command: {command}")


def _stamp_head() -> None:
    """Stamp the database with the current Alembic head revision."""
    cfg = _get_alembic_config()
    alembic_command.stamp(cfg, "head")


def _is_local_database(url: str) -> bool:
    parsed = make_url(url)
    if parsed.drivername.startswith("sqlite"):
        return True
    return parsed.host in ("localhost", "127.0.0.1", "::1")


def _database_display(url: str) -> str:
    parsed = make_url(url)
    if parsed.drivername.startswith("sqlite"):
        return f"SQLite ({parsed.database or url})"
    return f"{parsed.host}:{parsed.port or 5432}/{parsed.database}"


def _ensure_schema() -> None:
    """Create the schema using Alembic for PostgreSQL or SQLAlchemy metadata for SQLite."""
    if settings.database_url.startswith("sqlite"):
        # SQLite migrations use ALTER CONSTRAINT operations that are not supported
        # by the SQLite dialect. Use metadata directly for local SQLite development/tests.
        Base.metadata.create_all(bind=engine)
        _stamp_head()
    else:
        _run_migrations("upgrade", "head")


def _reset_schema() -> None:
    """Drop and recreate the schema, leaving the database at Alembic head."""
    Base.metadata.drop_all(bind=engine)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()

    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        _stamp_head()
    else:
        _run_migrations("upgrade", "head")


def _get_or_create_demo_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is not None:
        return user
    user = register_user(db, email, password)
    if user is None:
        raise RuntimeError(f"Failed to create demo user: {email}")
    return user


def _seed_demo_data(
    db: Session,
    email: str,
    password: str,
    no_ai: bool = False,
    no_drafts: bool = False,
    no_reminders: bool = False,
) -> dict:
    user = _get_or_create_demo_user(db, email, password)
    assert user.id is not None

    imported = import_mock_emails(db, user.id)
    emails = db.query(Email).filter(Email.user_id == user.id).all()

    classified = 0
    summarized = 0
    if not no_ai:
        for email_obj in emails:
            classify_email(db, email_obj.id, user.id)
            classified += 1
            summarize_email(db, email_obj.id, user.id)
            summarized += 1

    draft_count = 0
    if not no_ai and not no_drafts:
        for email_obj in emails[:3]:
            existing = (
                db.query(Draft)
                .filter_by(user_id=user.id, email_id=email_obj.id, tone="formal")
                .first()
            )
            if existing is not None:
                continue
            draft, _ = generate_draft(db, email_obj.id, "formal", user.id)
            if draft is not None:
                draft_count += 1

    reminder_count = 0
    if not no_ai and not no_reminders:
        for email_obj in emails:
            existing = (
                db.query(Reminder).filter_by(user_id=user.id, email_id=email_obj.id).first()
            )
            if existing is not None:
                continue
            created, _ = extract_reminders(db, email_obj.id, user.id)
            reminder_count += len(created)

    return {
        "user": user,
        "imported": imported,
        "classified": classified,
        "summarized": summarized,
        "drafts": draft_count,
        "reminders": reminder_count,
    }


@app.command()
def seed(
    email: str = typer.Option(DEFAULT_DEMO_EMAIL, "--email", "-e", help="Demo user email"),
    password: str = typer.Option(
        DEFAULT_DEMO_PASSWORD, "--password", "-p", help="Demo user password"
    ),
    no_ai: bool = typer.Option(
        False, "--no-ai", help="Skip AI classification, summarization, drafts and reminders"
    ),
    no_drafts: bool = typer.Option(False, "--no-drafts", help="Skip generating reply drafts"),
    no_reminders: bool = typer.Option(
        False, "--no-reminders", help="Skip extracting reminders"
    ),
):
    """Seed the database with local demo data."""
    _ensure_schema()
    db = SessionLocal()
    try:
        result = _seed_demo_data(
            db,
            email,
            password,
            no_ai=no_ai,
            no_drafts=no_drafts,
            no_reminders=no_reminders,
        )
        user = result["user"]
        typer.echo(f"Demo user: {user.email} (id={user.id})")
        typer.echo(f"Imported emails: {result['imported']}")
        if not no_ai:
            typer.echo(f"Classified emails: {result['classified']}")
            typer.echo(f"Summarized emails: {result['summarized']}")
        if not no_ai and not no_drafts:
            typer.echo(f"Generated drafts: {result['drafts']}")
        if not no_ai and not no_reminders:
            typer.echo(f"Extracted reminders: {result['reminders']}")
        typer.echo("Demo data seeded successfully.")
    finally:
        db.close()


@app.command()
def reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    force: bool = typer.Option(
        False, "--force", help="Allow reset on non-localhost databases"
    ),
    seed_after: bool = typer.Option(
        False, "--seed", help="Seed demo data after resetting the database"
    ),
    email: str = typer.Option(DEFAULT_DEMO_EMAIL, "--email", "-e", help="Demo user email"),
    password: str = typer.Option(
        DEFAULT_DEMO_PASSWORD, "--password", "-p", help="Demo user password"
    ),
    no_ai: bool = typer.Option(
        False,
        "--no-ai",
        help="When used with --seed, skip AI classification/summarization/drafts/reminders",
    ),
):
    """Drop and recreate the database schema using Alembic migrations."""
    if not _is_local_database(settings.database_url) and not force:
        typer.echo(
            f"Error: reset refused for non-local database ({settings.database_url}). "
            "Use --force to override only if you are sure.",
            err=True,
        )
        raise typer.Exit(code=1)

    display = _database_display(settings.database_url)
    if not yes:
        typer.confirm(
            f"This will DELETE ALL DATA in {display}. Continue?",
            abort=True,
        )

    _reset_schema()
    typer.echo("Database reset complete (Alembic migrations applied).")

    if seed_after:
        db = SessionLocal()
        try:
            result = _seed_demo_data(db, email, password, no_ai=no_ai)
            user = result["user"]
            typer.echo(f"Demo user: {user.email} (id={user.id})")
            typer.echo(f"Imported emails: {result['imported']}")
            if not no_ai:
                typer.echo(f"Classified emails: {result['classified']}")
                typer.echo(f"Summarized emails: {result['summarized']}")
                typer.echo(f"Generated drafts: {result['drafts']}")
                typer.echo(f"Extracted reminders: {result['reminders']}")
            typer.echo("Demo data seeded after reset.")
        finally:
            db.close()


if __name__ == "__main__":
    app()
