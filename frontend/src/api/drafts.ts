import { api } from './client';
import type { DraftResponse, DraftListResponse, DraftPatchRequest, DraftCreateRequest } from '../types/draft';

export type MailboxProvider = 'gmail' | 'outlook';

export interface DraftQueryParams {
  page?: number;
  page_size?: number;
}

export async function fetchDrafts(params: DraftQueryParams = {}): Promise<DraftListResponse> {
  const { data } = await api.get('/drafts', { params });
  return data;
}

export async function fetchDraft(id: number): Promise<DraftResponse> {
  const { data } = await api.get(`/drafts/${id}`);
  return data;
}

export async function createDraft(body: DraftCreateRequest): Promise<DraftResponse> {
  const { data } = await api.post('/drafts', body);
  return data;
}

export async function patchDraft(id: number, body: DraftPatchRequest): Promise<DraftResponse> {
  const { data } = await api.patch(`/drafts/${id}`, body);
  return data;
}

export async function sendDraft(id: number, provider?: MailboxProvider): Promise<DraftResponse> {
  const { data } = await api.post(`/drafts/${id}/send`, provider ? { provider } : {});
  return data;
}

export async function deleteDraft(id: number): Promise<{ status: 'deleted' }> {
  const { data } = await api.delete(`/drafts/${id}`);
  return data;
}
