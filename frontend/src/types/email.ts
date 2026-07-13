export type EmailCategory =
  | 'important' | 'normal' | 'promotion' | 'bill' | 'school_work' | 'needs_reply' | 'spam';

export interface EmailResponse {
  id: number;
  message_id: string;
  sender: string;
  recipients: string;
  subject: string;
  body: string;
  received_at: string;
  is_read: boolean;
  category: string;
  importance_score: number;
  summary: string | null;
  ai_processed: boolean;
  spam_confidence: number | null;
  spam_signals: string | null;
  imported_source: string;
  created_at: string;
  updated_at: string;
}

export interface EmailListResponse {
  items: EmailResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface AIError {
  message: string;
  type: 'auth_error' | 'rate_limit' | 'server_error' | 'timeout' | 'provider_error' | string;
  retryable: boolean;
}

export interface EmailDetailResponse extends EmailResponse {
  drafts: DraftResponse[];
  reminders: ReminderResponse[];
}

export interface ClassifyResponse {
  category: string;
  importance_score: number;
  error: AIError | null;
}

export interface SummarizeResponse {
  summary: string;
  error: AIError | null;
}

export interface GenerateDraftResponse {
  id: number;
  tone: string;
  content: string;
  error: AIError | null;
}

export interface ExtractRemindersResponse {
  reminders: ReminderItem[];
  error: AIError | null;
}

export interface ReminderItem {
  title: string;
  description: string | null;
  reminder_type: string;
  due_at: string | null;
}

// re-export from other type files
import { DraftResponse } from './draft';
import { ReminderResponse } from './reminder';
