export type ReminderType = 'deadline' | 'meeting' | 'payment' | 'reply_task' | 'other';
export type ReminderStatus = 'pending' | 'done' | 'deleted';

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

export interface ReminderListResponse {
  items: ReminderResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface ReminderPatchRequest {
  status?: ReminderStatus;
  title?: string;
  description?: string | null;
}
