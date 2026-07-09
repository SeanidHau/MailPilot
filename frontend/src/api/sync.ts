import { api } from './client';

export interface SyncResult {
  new: number;
  skipped: number;
  errors: string[];
}

export async function syncGmailInbox(): Promise<SyncResult> {
  const { data } = await api.post('/sync/gmail');
  return data;
}

export async function syncOutlookInbox(): Promise<SyncResult> {
  const { data } = await api.post('/sync/outlook');
  return data;
}
