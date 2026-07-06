import { api } from './client';
import type { FeedbackResponse } from '../types/feedback';

export async function fetchFeedback(params: Record<string, any> = {}) {
  const { data } = await api.get('/feedback', { params });
  return data;
}
