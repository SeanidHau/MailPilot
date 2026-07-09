# MailPilot

MailPilot is an intelligent email assistant web application with AI-assisted classification, summaries, reply drafts, and reminder extraction.

Project documents:

- [Development Plan](docs/development-plan.md)
- [Execution Plan](docs/execution-plan.md)
- [中文文档](README_CN.md) | [Chinese](README_CN.md)

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker (for PostgreSQL)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Start PostgreSQL
docker compose up -d db

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000/api/`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app is available at `http://localhost:5173`. The dev server proxies `/api` requests to the backend.

### Run Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://mailpilot:mailpilot@localhost:5432/mailpilot` | Database connection string |
| `AI_PROVIDER` | `mock` | Default AI provider (`mock`, `openai`, or `anthropic`) |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated CORS origins |
| `OPENAI_API_KEY` | empty | Default OpenAI-compatible API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Default OpenAI-compatible base URL |
| `OPENAI_MODEL` | `gpt-4o` | Default OpenAI-compatible model |
| `ANTHROPIC_API_KEY` | empty | Default Anthropic API key |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | Default Anthropic base URL |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | Default Anthropic model |
| `AI_REQUEST_TIMEOUT` | `60.0` | Per-request timeout for OpenAI-compatible and Anthropic calls, in seconds |
| `AI_MAX_RETRIES` | `2` | Maximum retry count for retryable AI provider failures |
| `AI_RATE_LIMIT_PER_MINUTE` | `30` | Global AI provider request rate limit |
| `JWT_SECRET_KEY` | generated if unset | JWT signing key. Set a stable secret outside local development |
| `ENCRYPTION_KEY` | generated if unset | Fernet key for encrypted stored AI API keys. Must be stable to decrypt saved values after restart |
| `GMAIL_CLIENT_ID` | empty | Google OAuth client ID for Gmail integration |
| `GMAIL_CLIENT_SECRET` | empty | Google OAuth client secret for Gmail integration |
| `GMAIL_REDIRECT_URI` | `http://localhost:8000/api/gmail/oauth/callback` | Google OAuth callback URL. Must match the Google Cloud OAuth client |
| `GMAIL_SCOPES` | `openid email https://www.googleapis.com/auth/gmail.readonly` | Space-separated Google OAuth scopes |
| `GMAIL_OAUTH_SUCCESS_URL` | `http://localhost:5173/settings?gmail=connected` | Frontend URL used after successful Gmail OAuth |
| `GMAIL_OAUTH_FAILURE_URL` | `http://localhost:5173/settings?gmail=error` | Frontend URL used after failed Gmail OAuth |
| `OUTLOOK_CLIENT_ID` | empty | Microsoft OAuth client ID for Outlook / Microsoft Graph integration |
| `OUTLOOK_CLIENT_SECRET` | empty | Microsoft OAuth client secret for Outlook / Microsoft Graph integration |
| `OUTLOOK_REDIRECT_URI` | `http://localhost:8000/api/outlook/oauth/callback` | Microsoft OAuth callback URL. Must match the Azure app registration |
| `OUTLOOK_SCOPES` | `offline_access User.Read Mail.Read` | Space-separated Microsoft Graph OAuth scopes |
| `OUTLOOK_OAUTH_SUCCESS_URL` | `http://localhost:5173/settings?outlook=connected` | Frontend URL used after successful Outlook OAuth |
| `OUTLOOK_OAUTH_FAILURE_URL` | `http://localhost:5173/settings?outlook=error` | Frontend URL used after failed Outlook OAuth |
| `VITE_API_BASE_URL` | `/api` | Frontend API base URL |

## API Endpoints

### Health
- `GET /api/health`

### Auth
- `POST /api/auth/register` — Register a user and return a JWT
- `POST /api/auth/login` — Login and return a JWT
- `GET /api/auth/me` — Current user profile, requires Bearer token

### Emails
- `POST /api/emails/import` — Import mock email data
- `GET /api/emails` — List emails (supports `q`, `category`, `is_read`, `min_importance`, `max_importance`, `page`, `page_size`)
- `GET /api/emails/{id}` — Email detail with drafts and reminders
- `PATCH /api/emails/{id}` — Update read status, category, or importance score
- `POST /api/emails/{id}/classify` — AI classification
- `POST /api/emails/{id}/summarize` — AI summary
- `POST /api/emails/{id}/drafts` — Generate reply draft (body: `{"tone": "formal|brief|polite_decline|ask_info"}`)
- `POST /api/emails/{id}/reminders/extract` — Extract reminders from email

### Drafts
- `GET /api/drafts` — List drafts
- `GET /api/drafts/{id}` — Draft detail
- `PATCH /api/drafts/{id}` — Update draft content or status

### Reminders
- `GET /api/reminders` — List reminders (supports `status` filter)
- `PATCH /api/reminders/{id}` — Update reminder (complete, etc.)
- `DELETE /api/reminders/{id}` — Soft-delete reminder

### Dashboard
- `GET /api/dashboard/summary` — Dashboard statistics

### Feedback
- `GET /api/feedback` — Classification change history

### Settings
- `GET /api/settings/ai` — Read AI provider config. Uses the current user's config when authenticated, otherwise returns defaults
- `PUT /api/settings/ai` — Save encrypted per-user AI provider config, requires Bearer token

### Gmail
- `GET /api/gmail/authorize` - Build a Google OAuth authorization URL, requires Bearer token
- `GET /api/gmail/oauth/callback` - Google OAuth callback; exchanges code, stores encrypted tokens, then redirects to the frontend
- `GET /api/gmail/status` - Read the current user's Gmail connection state, requires Bearer token
- `POST /api/gmail/refresh` - Force refresh the current user's Gmail access token, requires Bearer token
- `DELETE /api/gmail/disconnect` - Remove the current user's stored Gmail tokens, requires Bearer token

### Outlook / Microsoft Graph
- `GET /api/outlook/authorize` - Build a Microsoft OAuth authorization URL, requires Bearer token
- `GET /api/outlook/oauth/callback` - Microsoft OAuth callback; exchanges code, stores encrypted tokens, then redirects to the frontend
- `GET /api/outlook/status` - Read the current user's Outlook connection state, requires Bearer token
- `POST /api/outlook/refresh` - Force refresh the current user's Outlook access token, requires Bearer token
- `DELETE /api/outlook/disconnect` - Remove the current user's stored Outlook tokens, requires Bearer token

### Mailbox Sync
- `POST /api/sync/gmail` - Sync Gmail inbox emails with dedup by provider message ID, requires Bearer token
- `POST /api/sync/outlook` - Sync Outlook inbox emails with dedup by provider message ID, requires Bearer token

## Email Categories

| Category | Description |
|----------|-------------|
| `important` | Urgent, critical, deadline-related |
| `normal` | General correspondence |
| `promotion` | Marketing, discounts, campaigns |
| `bill` | Invoices, payments, subscriptions |
| `school_work` | Academic or work-related tasks |
| `needs_reply` | Requires response or confirmation |
| `spam` | Suspicious or unwanted |

## Draft Tones

| Tone | Description |
|------|-------------|
| `formal` | Complete and professional |
| `brief` | Short and direct |
| `polite_decline` | Respectful refusal |
| `ask_info` | Requests clarification or details |

## MVP Limitations

- No advanced spam detection model
- Gmail/Outlook OAuth and inbox sync are supported with per-provider message ID dedup and read/unread state sync
- No automatic email sending
- User authentication exists with per-user data isolation; unauthenticated access to data APIs returns 401
- AI providers are configurable with timeout, retry, and rate-limit handling, but production-grade observability and cost controls are not complete

## Technology Stack

**Backend:** FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL

**Frontend:** React 18, TypeScript, Vite, TanStack Query, React Router

**AI:** Mock rule-based provider, OpenAI-compatible provider, and Anthropic provider

## TODO

### Account And Data Privacy

- [x] Add `user_id` ownership to `emails`, `drafts`, `reminders`, and `classification_feedback`, then filter all list/detail/update/delete APIs by the current user.
- [x] Decide how anonymous/demo mock email data should work after user-level data ownership is added.
- [x] Add frontend route guards for pages/actions that should require login, especially saving AI settings and future mailbox data.
- [x] Add auth-focused tests for register, login, `/auth/me`, duplicate registration, invalid password, expired/invalid token, and logout behavior.
- [x] Add encryption-focused tests that verify AI API keys are encrypted at rest and decrypt correctly with a stable `ENCRYPTION_KEY`.

### Mailbox Integration

- [x] Implement Gmail OAuth authorization and token refresh.
- [x] Implement Outlook/Microsoft Graph OAuth authorization and token refresh.
- [x] Add mailbox sync jobs for inbox fetch, incremental updates, read/unread state, and deduplication by provider message ID.
- [x] Add manual JSON upload/import UI instead of only importing the bundled backend mock file.
- [ ] Add attachment metadata support and decide whether attachment content should be indexed or summarized.

### Email Actions

- [ ] Implement optional real email sending from saved drafts, with an explicit confirmation step.
- [ ] Add draft-to-send workflow state such as `ready_to_send`, `sent`, and `send_failed`.
- [ ] Add audit logs for user-triggered email actions and AI-generated content edits.

### AI Reliability

- [x] Add provider-level timeout, retry, and rate-limit handling for OpenAI-compatible and Anthropic calls.
- [x] Add structured error responses when real AI providers fail, instead of returning only generic fallback text.
- [x] Add per-user AI provider selection to background/service calls consistently once all data is user-scoped.
- [ ] Add prompt/version metadata to generated summaries, drafts, classifications, and extracted reminders.
- [ ] Add evaluation tests for classification accuracy, reminder extraction, and reply draft quality beyond the current mock-provider unit tests.

### Product And UX

- [ ] Add onboarding that guides first-time users through registration, mock import, and AI provider configuration.
- [ ] Add clearer settings-state messaging when the user is not logged in and attempts to save authenticated settings.
- [ ] Add better empty states for dashboards before any email import.
- [ ] Add responsive/mobile QA for the full authenticated flow.

### Operations

- [ ] Document production setup for stable `JWT_SECRET_KEY` and `ENCRYPTION_KEY`; rotating `ENCRYPTION_KEY` requires a re-encryption plan.
- [ ] Add CI jobs for backend tests, frontend typecheck/build, and Alembic migration verification on a fresh PostgreSQL database.
- [ ] Add seed/reset commands for local demo data.
- [ ] Add logging/metrics for auth failures, AI provider failures, import counts, and reminder extraction counts.
