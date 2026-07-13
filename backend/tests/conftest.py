import pytest
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.models import User
from app.db.session import get_db
import os

from app.main import app
from app.services.auth_service import create_access_token
from app.services import job_service, task_runner

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")


@pytest.fixture(scope="function")
def engine():
    connect_args = {"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(TEST_DATABASE_URL, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)

    # Several service tests intentionally use stable user IDs. Seed those
    # referenced rows so PostgreSQL enforces the same constraints as production.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        session.add_all(
            [
                User(id=1, email="fixture-user-1@test.dev", hashed_password="unused"),
                User(id=3, email="fixture-user-3@test.dev", hashed_password="unused"),
                User(id=7, email="fixture-user-7@test.dev", hashed_password="unused"),
            ]
        )
        session.commit()
        if not TEST_DATABASE_URL.startswith("sqlite"):
            session.execute(
                text("SELECT setval(pg_get_serial_sequence('users', 'id'), 7, true)")
            )
            session.commit()
    finally:
        session.close()

    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session, monkeypatch):
    # API tests still receive 202 responses, but execute the in-process worker
    # inline so fixture teardown cannot drop tables under a live worker thread.
    def run_job_inline(job_id, user_id, job_type, bind, payload=None):
        job_service.run_job(job_id, user_id, job_type, bind, payload)

    monkeypatch.setattr(task_runner, "schedule_job", run_job_inline)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client(client):
    """Client pre-authenticated with a test user."""
    # User 1 is seeded by the engine fixture for service tests that use stable
    # foreign keys. Reuse it here so authenticated API tests keep a stable ID.
    token = create_access_token(1)
    client.headers["Authorization"] = f"Bearer {token}"

    # The production API returns immediately for background jobs. Tests that
    # create fixture emails need to wait before querying the imported records.
    original_post = client.post
    original_put = client.put
    original_get = client.get

    def wait_for_job_response(response, args, kwargs):
        url = str(args[0]) if args else str(kwargs.get("url", ""))
        try:
            response_data = response.json()
        except ValueError:
            response_data = {}
        job_id = response_data.get("job_id")
        if job_id and "/api/jobs/" not in url:
            deadline = time.monotonic() + 10
            while job_id and time.monotonic() < deadline:
                job_response = original_get(f"/api/jobs/{job_id}")
                if job_response.status_code == 200:
                    job_status = job_response.json().get("status")
                    if job_status in {"completed", "failed"}:
                        break
                time.sleep(0.01)
        return response

    def post_and_wait_for_job(*args, **kwargs):
        return wait_for_job_response(original_post(*args, **kwargs), args, kwargs)

    def put_and_wait_for_job(*args, **kwargs):
        return wait_for_job_response(original_put(*args, **kwargs), args, kwargs)

    client.post = post_and_wait_for_job
    client.put = put_and_wait_for_job
    return client
