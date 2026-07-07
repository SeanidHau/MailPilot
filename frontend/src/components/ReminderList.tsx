import type { ReminderResponse } from '../types/reminder'
import { Calendar, CheckCircle2, Trash2 } from 'lucide-react'

const TYPE_LABELS: Record<string, string> = {
  deadline: '截止日期', meeting: '会议', payment: '付款', reply_task: '回复任务', other: '其他',
}

interface Props {
  reminders: ReminderResponse[]
  onComplete?: (id: number) => void
  onDelete?: (id: number) => void
}

export function ReminderList({ reminders, onComplete, onDelete }: Props) {
  if (reminders.length === 0) {
    return <div className="empty-state">暂无提醒。</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {reminders.map((r) => (
        <div key={r.id} className="card" style={{
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          opacity: r.status === 'done' ? 0.5 : 1,
        }}>
          <div>
            <div style={{ fontWeight: 600, textDecoration: r.status === 'done' ? 'line-through' : 'none' }}>
              {r.title}
            </div>
            {r.description && (
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>{r.description}</div>
            )}
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: 4, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <Calendar size={12} /> {r.due_at ? new Date(r.due_at).toLocaleDateString() : '无截止日期'}
              </span>
              <span>{TYPE_LABELS[r.reminder_type] || r.reminder_type}</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {r.status === 'pending' && onComplete && (
              <button className="btn-sm" style={{ background: 'var(--color-success)', color: '#fff' }}
                onClick={() => onComplete(r.id)}>
                <CheckCircle2 size={14} style={{ marginRight: 4 }} /> 完成
              </button>
            )}
            {r.status !== 'deleted' && onDelete && (
              <button className="btn-sm btn-danger" onClick={() => onDelete(r.id)}>
                <Trash2 size={14} />
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
