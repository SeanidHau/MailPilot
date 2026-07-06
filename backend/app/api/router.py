from fastapi import APIRouter

from app.api.routes import emails, drafts, reminders, dashboard, feedback

api_router = APIRouter()
api_router.include_router(emails.router, tags=["emails"])
api_router.include_router(drafts.router, tags=["drafts"])
api_router.include_router(reminders.router, tags=["reminders"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(feedback.router, tags=["feedback"])


@api_router.get("/health")
def health():
    return {"status": "ok"}
