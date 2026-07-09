export type DraftTone = 'formal' | 'brief' | 'polite_decline' | 'ask_info';
export type DraftStatus = 'draft' | 'saved' | 'ready_to_send' | 'sent' | 'send_failed';

export interface DraftResponse {
  id: number;
  email_id: number;
  tone: string;
  content: string;
  status: string;
  send_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface DraftListResponse {
  items: DraftResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface DraftPatchRequest {
  content?: string;
  status?: DraftStatus;
}
