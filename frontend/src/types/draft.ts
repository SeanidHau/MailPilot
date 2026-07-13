export type DraftTone = 'formal' | 'brief' | 'polite_decline' | 'ask_info' | 'manual';
export type DraftStatus = 'draft' | 'saved' | 'ready_to_send' | 'sent' | 'send_failed' | 'deleted';

export interface DraftResponse {
  id: number;
  email_id: number | null;
  tone: string;
  content: string;
  recipient: string | null;
  subject: string | null;
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
  recipient?: string;
  subject?: string;
  status?: DraftStatus;
}

export interface DraftCreateRequest {
  recipient: string;
  subject: string;
  content: string;
}
