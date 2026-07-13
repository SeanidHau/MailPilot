import type { ReminderResponse } from '../types/reminder'
import { Calendar, CheckCircle2, Trash2 } from 'lucide-react'

const TYPE_LABELS: Record<string, string> = {
  deadline: '截止日期', meeting: '会议', payment: '付款', reply_task: '回复任务', other: '其他',
}

interface Props {
  reminders: ReminderResponse[]
  selectedIds?: Set<number>
  onToggle?: (id: number) => void
  onComplete?: (id: number) => void
  onDelete?: (id: number) => void
}

export function ReminderList({ reminders, selectedIds, onToggle, onComplete, onDelete }: Props) {
  if (reminders.length === 0) {
    return <div className="empty-state">暂无提醒。</div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {reminders.map((r) => (
        <div key={r.id} className={`card reminder-card${onToggle ? ' reminder-card-selectable' : ''}`} style={{ opacity: r.status === 'done' ? 0.5 : 1 }}>
          {onToggle && (
            <label className="reminder-select" aria-label={`选择提醒：${r.title}`}>
              <input
                type="checkbox"
                checked={selectedIds?.has(r.id) || false}
                onChange={() => onToggle(r.id)}
              />
            </label>
          )}
          <div className="reminder-card-content">
            <div className="reminder-title" style={{ textDecoration: r.status === 'done' ? 'line-through' : 'none' }}>
              {r.title}
            </div>
            {r.description && (
              <div className="reminder-description">{r.description}</div>
            )}
            <div className="reminder-meta">
              <span className="reminder-meta-item">
                <Calendar size={12} /> {r.due_at ? new Date(r.due_at).toLocaleDateString() : '无截止日期'}
              </span>
              <span>{TYPE_LABELS[r.reminder_type] || r.reminder_type}</span>
            </div>
          </div>
          <div className="reminder-actions">
            {r.status === 'pending' && onComplete && (
              <button className="btn-sm reminder-complete-button" style={{ background: 'var(--color-success)', color: '#fff' }}
                onClick={() => onComplete(r.id)}>
                <CheckCircle2 size={14} />
                <span>完成</span>
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
