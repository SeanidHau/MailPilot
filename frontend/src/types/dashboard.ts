export interface DashboardSummary {
  total_emails: number;
  pending_emails: number;
  important_emails: number;
  pending_reminders: number;
  recent_important_emails: EmailSummary[];
  upcoming_reminders: ReminderSummary[];
}

export interface EmailSummary {
  id: number;
  sender: string;
  subject: string;
  category: string;
  importance_score: number;
  received_at: string;
}

export interface ReminderSummary {
  id: number;
  title: string;
  reminder_type: string;
  due_at: string | null;
  email_subject: string;
}
