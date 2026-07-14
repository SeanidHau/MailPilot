import { api } from './client';
import type { BackgroundJob } from '../types/job';

export async function fetchJob(id: number): Promise<BackgroundJob> {
  const { data } = await api.get(`/jobs/${id}`);
  return data;
}

export async function fetchActiveJob(jobType = 'ai_process'): Promise<BackgroundJob | null> {
  const { data } = await api.get('/jobs/active', { params: { job_type: jobType } });
  return data;
}

export async function pauseJob(id: number): Promise<BackgroundJob> {
  const { data } = await api.post(`/jobs/${id}/pause`);
  return data;
}
