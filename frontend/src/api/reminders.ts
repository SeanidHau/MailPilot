import { api } from './client';
import type { ReminderResponse, ReminderListResponse, ReminderPatchRequest } from '../types/reminder';

export interface ReminderQueryParams {
  status?: string;
  page?: number;
  page_size?: number;
}

export async function fetchReminders(params: ReminderQueryParams = {}): Promise<ReminderListResponse> {
  const { data } = await api.get('/reminders', { params });
  return data;
}

export async function fetchReminder(id: number): Promise<ReminderResponse> {
  const { data } = await api.get(`/reminders/${id}`);
  return data;
}

export async function patchReminder(id: number, body: ReminderPatchRequest): Promise<ReminderResponse> {
  const { data } = await api.patch(`/reminders/${id}`, body);
  return data;
}

export async function deleteReminder(id: number): Promise<{ status: string }> {
  const { data } = await api.delete(`/reminders/${id}`);
  return data;
}
