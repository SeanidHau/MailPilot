from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.router import api_router
from app.db.session import SessionLocal
from app.services.job_service import recover_stale_jobs
import logging

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()
    try:
        recover_stale_jobs(db)
    except Exception:
        # Migrations may run separately from application startup.
        logger.exception("background_job_recovery_failed")
    finally:
        db.close()
    yield


app = FastAPI(title="MailPilot", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
