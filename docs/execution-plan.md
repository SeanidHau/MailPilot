# MailPilot Execution Plan

## 1. MVP Delivery Strategy

Build in thin vertical slices:

1. Project skeleton and local runtime.
2. Database and core models.
3. Mock email import and email browsing.
4. Rule-based AI actions.
5. Drafts and reminders.
6. Dashboard and feedback.
7. Frontend integration.
8. Tests and documentation.

Each phase should leave the application closer to a runnable state.

## 2. Phase 1: Project Skeleton

### Backend Files

Create:

- `backend/pyproject.toml`
- `backend/.env.example`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/core/__init__.py`
- `backend/app/core/config.py`
- `backend/app/api/__init__.py`
- `backend/app/api/router.py`

Implementation:

- Configure FastAPI app.
- Add CORS middleware for the Vite dev server.
- Add `/api/health`.
- Load settings from environment variables.

Acceptance criteria:

- `uvicorn app.main:app --reload --port 8000` starts.
- `GET /api/health` returns a healthy response.

### Frontend Files

Create:

- `frontend/package.json`
- `frontend/index.html`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/src/main.tsx`
- `frontend/src/app/router.tsx`
- `frontend/src/app/queryClient.ts`
- `frontend/src/styles/global.css`

Implementation:

- Configure React, Vite, TypeScript, React Router, and TanStack Query.
- Add placeholder routes for all required pages.

Acceptance criteria:

- `npm run dev` starts.
- The app displays navigation and placeholder pages.

### Root Files

Create or update:

- `docker-compose.yml`
- `README.md`

Implementation:

- Add PostgreSQL service.
- Document basic local startup commands.

## 3. Phase 2: Database And Models

### Files

Create:

- `backend/app/db/__init__.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/app/db/models.py`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/<initial_revision>.py`

Implementation:

- Define SQLAlchemy base and session dependency.
- Define models for emails, drafts, reminders, classification feedback, and settings.
- Configure Alembic to read metadata from SQLAlchemy models.
- Add initial migration.

Acceptance criteria:

- `alembic upgrade head` creates all tables.
- Models can be imported without circular dependency errors.

## 4. Phase 3: Schemas And Shared Types

### Backend Files

Create:

- `backend/app/schemas/__init__.py`
- `backend/app/schemas/email.py`
- `backend/app/schemas/draft.py`
- `backend/app/schemas/reminder.py`
- `backend/app/schemas/feedback.py`
- `backend/app/schemas/dashboard.py`
- `backend/app/schemas/ai.py`

Implementation:

- Define request and response schemas.
- Define enum values for categories, tones, reminder types, and statuses.
- Validate importance score as 1-5.

Acceptance criteria:

- API routes can use schemas for request validation and response serialization.

### Frontend Files

Create:

- `frontend/src/types/email.ts`
- `frontend/src/types/draft.ts`
- `frontend/src/types/reminder.ts`
- `frontend/src/types/dashboard.ts`
- `frontend/src/types/feedback.ts`

Implementation:

- Mirror backend response shapes.
- Keep enum string values aligned with backend.

Acceptance criteria:

- Frontend API wrappers compile with typed responses.

## 5. Phase 4: Email Import And Browsing

### Backend Files

Create:

- `backend/app/mock_data/emails.json`
- `backend/app/services/email_service.py`
- `backend/app/api/routes/__init__.py`
- `backend/app/api/routes/emails.py`

Modify:

- `backend/app/api/router.py`
- `backend/app/main.py`

Implementation:

- Import mock email JSON into the database.
- Avoid duplicate import by `message_id`.
- List emails with pagination and filters.
- Fetch email detail.
- Patch read state, category, or importance score.
- When category changes manually, write a classification feedback record.

Acceptance criteria:

- `POST /api/emails/import` imports sample data.
- `GET /api/emails` returns paginated results.
- Filters work for keyword, category, read status, and importance.
- `GET /api/emails/{id}` returns full email details.
- `PATCH /api/emails/{id}` updates allowed fields.

## 6. Phase 5: AI Provider And Email Actions

### Files

Create:

- `backend/app/ai/__init__.py`
- `backend/app/ai/providers/__init__.py`
- `backend/app/ai/providers/base.py`
- `backend/app/ai/providers/mock.py`
- `backend/app/services/ai_service.py`

Modify:

- `backend/app/api/routes/emails.py`

Implementation:

- Add provider interface.
- Implement mock classification, importance scoring, summarization, draft generation, and reminder extraction.
- Add endpoints for classify, summarize, generate draft, and extract reminders.

Acceptance criteria:

- `POST /api/emails/{id}/classify` updates category and score.
- `POST /api/emails/{id}/summarize` stores and returns summary.
- `POST /api/emails/{id}/drafts` creates draft content for selected tone.
- `POST /api/emails/{id}/reminders/extract` creates reminder records.

## 7. Phase 6: Drafts, Reminders, Dashboard, Feedback APIs

### Files

Create:

- `backend/app/services/draft_service.py`
- `backend/app/services/reminder_service.py`
- `backend/app/services/dashboard_service.py`
- `backend/app/services/feedback_service.py`
- `backend/app/api/routes/drafts.py`
- `backend/app/api/routes/reminders.py`
- `backend/app/api/routes/dashboard.py`
- `backend/app/api/routes/feedback.py`

Modify:

- `backend/app/api/router.py`

Implementation:

- List and update drafts.
- List, complete, update, and soft-delete reminders.
- Provide dashboard summary.
- List and create classification feedback entries.

Acceptance criteria:

- Drafts are editable and saved.
- Reminders can be completed and deleted.
- Dashboard endpoint returns counts and recent items.
- Feedback endpoint returns user classification changes.

## 8. Phase 7: Frontend API Layer

### Files

Create:

- `frontend/src/api/client.ts`
- `frontend/src/api/emails.ts`
- `frontend/src/api/drafts.ts`
- `frontend/src/api/reminders.ts`
- `frontend/src/api/dashboard.ts`
- `frontend/src/api/feedback.ts`

Implementation:

- Centralize API base URL.
- Add typed functions for each backend endpoint.
- Normalize error handling enough for MVP UI messages.

Acceptance criteria:

- Pages can call backend through typed API functions.
- API base URL can be configured with `VITE_API_BASE_URL`.

## 9. Phase 8: Frontend Layout And Components

### Files

Create:

- `frontend/src/components/Layout.tsx`
- `frontend/src/components/StatCard.tsx`
- `frontend/src/components/EmailTable.tsx`
- `frontend/src/components/EmailFilters.tsx`
- `frontend/src/components/CategoryBadge.tsx`
- `frontend/src/components/ImportanceRating.tsx`
- `frontend/src/components/DraftEditor.tsx`
- `frontend/src/components/ReminderList.tsx`

Implementation:

- Build a clean productivity-tool layout.
- Use clear navigation for Dashboard, Emails, Drafts, Reminders, and Settings.
- Use stable table/list layouts with loading and empty states.

Acceptance criteria:

- Shared UI components render correctly on desktop and mobile widths.
- Text does not overflow buttons, cards, or filters.

## 10. Phase 9: Frontend Pages

### Files

Create:

- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/EmailsPage.tsx`
- `frontend/src/pages/EmailDetailPage.tsx`
- `frontend/src/pages/DraftsPage.tsx`
- `frontend/src/pages/RemindersPage.tsx`
- `frontend/src/pages/SettingsPage.tsx`

Implementation:

- Dashboard shows summary metrics and recent items.
- Emails page supports search and filters.
- Email detail supports manual classification, summary generation, draft generation, and reminder extraction.
- Drafts page supports editing and saving.
- Reminders page supports completion and deletion.
- Settings page supports mock email import and shows future AI/mailbox placeholders.

Acceptance criteria:

- User can complete the main MVP flow from the browser:
  1. Import mock email data.
  2. View dashboard counts.
  3. Search and filter emails.
  4. Open an email.
  5. Generate summary.
  6. Generate draft.
  7. Extract reminders.
  8. Change category and record feedback.
  9. Edit draft.
  10. Complete reminder.

## 11. Phase 10: Tests

### Backend Tests

Create:

- `backend/tests/conftest.py`
- `backend/tests/test_emails.py`
- `backend/tests/test_ai_provider.py`
- `backend/tests/test_drafts.py`
- `backend/tests/test_reminders.py`
- `backend/tests/test_dashboard.py`

Coverage:

- Import mock emails.
- Avoid duplicate import.
- Search and filter emails.
- Classify and score email.
- Generate summary.
- Generate draft for each tone.
- Extract reminders.
- Update drafts.
- Complete and delete reminders.
- Record classification feedback.
- Return dashboard summary.

### Frontend Tests

Optional for MVP, but recommended after core UI stabilizes:

- `frontend/src/pages/EmailsPage.test.tsx`
- `frontend/src/pages/EmailDetailPage.test.tsx`
- `frontend/src/pages/RemindersPage.test.tsx`

Coverage:

- Filter interactions.
- Detail page actions.
- Draft editing.
- Reminder completion.

## 12. Phase 11: Documentation And Verification

### Files

Modify:

- `README.md`
- `docs/development-plan.md`
- `docs/execution-plan.md`

Implementation:

- Document local setup.
- Document environment variables.
- Document API examples.
- Document MVP limitations.

Verification commands:

```bash
docker compose up -d db
cd backend
pip install -e .
alembic upgrade head
pytest
uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Manual verification:

- Open frontend.
- Import mock emails from Settings.
- Confirm all core MVP actions work end to end.

## 13. Suggested Build Order

1. Backend skeleton.
2. Database models and migration.
3. Email import/list/detail APIs.
4. Mock AI provider and email action APIs.
5. Draft/reminder/dashboard/feedback APIs.
6. Frontend skeleton and routing.
7. Frontend API client.
8. Dashboard and email list.
9. Email detail actions.
10. Draft and reminder pages.
11. Settings import flow.
12. Tests and README updates.

## 14. Key Implementation Defaults

- Use single-user mode.
- Use PostgreSQL.
- Use mock JSON import as the only email source for MVP.
- Keep AI provider configurable but default to mock provider.
- Store generated summaries on the `emails` table.
- Store generated drafts separately in the `drafts` table.
- Soft-delete reminders by setting `status = deleted`.
- Record classification feedback automatically when a user changes category.

