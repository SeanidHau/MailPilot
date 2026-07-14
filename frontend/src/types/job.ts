export type JobStatus = 'queued' | 'running' | 'pause_requested' | 'paused' | 'completed' | 'failed';

export interface JobAcceptedResponse {
  job_id: number;
  status: JobStatus;
}

export interface BackgroundJob {
  id: number;
  job_type: string;
  status: JobStatus;
  result: Record<string, any> | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
}
