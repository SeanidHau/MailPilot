import { api } from './client';
import type { ReminderResponse } from '../types/reminder';

export async function fetchReminders(params: Record<string, any> = {}) {
  const { data } = await api.get('/reminders', { params });
  return data;
}

export async function fetchReminder(id: number): Promise<ReminderResponse> {
  const { data } = await api.get(`/reminders/${id}`);
  return data;
}

export async function patchReminder(id: number, body: Record<string, any>): Promise<ReminderResponse> {
  const { data } = await api.patch(`/reminders/${id}`, body);
  return data;
}

export async function deleteReminder(id: number) {
  const { data } = await api.delete(`/reminders/${id}`);
  return data;
}
