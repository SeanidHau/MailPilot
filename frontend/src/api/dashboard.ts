import { api } from './client';
import type { DashboardSummary } from '../types/dashboard';

export async function fetchDashboard(): Promise<DashboardSummary> {
  const { data } = await api.get('/dashboard/summary');
  return data;
}
