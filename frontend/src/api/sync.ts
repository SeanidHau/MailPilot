import { api } from './client';
import type { JobAcceptedResponse } from '../types/job';

export async function syncGmailInbox(): Promise<JobAcceptedResponse> {
  const { data } = await api.post('/sync/gmail');
  return data;
}

export async function syncOutlookInbox(): Promise<JobAcceptedResponse> {
  const { data } = await api.post('/sync/outlook');
  return data;
}
