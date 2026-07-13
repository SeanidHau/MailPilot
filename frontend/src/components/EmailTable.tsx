import { useNavigate } from 'react-router-dom'
import type { EmailResponse } from '../types/email'
import { CategoryBadge } from './CategoryBadge'
import { ImportanceRating } from './ImportanceRating'
import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react'

type SortBy = 'received_at' | 'importance'
type SortOrder = 'asc' | 'desc'

interface Props {
  emails: EmailResponse[]
  selectedIds: Set<number>
  processingEmailId?: number | null
  sortBy: SortBy
  sortOrder: SortOrder
  onToggle: (id: number) => void
  onToggleAll: (checked: boolean) => void
  onSort: (sortBy: SortBy) => void
}

export function EmailTable({ emails, selectedIds, processingEmailId, sortBy, sortOrder, onToggle, onToggleAll, onSort }: Props) {
  const navigate = useNavigate()

  const sortIcon = (column: SortBy) => {
    if (sortBy !== column) return <ArrowUpDown size={13} aria-hidden="true" />
    return sortOrder === 'asc'
      ? <ArrowUp size={13} aria-hidden="true" />
      : <ArrowDown size={13} aria-hidden="true" />
  }

  const sortLabel = (column: SortBy, label: string) => (
    <button
      type="button"
      className="table-sort-button"
      onClick={() => onSort(column)}
      title={`${label}：${sortBy === column && sortOrder === 'asc' ? '升序' : '降序'}`}
      aria-label={`按${label}排序，当前${sortBy === column ? (sortOrder === 'asc' ? '升序' : '降序') : '未排序'}`}
    >
      <span>{label}</span>
      {sortIcon(column)}
    </button>
  )

  if (emails.length === 0) {
    return <div className="empty-state">暂无邮件。</div>
  }

  return (
    <div className="card email-table-container" style={{ padding: 0, overflow: 'auto' }}>
      <table className="email-table">
        <colgroup>
          <col className="email-col-select" />
          <col className="email-col-sender" />
          <col className="email-col-subject" />
          <col className="email-col-category" />
          <col className="email-col-importance" />
          <col className="email-col-ai" />
          <col className="email-col-received" />
        </colgroup>
        <thead>
          <tr>
            <th>
              <input
                type="checkbox"
                aria-label="全选当前页邮件"
                checked={emails.length > 0 && emails.every((email) => selectedIds.has(email.id))}
                onChange={(event) => onToggleAll(event.target.checked)}
                onClick={(event) => event.stopPropagation()}
              />
            </th>
            <th>发件人</th>
            <th>主题</th>
            <th>分类</th>
            <th aria-sort={sortBy === 'importance' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}>
              {sortLabel('importance', '重要性')}
            </th>
            <th>AI 状态</th>
            <th aria-sort={sortBy === 'received_at' ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'}>
              {sortLabel('received_at', '接收时间')}
            </th>
          </tr>
        </thead>
        <tbody>
          {emails.map((email) => (
            <tr
              key={email.id}
              onClick={() => navigate(`/emails/${email.id}`)}
              style={{ cursor: 'pointer', fontWeight: email.is_read ? 400 : 600 }}
            >
              <td onClick={(event) => event.stopPropagation()}>
                <input
                  type="checkbox"
                  aria-label={`选择邮件：${email.subject}`}
                  checked={selectedIds.has(email.id)}
                  onChange={() => onToggle(email.id)}
                />
              </td>
              <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {email.sender}
              </td>
              <td style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {email.subject}
              </td>
              <td><CategoryBadge category={email.category} /></td>
              <td><ImportanceRating score={email.importance_score} /></td>
              <td>
                <span style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  padding: '0.2rem 0.45rem',
                  borderRadius: 999,
                  fontSize: '0.75rem',
                  color: processingEmailId === email.id ? '#92400e' : email.ai_processed ? '#166534' : '#64748b',
                  background: processingEmailId === email.id ? '#fef3c7' : email.ai_processed ? '#dcfce7' : '#f1f5f9',
                  whiteSpace: 'nowrap',
                }}>
                  {processingEmailId === email.id ? '处理中' : email.ai_processed ? '已完成' : '待处理'}
                </span>
              </td>
              <td style={{ whiteSpace: 'nowrap', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                {new Date(email.received_at).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
