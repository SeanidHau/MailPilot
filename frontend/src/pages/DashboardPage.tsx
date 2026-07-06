import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { fetchDashboard } from '../api/dashboard'
import { StatCard } from '../components/StatCard'
import { CategoryBadge } from '../components/CategoryBadge'
import { Mail, AlertTriangle, Bell, Star } from 'lucide-react'

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })
  const navigate = useNavigate()

  if (isLoading) return <div className="empty-state">Loading...</div>
  if (!data) return null

  return (
    <div>
      <div className="page-header"><h1>Dashboard</h1></div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <StatCard label="Pending Emails" value={data.pending_emails} color="#f59e0b" />
        <StatCard label="Important" value={data.important_emails} color="#ef4444" />
        <StatCard label="Pending Reminders" value={data.pending_reminders} color="#3b82f6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
            <Star size={16} style={{ marginRight: 6 }} />
            Recent Important Emails
          </h2>
          {data.recent_important_emails.length === 0 ? (
            <div className="empty-state">No important emails</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {data.recent_important_emails.map((e) => (
                <div key={e.id} className="card" onClick={() => navigate(`/emails/${e.id}`)}
                  style={{ cursor: 'pointer' }}>
                  <div style={{ fontWeight: 600 }}>{e.subject}</div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: 4, fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                    <span>{e.sender}</span>
                    <CategoryBadge category={e.category} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
            <Bell size={16} style={{ marginRight: 6 }} />
            Upcoming Reminders
          </h2>
          {data.upcoming_reminders.length === 0 ? (
            <div className="empty-state">No upcoming reminders</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {data.upcoming_reminders.map((r) => (
                <div key={r.id} className="card">
                  <div style={{ fontWeight: 600 }}>{r.title}</div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
                    {r.email_subject}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
                    {r.due_at ? new Date(r.due_at).toLocaleDateString() : 'No due date'} &middot; {r.reminder_type}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
