export interface ReminderResponse {
  id: number;
  email_id: number;
  title: string;
  description: string | null;
  due_at: string | null;
  reminder_type: string;
  status: string;
  created_at: string;
  updated_at: string;
}
