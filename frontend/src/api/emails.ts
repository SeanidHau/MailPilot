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

export async function importEmails(): Promise<{ imported: number }> {
  const { data } = await api.post('/emails/import');
  return data;
}

export async function fetchEmails(params: Record<string, any>): Promise<EmailListResponse> {
  const { data } = await api.get('/emails', { params });
  return data;
}

export async function fetchEmail(id: number): Promise<EmailDetailResponse> {
  const { data } = await api.get(`/emails/${id}`);
  return data;
}

export async function patchEmail(id: number, body: Record<string, any>): Promise<EmailResponse> {
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
