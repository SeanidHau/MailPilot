export interface FeedbackResponse {
  id: number;
  email_id: number;
  old_category: string;
  new_category: string;
  reason: string | null;
  created_at: string;
}
