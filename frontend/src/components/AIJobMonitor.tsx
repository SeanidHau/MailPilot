import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pause, Sparkles } from 'lucide-react'
import { fetchActiveJob, fetchJob, pauseJob } from '../api/jobs'

const STORAGE_KEY = 'mailpilot.aiJobId'
const JOB_EVENT = 'mailpilot:ai-job-started'

export function getRememberedAIJobId(): number | null {
  const raw = window.localStorage.getItem(STORAGE_KEY)
  const id = raw ? Number(raw) : NaN
  return Number.isInteger(id) && id > 0 ? id : null
}

export function rememberAIJob(jobId: number) {
  window.localStorage.setItem(STORAGE_KEY, String(jobId))
  window.dispatchEvent(new Event(JOB_EVENT))
}

export function forgetAIJob(jobId?: number) {
  if (!jobId || getRememberedAIJobId() === jobId) window.localStorage.removeItem(STORAGE_KEY)
}

export function AIJobMonitor() {
  const queryClient = useQueryClient()
  const [jobId, setJobId] = useState<number | null>(() => getRememberedAIJobId())

  useEffect(() => {
    const handleJobStarted = () => setJobId(getRememberedAIJobId())
    window.addEventListener(JOB_EVENT, handleJobStarted)
    return () => window.removeEventListener(JOB_EVENT, handleJobStarted)
  }, [])

  const activeJobQuery = useQuery({
    queryKey: ['active-ai-job'],
    queryFn: () => fetchActiveJob(),
    enabled: jobId === null,
    refetchInterval: jobId === null ? 3000 : false,
  })

  useEffect(() => {
    if (jobId === null && activeJobQuery.data) setJobId(activeJobQuery.data.id)
  }, [activeJobQuery.data, jobId])

  const jobQuery = useQuery({
    queryKey: ['global-ai-job', jobId],
    queryFn: () => fetchJob(jobId!),
    enabled: jobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed' ? false : 1000
    },
  })

  const pauseMutation = useMutation({
    mutationFn: (id: number) => pauseJob(id),
    onSuccess: (updatedJob) => {
      queryClient.setQueryData(['global-ai-job', updatedJob.id], updatedJob)
      queryClient.invalidateQueries({ queryKey: ['active-ai-job'] })
    },
  })

  const job = jobQuery.data
  useEffect(() => {
    if (!job) return
    if (job.status === 'queued' || job.status === 'running' || job.status === 'pause_requested') {
      queryClient.invalidateQueries({ queryKey: ['emails'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      return
    }
    forgetAIJob(job.id)
    setJobId(null)
    queryClient.invalidateQueries({ queryKey: ['emails'] })
    queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    queryClient.invalidateQueries({ queryKey: ['active-ai-job'] })
  }, [job, queryClient])

  if (!job || (job.status !== 'queued' && job.status !== 'running' && job.status !== 'pause_requested')) return null

  const result = job.result || {}
  const total = typeof result.total === 'number' ? result.total : 0
  const processed = typeof result.processed === 'number' ? result.processed : 0
  const percent = total > 0 ? Math.min(100, Math.round((processed / total) * 100)) : 0
  const isPausing = job.status === 'pause_requested'

  return (
    <div role="status" style={{ position: 'sticky', top: 0, zIndex: 10, display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 1rem', borderBottom: '1px solid #fde68a', background: '#fffbeb', color: '#92400e', fontSize: '0.8125rem' }}>
      <Sparkles size={15} />
      <span style={{ whiteSpace: 'nowrap' }}>{isPausing ? 'AI 正在暂停' : 'AI 正在后台处理邮件'}</span>
      {total > 0 && <span style={{ whiteSpace: 'nowrap' }}>{processed}/{total}</span>}
      {total > 0 && (
        <div style={{ flex: 1, maxWidth: 240, height: 5, overflow: 'hidden', borderRadius: 999, background: '#fde68a' }}>
          <div style={{ width: `${percent}%`, height: '100%', background: '#d97706', transition: 'width 240ms ease' }} />
        </div>
      )}
      {typeof result.current_subject === 'string' && result.current_subject && (
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#a16207' }}>
          当前：{result.current_subject}
        </span>
      )}
      {!isPausing && (
        <button
          className="btn-secondary btn-sm"
          onClick={() => pauseMutation.mutate(job.id)}
          disabled={pauseMutation.isPending}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap' }}
        >
          <Pause size={13} />
          暂停
        </button>
      )}
    </div>
  )
}
