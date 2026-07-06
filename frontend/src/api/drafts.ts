import { api } from './client';
import type { DraftResponse } from '../types/draft';

export async function fetchDrafts(params: Record<string, any> = {}) {
  const { data } = await api.get('/drafts', { params });
  return data;
}

export async function fetchDraft(id: number): Promise<DraftResponse> {
  const { data } = await api.get(`/drafts/${id}`);
  return data;
}

export async function patchDraft(id: number, body: Record<string, any>): Promise<DraftResponse> {
  const { data } = await api.patch(`/drafts/${id}`, body);
  return data;
}
