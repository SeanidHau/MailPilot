import { api } from './client';
import type { AIProviderConfig, GmailAuthorizeResponse, GmailStatus } from '../types/settings';

export async function fetchAISettings(): Promise<AIProviderConfig> {
  const { data } = await api.get('/settings/ai');
  return data;
}

export async function updateAISettings(config: AIProviderConfig): Promise<AIProviderConfig> {
  const { data } = await api.put('/settings/ai', config);
  return data;
}

export async function fetchGmailStatus(): Promise<GmailStatus> {
  const { data } = await api.get('/gmail/status');
  return data;
}

export async function fetchGmailAuthorizationUrl(): Promise<GmailAuthorizeResponse> {
  const { data } = await api.get('/gmail/authorize');
  return data;
}

export async function refreshGmailToken(): Promise<GmailStatus> {
  const { data } = await api.post('/gmail/refresh');
  return data;
}

export async function disconnectGmail(): Promise<void> {
  await api.delete('/gmail/disconnect');
}
