# MailPilot Development Plan

## 1. Project Overview

MailPilot is a productivity-focused web application for managing email with AI-assisted classification, summaries, reply drafts, and reminder extraction.

The first version should prioritize a working MVP instead of a complex full email platform. Email data will be imported from local mock JSON data, and AI behavior will be implemented with rule-based/mock providers. The system should keep clear extension points for future Gmail/Outlook authorization and real large model APIs.

## 2. Goals

- Import or read email data from local mock JSON.
- Classify emails by subject, sender, and body content.
- Support user corrections to classification results.
- Generate editable reply drafts in different tones.
- Extract deadlines, meetings, payment times, and reply tasks into reminders.
- Summarize long emails.
- Score email importance from 1 to 5.
- Provide dashboard, email list, email detail, draft management, reminder management, and settings pages.
- Provide RESTful backend APIs.
- Keep the codebase structured for future real mailbox and AI integrations.

## 3. Non-Goals For MVP

- No real Gmail or Outlook integration.
- No OAuth login or multi-user authentication.
- No automatic email sending.
- No production-grade AI model integration.
- No advanced spam detection model or training pipeline.

## 4. Recommended Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic and pydantic-settings
- PostgreSQL by default
- Pytest for tests

### Frontend

- TypeScript
- React
- Vite
- React Router
- TanStack Query
- Axios or Fetch wrapper
- lucide-react for icons

### Database

- PostgreSQL for the default implementation.
- MySQL can be supported later with minor driver and field compatibility adjustments.

### AI Layer

- MVP: local mock/rule-based provider.
- Future: provider implementation for real model APIs.

## 5. System Architecture

```text
React + Vite Web App
        |
        | REST API
        v
FastAPI Backend
        |
        +-- Email Service
        +-- Draft Service
        +-- Reminder Service
        +-- Feedback Service
        +-- Dashboard Service
        +-- AI Service
              |
              +-- MockAIProvider
              +-- FutureLLMProvider
        |
        v
PostgreSQL
```

The frontend should only call backend APIs. Classification, summary generation, draft generation, and reminder extraction should be coordinated by backend services. The frontend should not contain AI business rules.

## 6. Frontend Page Design

### Dashboard

Route: `/`

Displays:

- Today's pending emails.
- Important email count.
- Pending reminder count.
- Recent important emails.
- Upcoming reminders.

### Email List

Route: `/emails`

Displays:

- Search input.
- Category filter.
- Read/unread filter.
- Importance score filter.
- Email table with sender, subject, category, importance score, received time, and read status.

Actions:

- Open email detail.
- Mark read/unread if included in MVP.

### Email Detail

Route: `/emails/:id`

Displays:

- Sender, recipients, subject, received time.
- Email body.
- Current classification.
- Importance score.
- Summary.
- Related drafts.
- Related reminders.

Actions:

- Change category manually.
- Re-run classification.
- Generate or refresh summary.
- Generate reply draft by tone.
- Extract reminders.

### Draft Management

Route: `/drafts`

Displays:

- List of generated drafts.
- Linked source email.
- Tone.
- Editable content.

Actions:

- Edit draft.
- Save draft.

### Reminder Management

Route: `/reminders`

Displays:

- Pending reminders.
- Completed reminders.
- Reminder type, due time, source email, description.

Actions:

- Complete reminder.
- Delete reminder.

### Settings

Route: `/settings`

Displays:

- Mock data import action.
- AI mode placeholder.
- Classification rule description.
- Future mailbox authorization placeholder.

## 7. Backend API Design

### Health

- `GET /api/health`

### Emails

- `POST /api/emails/import`
- `GET /api/emails`
- `GET /api/emails/{email_id}`
- `PATCH /api/emails/{email_id}`
- `POST /api/emails/{email_id}/classify`
- `POST /api/emails/{email_id}/summarize`
- `POST /api/emails/{email_id}/drafts`
- `POST /api/emails/{email_id}/reminders/extract`

Supported query parameters for `GET /api/emails`:

- `q`
- `category`
- `is_read`
- `min_importance`
- `max_importance`
- `page`
- `page_size`

### Drafts

- `GET /api/drafts`
- `GET /api/drafts/{draft_id}`
- `PATCH /api/drafts/{draft_id}`

### Reminders

- `GET /api/reminders`
- `PATCH /api/reminders/{reminder_id}`
- `DELETE /api/reminders/{reminder_id}`

### Dashboard

- `GET /api/dashboard/summary`

### Feedback

- `GET /api/feedback`
- `POST /api/feedback/classification`

## 8. Database Design

### emails

Stores imported email content and AI/user-derived metadata.

Fields:

- `id`
- `message_id`
- `sender`
- `recipients`
- `subject`
- `body`
- `received_at`
- `is_read`
- `category`
- `importance_score`
- `summary`
- `imported_source`
- `created_at`
- `updated_at`

### drafts

Stores generated and user-edited reply drafts.

Fields:

- `id`
- `email_id`
- `tone`
- `content`
- `status`
- `created_at`
- `updated_at`

### reminders

Stores extracted tasks, meetings, deadlines, payment reminders, and reply reminders.

Fields:

- `id`
- `email_id`
- `title`
- `description`
- `due_at`
- `reminder_type`
- `status`
- `created_at`
- `updated_at`

### classification_feedback

Stores user changes to classification results.

Fields:

- `id`
- `email_id`
- `old_category`
- `new_category`
- `reason`
- `created_at`

### settings

Stores simple system settings and future provider configuration metadata.

Fields:

- `id`
- `key`
- `value`
- `updated_at`

## 9. Enums And Domain Values

### Email Category

- `important`
- `normal`
- `promotion`
- `bill`
- `school_work`
- `needs_reply`
- `spam`

### Draft Tone

- `formal`
- `brief`
- `polite_decline`
- `ask_info`

### Reminder Type

- `deadline`
- `meeting`
- `payment`
- `reply_task`
- `other`

### Reminder Status

- `pending`
- `done`
- `deleted`

### Draft Status

- `draft`
- `saved`

## 10. AI And Rule Module Design

The backend AI service should depend on an abstract provider interface:

- `classify_email(email)`
- `summarize_email(email)`
- `generate_reply(email, tone)`
- `extract_reminders(email)`

### MVP Classification Rules

- Promotion: detects words such as discount, sale, offer, unsubscribe, campaign.
- Bill: detects invoice, receipt, payment, due amount, subscription, billing.
- School/work: detects assignment, class, meeting, project, report, professor, manager.
- Needs reply: detects reply, respond, confirm, approve, feedback, question.
- Important: detects urgent, deadline, final notice, action required, critical.
- Spam: detects suspicious phrases, fake prize, lottery, unknown aggressive marketing.
- Normal: fallback category.

### Importance Scoring

- Start from 1.
- Add points for urgent language, deadlines, meetings, payment notices, direct requests, or known important senders.
- Clamp result to the 1-5 range.

### Summary

- MVP should generate a short summary from the first meaningful sentences and detected keywords.
- Long emails should be summarized into 2-3 concise bullet-style statements.

### Draft Generation

Drafts should use templates by tone:

- Formal: complete and professional.
- Brief: short and direct.
- Polite decline: respectful refusal.
- Ask information: asks for clarification or missing details.

### Reminder Extraction

Reminder extraction should use keyword and regex matching for:

- Dates.
- Times.
- Deadlines.
- Meetings.
- Payment due notices.
- Reply or confirmation requests.

If exact due time cannot be confidently parsed, create a reminder with a clear description and nullable `due_at`.

## 11. Recommended Directory Structure

```text
MailPilot/
  backend/
    app/
      main.py
      core/
        config.py
      db/
        base.py
        session.py
        models.py
      schemas/
        ai.py
        dashboard.py
        draft.py
        email.py
        feedback.py
        reminder.py
      api/
        router.py
        routes/
          dashboard.py
          drafts.py
          emails.py
          feedback.py
          reminders.py
      services/
        ai_service.py
        dashboard_service.py
        draft_service.py
        email_service.py
        feedback_service.py
        reminder_service.py
      ai/
        providers/
          base.py
          mock.py
      mock_data/
        emails.json
    alembic/
    tests/
    pyproject.toml
    .env.example
  frontend/
    src/
      app/
        queryClient.ts
        router.tsx
      api/
        client.ts
        dashboard.ts
        drafts.ts
        emails.ts
        feedback.ts
        reminders.ts
      components/
      pages/
      styles/
      types/
    package.json
    vite.config.ts
    tsconfig.json
  docs/
    development-plan.md
    execution-plan.md
  docker-compose.yml
  README.md
```

