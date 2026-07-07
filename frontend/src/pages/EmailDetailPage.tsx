import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchEmail, patchEmail, classifyEmail, summarizeEmail, generateDraft, extractReminders } from '../api/emails'
import { CategoryBadge } from '../components/CategoryBadge'
import { ImportanceRating } from '../components/ImportanceRating'
import { ArrowLeft, RefreshCw, FileText, Bell } from 'lucide-react'
import { useState } from 'react'

const CATEGORIES = ['important', 'normal', 'promotion', 'bill', 'school_work', 'needs_reply', 'spam']
const CATEGORY_LABELS: Record<string, string> = {
  important: '重要', normal: '普通', promotion: '促销', bill: '账单',
  school_work: '学业/工作', needs_reply: '待回复', spam: '垃圾邮件',
}
const TONES = [
  { value: 'formal', label: '正式' },
  { value: 'brief', label: '简洁' },
  { value: 'polite_decline', label: '礼貌拒绝' },
  { value: 'ask_info', label: '询问信息' },
]
const TONE_LABELS: Record<string, string> = { formal: '正式', brief: '简洁', polite_decline: '礼貌拒绝', ask_info: '询问信息' }
const REMINDER_TYPE_LABELS: Record<string, string> = {
  deadline: '截止日期', meeting: '会议', payment: '付款', reply_task: '回复任务', other: '其他',
}
const STATUS_LABELS: Record<string, string> = { pending: '待处理', done: '已完成', deleted: '已删除', draft: '草稿', saved: '已保存' }

export function EmailDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const emailId = Number(id)
  const [draftTone, setDraftTone] = useState('formal')

  const { data, isLoading } = useQuery({
    queryKey: ['email', emailId],
    queryFn: () => fetchEmail(emailId),
  })

  const classifyMut = useMutation({ mutationFn: () => classifyEmail(emailId), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['email', emailId] }) })
  const summarizeMut = useMutation({ mutationFn: () => summarizeEmail(emailId), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['email', emailId] }) })
  const draftMut = useMutation({ mutationFn: (tone: string) => generateDraft(emailId, tone), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['email', emailId] }) })
  const reminderMut = useMutation({ mutationFn: () => extractReminders(emailId), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['email', emailId] }) })
  const patchMut = useMutation({
    mutationFn: (body: Record<string, any>) => patchEmail(emailId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['email', emailId] }),
  })

  if (isLoading) return <div className="empty-state">加载中...</div>
  if (!data) return <div className="empty-state">邮件未找到。</div>

  return (
    <div>
      <button className="btn-secondary btn-sm" onClick={() => navigate('/emails')}
        style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 4 }}>
        <ArrowLeft size={14} /> 返回
      </button>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{data.subject}</h1>
        <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', flexWrap: 'wrap' }}>
          <span><strong>发件人：</strong> {data.sender}</span>
          <span><strong>收件人：</strong> {data.recipients}</span>
          <span><strong>接收时间：</strong> {new Date(data.received_at).toLocaleString()}</span>
        </div>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <CategoryBadge category={data.category} />
          <ImportanceRating score={data.importance_score} />
          <select
            value={data.category}
            onChange={(e) => patchMut.mutate({ category: e.target.value })}
            style={{ fontSize: '0.8125rem' }}
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{CATEGORY_LABELS[c] || c}</option>
            ))}
          </select>
        </div>
        <div style={{ marginTop: '1rem', whiteSpace: 'pre-wrap', lineHeight: 1.7, fontSize: '0.9rem' }}>
          {data.body}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
        <button className="btn-primary btn-sm" onClick={() => classifyMut.mutate()}
          disabled={classifyMut.isPending}>
          <RefreshCw size={14} style={{ marginRight: 4 }} />
          {classifyMut.isPending ? '正在分类...' : '自动分类'}
        </button>
        <button className="btn-secondary btn-sm" onClick={() => summarizeMut.mutate()}
          disabled={summarizeMut.isPending}>
          <FileText size={14} style={{ marginRight: 4 }} />
          {summarizeMut.isPending ? '正在生成摘要...' : '生成摘要'}
        </button>
        <button className="btn-secondary btn-sm" onClick={() => reminderMut.mutate()}
          disabled={reminderMut.isPending}>
          <Bell size={14} style={{ marginRight: 4 }} />
          {reminderMut.isPending ? '正在提取...' : '提取提醒'}
        </button>
      </div>

      {data.summary && (
        <div className="card" style={{ marginBottom: '1rem', background: '#f0fdf4', borderColor: '#bbf7d0' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>摘要</h3>
          <p style={{ fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>{data.summary}</p>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>生成回复草稿</h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <select value={draftTone} onChange={(e) => setDraftTone(e.target.value)}>
            {TONES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <button className="btn-primary btn-sm" onClick={() => draftMut.mutate(draftTone)}
            disabled={draftMut.isPending}>
            生成
          </button>
        </div>
        {draftMut.data && (
          <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: '#f8fafc', borderRadius: 'var(--radius)', whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
            {draftMut.data.content}
          </div>
        )}
      </div>

      {data.drafts.length > 0 && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>相关草稿</h3>
          {data.drafts.map((d) => (
            <div key={d.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                语气：{TONE_LABELS[d.tone] || d.tone} &middot; 状态：{STATUS_LABELS[d.status] || d.status}
              </div>
              <div style={{ fontSize: '0.8125rem', whiteSpace: 'pre-wrap', marginTop: 4 }}>{d.content.slice(0, 200)}...</div>
            </div>
          ))}
        </div>
      )}

      {data.reminders.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>相关提醒</h3>
          {data.reminders.map((r) => (
            <div key={r.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{r.title}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                {REMINDER_TYPE_LABELS[r.reminder_type] || r.reminder_type} &middot; {r.due_at ? new Date(r.due_at).toLocaleDateString() : '无截止日期'} &middot; {STATUS_LABELS[r.status] || r.status}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
