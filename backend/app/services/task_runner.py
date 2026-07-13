"""In-process executor for work that must not block an HTTP response."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from app.services import job_service


_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mailpilot-job")


def schedule_job(
    job_id: int,
    user_id: int,
    job_type: str,
    bind: Any,
    payload: list[dict] | None = None,
) -> None:
    _executor.submit(job_service.run_job, job_id, user_id, job_type, bind, payload)

