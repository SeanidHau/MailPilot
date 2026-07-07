# MailPilot

MailPilot is an intelligent email assistant web application with AI-assisted classification, summaries, reply drafts, and reminder extraction.

Project documents:

- [Development Plan](docs/development-plan.md)
- [Execution Plan](docs/execution-plan.md)

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
| `AI_PROVIDER` | `mock` | AI provider (currently only `mock` supported) |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated CORS origins |
| `VITE_API_BASE_URL` | `/api` | Frontend API base URL |

## API Endpoints

### Health
- `GET /api/health`

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

- No Gmail or Outlook integration (mock JSON import only)
- No OAuth or multi-user authentication
- No automatic email sending
- Rule-based AI provider (keywords + regex); no real LLM integration
- No advanced spam detection model

## Technology Stack

**Backend:** FastAPI, SQLAlchemy, Alembic, Pydantic, PostgreSQL

**Frontend:** React 18, TypeScript, Vite, TanStack Query, React Router

**AI:** Mock rule-based provider with extension points for real LLM APIs
