import { api } from './client';
import type { FeedbackListResponse } from '../types/feedback';

export interface FeedbackQueryParams {
  page?: number;
  page_size?: number;
}

export async function fetchFeedback(params: FeedbackQueryParams = {}): Promise<FeedbackListResponse> {
  const { data } = await api.get('/feedback', { params });
  return data;
}
