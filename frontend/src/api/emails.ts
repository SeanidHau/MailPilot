import { api } from './client';
import type {
  EmailListResponse,
  EmailDetailResponse,
  EmailResponse,
  ClassifyResponse,
  SummarizeResponse,
  GenerateDraftResponse,
  ExtractRemindersResponse,
} from '../types/email';

export interface EmailQueryParams {
  q?: string;
  category?: string;
  is_read?: boolean;
  min_importance?: number;
  max_importance?: number;
  page?: number;
  page_size?: number;
}

export interface EmailPatchBody {
  is_read?: boolean;
  category?: string;
  importance_score?: number;
}

export async function importEmails(): Promise<{ imported: number; skipped: number; errors: string[] }> {
  const { data } = await api.post('/emails/import');
  return data;
}

export async function uploadEmails(emails: Record<string, any>[]): Promise<{ imported: number; skipped: number; errors: string[] }> {
  const { data } = await api.post('/emails/import/upload', { emails });
  return data;
}

export async function fetchEmails(params: EmailQueryParams): Promise<EmailListResponse> {
  const { data } = await api.get('/emails', { params });
  return data;
}

export async function fetchEmail(id: number): Promise<EmailDetailResponse> {
  const { data } = await api.get(`/emails/${id}`);
  return data;
}

export async function patchEmail(id: number, body: EmailPatchBody): Promise<EmailResponse> {
  const { data } = await api.patch(`/emails/${id}`, body);
  return data;
}

export async function classifyEmail(id: number): Promise<ClassifyResponse> {
  const { data } = await api.post(`/emails/${id}/classify`);
  return data;
}

export async function summarizeEmail(id: number): Promise<SummarizeResponse> {
  const { data } = await api.post(`/emails/${id}/summarize`);
  return data;
}

export async function generateDraft(id: number, tone: string): Promise<GenerateDraftResponse> {
  const { data } = await api.post(`/emails/${id}/drafts`, { tone });
  return data;
}

export async function extractReminders(id: number): Promise<ExtractRemindersResponse> {
  const { data } = await api.post(`/emails/${id}/reminders/extract`);
  return data;
}
