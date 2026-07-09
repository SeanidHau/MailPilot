import { useQuery } from '@tanstack/react-query'
import { useNavigate, Link } from 'react-router-dom'
import { fetchDashboard } from '../api/dashboard'
import { StatCard } from '../components/StatCard'
import { CategoryBadge } from '../components/CategoryBadge'
import { Inbox, Star, Bell, ArrowRight } from 'lucide-react'

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })
  const navigate = useNavigate()

  if (isLoading) return <div className="empty-state">加载中...</div>
  if (!data) return null

  const isEmpty = data.pending_emails === 0 && data.pending_reminders === 0

  if (isEmpty) {
    return (
      <div>
        <div className="page-header"><h1>仪表盘</h1></div>
        <div className="card" style={{ textAlign: 'center', padding: '3rem 2rem' }}>
          <Inbox size={48} style={{ color: 'var(--color-text-muted)', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem' }}>欢迎使用 MailPilot</h2>
          <p style={{ color: 'var(--color-text-muted)', marginBottom: '1.5rem', maxWidth: 400, marginLeft: 'auto', marginRight: 'auto' }}>
            还没有邮件数据。你可以导入示例数据、上传 JSON 文件，或连接邮箱开始使用。
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/settings" className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}>
              前往设置 <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header"><h1>仪表盘</h1></div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <StatCard label="待处理邮件" value={data.pending_emails} color="#f59e0b" />
        <StatCard label="重要邮件" value={data.important_emails} color="#ef4444" />
        <StatCard label="待办提醒" value={data.pending_reminders} color="#3b82f6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>
            <Star size={16} style={{ marginRight: 6 }} />
            最近重要邮件
          </h2>
          {data.recent_important_emails.length === 0 ? (
            <div className="empty-state">暂无重要邮件</div>
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
            近期提醒
          </h2>
          {data.upcoming_reminders.length === 0 ? (
            <div className="empty-state">暂无提醒</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {data.upcoming_reminders.map((r) => (
                <div key={r.id} className="card">
                  <div style={{ fontWeight: 600 }}>{r.title}</div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 2 }}>
                    {r.email_subject}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
                    {r.due_at ? new Date(r.due_at).toLocaleDateString() : '无截止日期'} &middot; {r.reminder_type}
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
