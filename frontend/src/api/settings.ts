import { api } from './client';
import type { AIProviderConfig } from '../types/settings';

export async function fetchAISettings(): Promise<AIProviderConfig> {
  const { data } = await api.get('/settings/ai');
  return data;
}

export async function updateAISettings(config: AIProviderConfig): Promise<AIProviderConfig> {
  const { data } = await api.put('/settings/ai', config);
  return data;
}
