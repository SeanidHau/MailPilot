import { useNavigate } from 'react-router-dom'
import type { EmailResponse } from '../types/email'
import { CategoryBadge } from './CategoryBadge'
import { ImportanceRating } from './ImportanceRating'

export function EmailTable({ emails }: { emails: EmailResponse[] }) {
  const navigate = useNavigate()

  if (emails.length === 0) {
    return <div className="empty-state">No emails found.</div>
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'auto' }}>
      <table>
        <thead>
          <tr>
            <th style={{ width: 30 }}></th>
            <th>Sender</th>
            <th>Subject</th>
            <th>Category</th>
            <th>Importance</th>
            <th>Received</th>
          </tr>
        </thead>
        <tbody>
          {emails.map((email) => (
            <tr
              key={email.id}
              onClick={() => navigate(`/emails/${email.id}`)}
              style={{ cursor: 'pointer', fontWeight: email.is_read ? 400 : 600 }}
            >
              <td>
                {!email.is_read && (
                  <span style={{
                    display: 'inline-block', width: 8, height: 8, borderRadius: '50%',
                    background: 'var(--color-primary)',
                  }} />
                )}
              </td>
              <td style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {email.sender}
              </td>
              <td style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {email.subject}
              </td>
              <td><CategoryBadge category={email.category} /></td>
              <td><ImportanceRating score={email.importance_score} /></td>
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
