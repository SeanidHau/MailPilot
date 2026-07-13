import pytest
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
import os

from app.main import app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")


@pytest.fixture(scope="function")
def engine():
    connect_args = {"check_same_thread": False} if TEST_DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(TEST_DATABASE_URL, connect_args=connect_args)
    Base.metadata.create_all(bind=engine)
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
def client(db_session):
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
    resp = client.post("/api/auth/register", json={"email": "test@test.dev", "password": "123456"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
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
