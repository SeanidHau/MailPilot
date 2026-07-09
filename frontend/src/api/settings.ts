import { api } from './client';
import type { AIProviderConfig, GmailAuthorizeResponse, GmailStatus, OutlookAuthorizeResponse, OutlookStatus } from '../types/settings';

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

export async function fetchOutlookStatus(): Promise<OutlookStatus> {
  const { data } = await api.get('/outlook/status');
  return data;
}

export async function fetchOutlookAuthorizationUrl(): Promise<OutlookAuthorizeResponse> {
  const { data } = await api.get('/outlook/authorize');
  return data;
}

export async function refreshOutlookToken(): Promise<OutlookStatus> {
  const { data } = await api.post('/outlook/refresh');
  return data;
}

export async function disconnectOutlook(): Promise<void> {
  await api.delete('/outlook/disconnect');
}
