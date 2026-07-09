import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight, Bell, Inbox, Star } from 'lucide-react'
import { fetchDashboard } from '../api/dashboard'
import { StatCard } from '../components/StatCard'
import { CategoryBadge } from '../components/CategoryBadge'
import { OnboardingSteps } from '../components/OnboardingSteps'

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })
  const navigate = useNavigate()

  if (isLoading) return <div className="empty-state">Loading...</div>
  if (!data) return null

  const isEmpty = data.total_emails === 0

  if (isEmpty) {
    return (
      <div>
        <div className="page-header"><h1>Dashboard</h1></div>
        <div style={{ marginBottom: '1rem' }}>
          <OnboardingSteps />
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
          <Inbox size={48} style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem' }}>Welcome to MailPilot</h2>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem', maxWidth: 440, marginLeft: 'auto', marginRight: 'auto' }}>
            Import mock data, upload JSON, or connect a mailbox from settings to start reviewing emails.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/settings#import" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}>
              Open import tools <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header"><h1>Dashboard</h1></div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <StatCard label="Pending emails" value={data.pending_emails} color="#f59e0b" />
        <StatCard label="Important emails" value={data.important_emails} color="#ef4444" />
        <StatCard label="Pending reminders" value={data.pending_reminders} color="#3b82f6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
            <Star size={16} style={{ marginRight: 6 }} />
            Recent important emails
          </h2>
          {data.recent_important_emails.length === 0 ? (
            <div className="empty-state">No important emails yet.</div>
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
            Upcoming reminders
          </h2>
          {data.upcoming_reminders.length === 0 ? (
            <div className="empty-state">No reminders yet.</div>
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
