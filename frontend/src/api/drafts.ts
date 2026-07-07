import { api } from './client';
import type { DraftResponse, DraftListResponse, DraftPatchRequest } from '../types/draft';

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

export async function patchDraft(id: number, body: DraftPatchRequest): Promise<DraftResponse> {
  const { data } = await api.patch(`/drafts/${id}`, body);
  return data;
}
