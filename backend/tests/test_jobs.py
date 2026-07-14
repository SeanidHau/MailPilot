from datetime import datetime


def test_gmail_sync_reuses_active_job(client, monkeypatch):
    from app.services import task_runner

    monkeypatch.setattr(task_runner, "schedule_job", lambda *args, **kwargs: None)
    register = client.post(
        "/api/auth/register",
        json={"email": "sync-active@example.com", "password": "123456"},
    )
    client.headers["Authorization"] = f"Bearer {register.json()['access_token']}"

    first = client.post("/api/sync/gmail")
    second = client.post("/api/sync/gmail")

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["job_id"] == first.json()["job_id"]
    assert second.json()["status"] == "queued"


def test_outlook_sync_reuses_active_job(client, monkeypatch):
    from app.services import task_runner

    monkeypatch.setattr(task_runner, "schedule_job", lambda *args, **kwargs: None)
    register = client.post(
        "/api/auth/register",
        json={"email": "outlook-sync-active@example.com", "password": "123456"},
    )
    client.headers["Authorization"] = f"Bearer {register.json()['access_token']}"

    first = client.post("/api/sync/outlook")
    second = client.post("/api/sync/outlook")

    assert first.status_code == 202
    assert second.status_code == 202
    assert second.json()["job_id"] == first.json()["job_id"]
    assert second.json()["status"] == "queued"


def test_upload_import_runs_as_background_job(auth_client):
    response = auth_client.post(
        "/api/emails/import/upload",
        json=[
            {
                "message_id": "async-upload-001",
                "sender": "alice@example.com",
                "recipients": "me@example.com",
                "subject": "Async import",
                "body": "Please review this message.",
                "received_at": datetime(2026, 7, 13, 10, 0).isoformat(),
            }
        ],
    )

    assert response.status_code == 202
    job_id = response.json()["job_id"]
    job = auth_client.get(f"/api/jobs/{job_id}")
    assert job.status_code == 200
    assert job.json()["status"] == "completed"
    assert job.json()["result"]["imported"] == 1


def test_job_is_user_scoped(auth_client, client):
    response = auth_client.post("/api/emails/import")
    job_id = response.json()["job_id"]

    other_user = client.post(
        "/api/auth/register",
        json={"email": "job-other@example.com", "password": "123456"},
    )
    other_token = other_user.json()["access_token"]
    response = client.get(
        f"/api/jobs/{job_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_manual_ai_processing_only_processes_incomplete_emails(auth_client, db_session):
    from app.db.models import Email

    email = Email(
        message_id="manual-ai-001",
        sender="alice@example.com",
        recipients="me@example.com",
        subject="Needs AI processing",
        body="Please review this message.",
        received_at=datetime(2026, 7, 13, 10, 0),
        user_id=auth_client.get("/api/auth/me").json()["id"],
    )
    db_session.add(email)
    db_session.commit()

    response = auth_client.post("/api/emails/process-ai")
    assert response.status_code == 202
    job = auth_client.get(f"/api/jobs/{response.json()['job_id']}").json()
    assert job["status"] == "completed"
    assert job["result"]["processed"] == 1

    response = auth_client.post("/api/emails/process-ai")
    job = auth_client.get(f"/api/jobs/{response.json()['job_id']}").json()
    assert job["result"]["processed"] == 0


def test_ai_job_can_request_pause(client, monkeypatch):
    from app.services import task_runner

    monkeypatch.setattr(task_runner, "schedule_job", lambda *args, **kwargs: None)
    register = client.post(
        "/api/auth/register",
        json={"email": "pause-ai@example.com", "password": "123456"},
    )
    client.headers["Authorization"] = f"Bearer {register.json()['access_token']}"

    response = client.post("/api/emails/process-ai")
    job_id = response.json()["job_id"]
    pause_response = client.post(f"/api/jobs/{job_id}/pause")

    assert pause_response.status_code == 200
    assert pause_response.json()["status"] == "pause_requested"


def test_ai_processing_pauses_between_emails(db_session, monkeypatch):
    from app.db.models import Email
    from app.services import email_service
    from app.ai.metadata import make_metadata

    processed_subjects: list[str] = []
    user_id = 1
    first = Email(
        message_id="ai-pause-first",
        sender="first@example.com",
        recipients="me@example.com",
        subject="First",
        body="First body",
        received_at=datetime(2026, 7, 12, 10, 0),
        user_id=user_id,
    )
    second = Email(
        message_id="ai-pause-second",
        sender="second@example.com",
        recipients="me@example.com",
        subject="Second",
        body="Second body",
        received_at=datetime(2026, 7, 11, 10, 0),
        user_id=user_id,
    )
    db_session.add_all([first, second])
    db_session.commit()

    def fake_process_email(db, email_id, current_user_id):
        email = db.query(Email).filter(Email.id == email_id, Email.user_id == current_user_id).one()
        processed_subjects.append(email.subject)
        email.summary = f"summary: {email.subject}"
        email.ai_metadata = make_metadata("FakeProvider", "fake-model")
        db.commit()
        return []

    monkeypatch.setattr(email_service, "process_email_with_ai", fake_process_email)

    result = email_service.process_unprocessed_emails(
        db_session,
        user_id,
        should_pause=lambda: len(processed_subjects) >= 1,
    )

    remaining = db_session.query(Email).filter(Email.user_id == user_id, Email.summary.is_(None)).one()
    assert result["paused"] is True
    assert result["processed"] == 1
    assert processed_subjects == ["First"]
    assert remaining.subject == "Second"


def test_ai_processing_prioritizes_new_mail_added_during_run(db_session, monkeypatch):
    from app.db.models import Email
    from app.services import email_service
    from app.ai.metadata import make_metadata

    processed_subjects: list[str] = []
    user_id = 1
    older = Email(
        message_id="ai-priority-old",
        sender="old@example.com",
        recipients="me@example.com",
        subject="Older backlog",
        body="Old body",
        received_at=datetime(2026, 7, 10, 10, 0),
        user_id=user_id,
    )
    newer = Email(
        message_id="ai-priority-new",
        sender="new@example.com",
        recipients="me@example.com",
        subject="Newest initial",
        body="New body",
        received_at=datetime(2026, 7, 12, 10, 0),
        user_id=user_id,
    )
    db_session.add_all([older, newer])
    db_session.commit()

    def fake_process_email(db, email_id, current_user_id):
        email = db.query(Email).filter(Email.id == email_id, Email.user_id == current_user_id).one()
        processed_subjects.append(email.subject)
        email.summary = f"summary: {email.subject}"
        email.ai_metadata = make_metadata("FakeProvider", "fake-model")
        if email.subject == "Newest initial":
            db.add(Email(
                message_id="ai-priority-arrived-during-run",
                sender="fresh@example.com",
                recipients="me@example.com",
                subject="Arrived during run",
                body="Fresh body",
                received_at=datetime(2026, 7, 14, 10, 0),
                user_id=current_user_id,
            ))
        db.commit()
        return []

    monkeypatch.setattr(email_service, "process_email_with_ai", fake_process_email)

    result = email_service.process_unprocessed_emails(db_session, user_id)

    assert result["processed"] == 3
    assert processed_subjects == [
        "Newest initial",
        "Arrived during run",
        "Older backlog",
    ]
