import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchEmail, patchEmail, classifyEmail, summarizeEmail, generateDraft, extractReminders } from '../api/emails'
import { CategoryBadge } from '../components/CategoryBadge'
import { ImportanceRating } from '../components/ImportanceRating'
import { ArrowLeft, RefreshCw, FileText, Bell } from 'lucide-react'
import { useState } from 'react'

const CATEGORIES = ['important', 'normal', 'promotion', 'bill', 'school_work', 'needs_reply', 'spam']
const TONES = [
  { value: 'formal', label: 'Formal' },
  { value: 'brief', label: 'Brief' },
  { value: 'polite_decline', label: 'Polite Decline' },
  { value: 'ask_info', label: 'Ask Info' },
]

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

  if (isLoading) return <div className="empty-state">Loading...</div>
  if (!data) return <div className="empty-state">Email not found.</div>

  return (
    <div>
      <button className="btn-secondary btn-sm" onClick={() => navigate('/emails')}
        style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 4 }}>
        <ArrowLeft size={14} /> Back
      </button>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{data.subject}</h1>
        <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.75rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', flexWrap: 'wrap' }}>
          <span><strong>From:</strong> {data.sender}</span>
          <span><strong>To:</strong> {data.recipients}</span>
          <span><strong>Received:</strong> {new Date(data.received_at).toLocaleString()}</span>
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
              <option key={c} value={c}>{c.replace('_', ' ')}</option>
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
          {classifyMut.isPending ? 'Classifying...' : 'Auto Classify'}
        </button>
        <button className="btn-secondary btn-sm" onClick={() => summarizeMut.mutate()}
          disabled={summarizeMut.isPending}>
          <FileText size={14} style={{ marginRight: 4 }} />
          {summarizeMut.isPending ? 'Summarizing...' : 'Generate Summary'}
        </button>
        <button className="btn-secondary btn-sm" onClick={() => reminderMut.mutate()}
          disabled={reminderMut.isPending}>
          <Bell size={14} style={{ marginRight: 4 }} />
          {reminderMut.isPending ? 'Extracting...' : 'Extract Reminders'}
        </button>
      </div>

      {data.summary && (
        <div className="card" style={{ marginBottom: '1rem', background: '#f0fdf4', borderColor: '#bbf7d0' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Summary</h3>
          <p style={{ fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>{data.summary}</p>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Generate Reply Draft</h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <select value={draftTone} onChange={(e) => setDraftTone(e.target.value)}>
            {TONES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
          <button className="btn-primary btn-sm" onClick={() => draftMut.mutate(draftTone)}
            disabled={draftMut.isPending}>
            Generate
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
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Related Drafts</h3>
          {data.drafts.map((d) => (
            <div key={d.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                Tone: {d.tone} &middot; Status: {d.status}
              </div>
              <div style={{ fontSize: '0.8125rem', whiteSpace: 'pre-wrap', marginTop: 4 }}>{d.content.slice(0, 200)}...</div>
            </div>
          ))}
        </div>
      )}

      {data.reminders.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Related Reminders</h3>
          {data.reminders.map((r) => (
            <div key={r.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--color-border)' }}>
              <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{r.title}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                {r.reminder_type} &middot; {r.due_at ? new Date(r.due_at).toLocaleDateString() : 'No due date'} &middot; {r.status}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
