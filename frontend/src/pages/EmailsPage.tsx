import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, MailOpen, Sparkles, Trash2 } from 'lucide-react'
import { bulkUpdateEmails, fetchEmails, processUnprocessedEmails, type EmailQueryParams, type BulkEmailAction } from '../api/emails'
import { fetchJob } from '../api/jobs'
import { EmailTable } from '../components/EmailTable'
import { EmailFilters } from '../components/EmailFilters'
import { forgetAIJob, getRememberedAIJobId, rememberAIJob } from '../components/AIJobMonitor'

export function EmailsPage() {
  const [filters, setFilters] = useState({
    q: '', category: '', is_read: '', min_importance: '',
    sort_by: 'received_at', sort_order: 'desc',
  })
  const [page, setPage] = useState(1)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [bulkMessage, setBulkMessage] = useState('')
  const [aiJobId, setAiJobId] = useState<number | null>(() => getRememberedAIJobId())
  const [aiMessage, setAiMessage] = useState('')
  const queryClient = useQueryClient()

  const handleFilterChange = (nextFilters: typeof filters) => {
    setFilters(nextFilters)
    setPage(1)
    setSelectedIds(new Set())
  }

  const handleSort = (sortBy: 'received_at' | 'importance') => {
    setFilters((current) => ({
      ...current,
      sort_by: current.sort_by === sortBy && current.sort_order === 'desc' ? sortBy : sortBy,
      sort_order: current.sort_by === sortBy && current.sort_order === 'desc' ? 'asc' : 'desc',
    }))
    setPage(1)
    setSelectedIds(new Set())
  }

  const params: EmailQueryParams = { page, page_size: 20 }
  if (filters.q) params.q = filters.q
  if (filters.category) params.category = filters.category
  if (filters.is_read) params.is_read = filters.is_read === 'true'
  if (filters.min_importance) params.min_importance = Number(filters.min_importance)
  if (filters.sort_by === 'received_at' || filters.sort_by === 'importance') params.sort_by = filters.sort_by
  if (filters.sort_order === 'asc' || filters.sort_order === 'desc') params.sort_order = filters.sort_order

  const { data, isLoading } = useQuery({
    queryKey: ['emails', params],
    queryFn: () => fetchEmails(params),
  })
  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1

  const aiJobQuery = useQuery({
    queryKey: ['job', aiJobId],
    queryFn: () => fetchJob(aiJobId!),
    enabled: aiJobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed' ? false : 1000
    },
  })
  const aiProgress = aiJobQuery.data?.result || {}
  const processingEmailId = typeof aiProgress.current_email_id === 'number' ? aiProgress.current_email_id : null
  const aiTotal = typeof aiProgress.total === 'number' ? aiProgress.total : 0
  const aiProcessed = typeof aiProgress.processed === 'number' ? aiProgress.processed : 0
  const aiPercent = aiTotal > 0 ? Math.min(100, Math.round((aiProcessed / aiTotal) * 100)) : 0

  useEffect(() => {
    const job = aiJobQuery.data
    if (!job) return
    if (job.status === 'queued' || job.status === 'running') {
      const progress = job.result || {}
      queryClient.invalidateQueries({ queryKey: ['emails'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      if (typeof progress.total === 'number') {
        setAiMessage(`AI 正在处理邮件：${progress.processed ?? 0}/${progress.total}${progress.failed ? `，失败 ${progress.failed} 封` : ''}`)
      }
      return
    }
    if (job.status === 'completed') {
      const processed = job.result?.processed ?? 0
      const errorCount = job.result?.errors?.length ?? 0
      setAiMessage(`AI 处理完成：处理 ${processed} 封邮件${errorCount ? `，${errorCount} 个错误` : ''}。`)
      queryClient.invalidateQueries({ queryKey: ['emails'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    } else {
      setAiMessage(`AI 处理失败：${job.error || '后台任务执行失败'}`)
    }
    forgetAIJob(job.id)
    setAiJobId(null)
  }, [aiJobQuery.data, queryClient])

  const aiMut = useMutation({
    mutationFn: processUnprocessedEmails,
    onSuccess: (result) => {
      rememberAIJob(result.job_id)
      setAiJobId(result.job_id)
      setAiMessage('已提交 AI 处理任务，正在处理未完成的邮件...')
    },
    onError: (error: Error) => setAiMessage(`AI 处理失败：${error.message}`),
  })

  useEffect(() => {
    const visibleIds = new Set(data?.items.map((email) => email.id) || [])
    setSelectedIds((current) => new Set([...current].filter((id) => visibleIds.has(id))))
  }, [data?.items])

  const bulkMut = useMutation({
    mutationFn: ({ action, ids }: { action: BulkEmailAction; ids: number[] }) => bulkUpdateEmails(ids, action),
    onSuccess: (result) => {
      setBulkMessage(`${result.updated} 封邮件已${result.action === 'delete' ? '删除' : '标记为已读'}。`)
      setSelectedIds(new Set())
      queryClient.invalidateQueries({ queryKey: ['emails'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (error: Error) => setBulkMessage(`操作失败：${error.message}`),
  })

  const toggleEmail = (id: number) => {
    setSelectedIds((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleAll = (checked: boolean) => {
    setSelectedIds(checked ? new Set(data?.items.map((email) => email.id) || []) : new Set())
  }

  const handleBulkAction = (action: BulkEmailAction) => {
    if (selectedIds.size === 0) return
    if (action === 'delete' && !window.confirm(`确定删除选中的 ${selectedIds.size} 封邮件吗？`)) return
    setBulkMessage('')
    bulkMut.mutate({ action, ids: [...selectedIds] })
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
        <h1>邮件</h1>
        <button
          className="btn-secondary"
          onClick={() => aiMut.mutate()}
          disabled={aiMut.isPending || aiJobId !== null}
          title="只处理尚未完成 AI 处理的邮件"
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Sparkles size={14} />
          {aiMut.isPending || aiJobId !== null ? 'AI 处理中...' : '处理未处理邮件'}
        </button>
      </div>
      {aiMessage && <div style={{ marginBottom: '1rem', fontSize: '0.875rem' }}>{aiMessage}</div>}
      {aiJobId !== null && aiTotal > 0 && (
        <div style={{ marginBottom: '1rem' }} aria-label={`AI 处理进度 ${aiPercent}%`}>
          <div style={{ height: 6, overflow: 'hidden', borderRadius: 999, background: '#e2e8f0' }}>
            <div style={{ width: `${aiPercent}%`, height: '100%', background: 'var(--color-primary)', transition: 'width 240ms ease' }} />
          </div>
          <div style={{ marginTop: 4, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            {aiProcessed}/{aiTotal} 封邮件
          </div>
        </div>
      )}
      <EmailFilters filters={filters} onChange={handleFilterChange} />

      {selectedIds.size > 0 && (
        <div className="bulk-actions" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>已选 {selectedIds.size} 封</span>
          <button className="btn-secondary btn-sm" onClick={() => handleBulkAction('mark_read')} disabled={bulkMut.isPending}>
            <MailOpen size={14} style={{ marginRight: 4 }} /> 标记已读
          </button>
          <button className="btn-danger btn-sm" onClick={() => handleBulkAction('delete')} disabled={bulkMut.isPending}>
            <Trash2 size={14} style={{ marginRight: 4 }} /> 删除
          </button>
        </div>
      )}
      {bulkMessage && <div style={{ marginBottom: '1rem', fontSize: '0.875rem' }}>{bulkMessage}</div>}

      {isLoading ? (
        <div className="empty-state">加载中...</div>
      ) : data ? (
        <>
          <EmailTable
            emails={data.items}
            selectedIds={selectedIds}
            processingEmailId={processingEmailId}
            sortBy={filters.sort_by as 'received_at' | 'importance'}
            sortOrder={filters.sort_order as 'asc' | 'desc'}
            onToggle={toggleEmail}
            onToggleAll={toggleAll}
            onSort={handleSort}
          />
          {data.total > data.page_size && (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', marginTop: '1rem', flexWrap: 'wrap' }}>
              <button className="btn-secondary btn-sm" aria-label="第一页" title="第一页" disabled={page <= 1} onClick={() => setPage(1)}>
                <ChevronsLeft size={14} />
              </button>
              <button className="btn-secondary btn-sm" aria-label="上一页" title="上一页" disabled={page <= 1} onClick={() => setPage((current) => current - 1)}>
                <ChevronLeft size={14} />
              </button>
              <select
                aria-label="选择页码"
                value={page}
                onChange={(event) => setPage(Number(event.target.value))}
                style={{ minHeight: 30, padding: '0.25rem 0.5rem' }}
              >
                {Array.from({ length: totalPages }, (_, index) => index + 1).map((pageNumber) => (
                  <option key={pageNumber} value={pageNumber}>第 {pageNumber} 页</option>
                ))}
              </select>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                共 {totalPages} 页
              </span>
              <button className="btn-secondary btn-sm" aria-label="下一页" title="下一页" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)}>
                <ChevronRight size={14} />
              </button>
              <button className="btn-secondary btn-sm" aria-label="最后一页" title="最后一页"
                disabled={page >= totalPages}
                onClick={() => setPage(totalPages)}>
                <ChevronsRight size={14} />
              </button>
            </div>
          )}
        </>
      ) : null}
    </div>
  )
}
