# MailPilot

MailPilot is a production-oriented MVP of an intelligent email workspace. It combines mailbox synchronization, AI-assisted triage, summaries, reminders, reply drafting, and user-confirmed email sending in a web application.

The default AI provider is a local mock provider, so the project can run without an external model API. OpenAI-compatible and Anthropic providers can be configured per user from the Settings page.

## What It Does

- User registration, login, JWT authentication, and per-user data isolation
- Gmail OAuth and Microsoft Graph OAuth with encrypted access and refresh tokens
- Gmail and Outlook inbox synchronization with provider-message deduplication and read-state updates
- JSON upload/import for local mailbox data
- Automatic email classification into important, normal, promotion, billing, school/work, needs reply, and spam
- Importance scoring, multi-signal spam detection, and Chinese email summaries
- Reminder extraction for deadlines, meetings, payments, and reply tasks
- AI-generated reply drafts with formal, brief, polite-decline, and information-request tones
- Manual compose flow for new emails, draft editing, deletion, and user-confirmed sending
- Dashboard statistics, audit logs, search, filters, sorting, pagination, and bulk email/reminder actions
- Background jobs for imports, mailbox sync, and AI processing with persistent progress records

## Screens

- Dashboard: inbox workload, important messages, pending reminders, and empty state onboarding
- Emails: searchable and filterable inbox with sorting by received time or importance
- Email detail: message body, summary, AI actions, drafts, and extracted reminders
- Drafts: reply drafts, new-message compose, provider selection, send confirmation, and failure retry
- Reminders: due dates, completion, soft deletion, multi-select, bulk completion, and bulk deletion
- Settings: AI provider configuration, JSON import, Gmail, and Outlook connections

## Architecture

```text
React + TypeScript + Vite
        |
        | REST / JSON through /api proxy
        v
FastAPI + SQLAlchemy + Alembic
        |
        +-- PostgreSQL
        +-- AI providers: mock / OpenAI-compatible / Anthropic
        +-- Gmail API / Microsoft Graph
        +-- In-process background task runner
```

The backend owns authentication, authorization, validation, provider integrations, background job records, and encrypted secret handling. The frontend uses TanStack Query for server state and React Router for protected application routes.

## Requirements

- Python 3.9 or newer
- Node.js 18 or newer
- Docker and Docker Compose for the local PostgreSQL service

## Quick Start

### 1. Start PostgreSQL

From the repository root:

```bash
docker compose up -d db
```

### 2. Configure the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

For a local first run, the default `AI_PROVIDER=mock` is sufficient. Set stable secrets before using the application beyond local development:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Use the first value for `JWT_SECRET_KEY` and the second for `ENCRYPTION_KEY`. Keep `ENCRYPTION_KEY` unchanged while encrypted AI keys and OAuth tokens exist in the database.

### 3. Apply migrations and start the API

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000/api/`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

### 4. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`.

### 5. Create local data

Register through the UI, or seed a local demo account:

```bash
cd backend
source .venv/bin/activate
mailpilot seed
```

Default demo credentials:

```text
Email:    demo@mailpilot.dev
Password: demo123
```

Useful options:

```bash
mailpilot seed --email admin@example.com --password changeme
mailpilot seed --no-ai
mailpilot seed --no-drafts --no-reminders
mailpilot reset --yes --seed
```

`mailpilot reset` drops all tables and reapplies the schema. It is intended for local development only and protects non-local databases unless `--force` is supplied.

## Configuration

The complete template is [backend/.env.example](backend/.env.example). The most important settings are:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | Local PostgreSQL URL | SQLAlchemy database connection |
| `AI_PROVIDER` | `mock` | Server-side default provider: `mock`, `openai`, or `anthropic` |
| `OPENAI_API_KEY` | empty | OpenAI-compatible provider key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI-compatible model |
| `ANTHROPIC_API_KEY` | empty | Anthropic provider key |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | Anthropic endpoint |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | Anthropic model |
| `AI_REQUEST_TIMEOUT` | `30` | AI request timeout in seconds |
| `AI_MAX_RETRIES` | `1` | Maximum retries for retryable provider failures |
| `AI_RATE_LIMIT_PER_MINUTE` | `30` | Global provider request limit |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT signing secret |
| `ENCRYPTION_KEY` | empty | Fernet key for stored API keys and OAuth tokens |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `VITE_API_BASE_URL` | `/api` | Frontend API base URL |

AI API keys are configured per user in Settings and encrypted at rest. The environment provider settings are used as defaults when a user has not saved a provider configuration.

## Gmail and Outlook Setup

Real mailbox synchronization and sending require provider OAuth credentials.

### Local callback URLs through Vite

Register these exact URLs with the provider consoles:

```text
Google:    http://localhost:5173/api/gmail/oauth/callback
Microsoft: http://localhost:5173/api/outlook/oauth/callback
```

Set:

```dotenv
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
OUTLOOK_CLIENT_ID=...
OUTLOOK_CLIENT_SECRET=...
```

The default scopes include Gmail read/send access and Microsoft Graph `Mail.Read`/`Mail.Send` access. OAuth state is signed and protected with an HttpOnly nonce cookie. Tokens are encrypted before storage.

If the frontend calls the backend directly, register these alternatives instead:

```text
Google:    http://localhost:8000/api/gmail/oauth/callback
Microsoft: http://localhost:8000/api/outlook/oauth/callback
```

For production, configure exact public callback URLs using `GMAIL_REDIRECT_URI` and `OUTLOOK_REDIRECT_URI`, and follow [docs/production.md](docs/production.md) for secret management and key rotation.

## API Overview

All data endpoints require `Authorization: Bearer <token>` unless noted otherwise. The complete contract is available from `/docs`.

### System and authentication

```text
GET  /api/health
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### Emails and processing

```text
POST /api/emails/import                 Queue bundled mock import
POST /api/emails/import/upload           Queue JSON email import
GET  /api/emails                        List, filter, sort, and paginate
PATCH /api/emails/{id}                  Read/category/importance updates
POST /api/emails/bulk                   Bulk mark-read or soft-delete
GET  /api/emails/{id}                   Detail with drafts/reminders
POST /api/emails/{id}/classify          Classify one email
POST /api/emails/{id}/summarize         Summarize one email
POST /api/emails/process-ai             Queue unprocessed AI work
```

`GET /api/emails` supports `q`, `category`, `is_read`, `min_importance`, `max_importance`, `sort_by`, `sort_order`, `page`, and `page_size`. `sort_by` is `received_at` or `importance`; the default is `received_at` descending.

### Drafts and sending

```text
POST /api/emails/{id}/drafts             Generate a reply draft
POST /api/drafts                         Create a new composed email draft
GET  /api/drafts                         List drafts
GET  /api/drafts/{id}                    Draft detail
PATCH /api/drafts/{id}                   Edit content, recipient, subject, or status
DELETE /api/drafts/{id}                  Soft-delete a draft
POST /api/drafts/{id}/send               Send after confirmation
```

The send request may specify `{"provider":"gmail"}` or `{"provider":"outlook"}`. The frontend requires a connected mailbox and confirmation before sending. Sendable states are `draft`, `saved`, `ready_to_send`, and `send_failed`; successful sends become `sent`.

### Reminders and dashboard

```text
GET  /api/reminders
PATCH /api/reminders/{id}
DELETE /api/reminders/{id}
POST /api/reminders/bulk                Complete or delete selected reminders
POST /api/emails/{id}/reminders/extract  Extract reminders from one email
GET  /api/dashboard/summary
```

### Mailbox connections and jobs

```text
GET    /api/gmail/authorize
GET    /api/gmail/oauth/callback
GET    /api/gmail/status
POST   /api/gmail/refresh
DELETE /api/gmail/disconnect

GET    /api/outlook/authorize
GET    /api/outlook/oauth/callback
GET    /api/outlook/status
POST   /api/outlook/refresh
DELETE /api/outlook/disconnect

POST /api/sync/gmail
POST /api/sync/outlook
GET  /api/jobs/{id}
GET  /api/jobs/active?job_type=ai_process
```

Import, sync, and AI processing endpoints return a job ID. Poll the job endpoint for `queued`, `running`, `completed`, or `failed` state and progress data.

### Settings, feedback, and audit

```text
GET  /api/settings/ai
PUT  /api/settings/ai
GET  /api/feedback
GET  /api/audit
```

## Data and Security

- Passwords are stored as bcrypt hashes.
- JWTs are used for API authentication.
- Email, draft, reminder, feedback, settings, OAuth account, audit, and job queries are scoped to the authenticated user.
- AI API keys and Gmail/Outlook access and refresh tokens are Fernet-encrypted at rest.
- OAuth uses signed state values and an HttpOnly nonce cookie for CSRF protection.
- Classification changes, AI actions, imports, draft sends, and bulk actions are recorded in audit logs.
- Gmail and Outlook sync stores attachment metadata only; attachment contents are not indexed or summarized.

## Testing

Backend tests use isolated database fixtures and cover authentication, ownership isolation, encryption, OAuth state/token handling, AI providers, retry behavior, sync parsing, spam detection, background jobs, draft sending, reminders, and API validation.

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Frontend type checking and production build:

```bash
cd frontend
npm run build
```

Migration verification:

```bash
cd backend
alembic upgrade head
```

## Project Layout

```text
backend/
  app/
    ai/                 Providers, prompts, parsing, retry, spam rules
    api/                FastAPI routes and authentication dependencies
    db/                 SQLAlchemy models and database session
    schemas/            Pydantic request/response models
    services/           Business logic, OAuth, sync, jobs, and sending
  alembic/              Database migrations
  tests/                Backend test suite
frontend/
  src/api/              Typed API clients
  src/components/       Shared UI components
  src/pages/            Protected application pages
  src/types/            Shared TypeScript types
  src/styles/            Global responsive styles
docs/
  development-plan.md   Product and implementation plan
  execution-plan.md     Phase-by-phase execution plan
  production.md         Production secrets and deployment notes
```

## Current Boundaries and Roadmap

- Attachment content extraction for PDFs, images, and office files is not included; only metadata is stored.
- The background task runner is in-process. A distributed queue and worker service should be added before multi-instance production deployment.
- AI classification currently combines provider output and deterministic rules; a trained classifier and evaluation pipeline are future work.
- There is no team/shared mailbox or organization-level permission model yet.
- Real-time job updates currently use polling rather than WebSockets or server-sent events.

## Documentation

- [Production setup](docs/production.md)
- [Development plan](docs/development-plan.md)
- [Execution plan](docs/execution-plan.md)
- [中文 README](README_CN.md)
