from datetime import datetime


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
