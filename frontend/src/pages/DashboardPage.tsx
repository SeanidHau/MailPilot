import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  ArrowRight,
  Bell,
  CheckCircle2,
  Clock3,
  Inbox,
  MailPlus,
  PlugZap,
  Sparkles,
  Star,
  Upload,
} from 'lucide-react'
import { fetchDashboard } from '../api/dashboard'
import { CategoryBadge } from '../components/CategoryBadge'
import { OnboardingSteps } from '../components/OnboardingSteps'

function formatDate(value: string | null) {
  if (!value) return '无截止日期'
  return new Date(value).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

export function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ['dashboard'], queryFn: fetchDashboard })
  const navigate = useNavigate()

  if (isLoading) return <div className="empty-state">加载中...</div>
  if (!data) return null

  const isEmpty = data.total_emails === 0

  if (isEmpty) {
    return (
      <div className="dashboard-page">
        <section className="dashboard-hero dashboard-hero-empty">
          <div className="dashboard-hero-copy">
            <div className="dashboard-eyebrow">MailPilot Command Desk</div>
            <h1>把收件箱接入你的工作台</h1>
            <p>
              还没有邮件数据。导入示例数据、上传 JSON 文件，或连接邮箱后，MailPilot 会开始整理分类、草稿和提醒。
            </p>
            <div className="dashboard-actions">
              <Link to="/settings#import" className="dashboard-primary-action">
                导入邮件 <ArrowRight size={16} />
              </Link>
              <Link to="/emails" className="dashboard-secondary-action">
                查看邮件页
              </Link>
            </div>
          </div>

          <div className="dashboard-empty-orbit" aria-hidden="true">
            <div className="dashboard-inbox-mark">
              <Inbox size={44} />
            </div>
            <div className="orbit-step orbit-step-a">
              <MailPlus size={18} />
              <span>示例数据</span>
            </div>
            <div className="orbit-step orbit-step-b">
              <Upload size={18} />
              <span>JSON 上传</span>
            </div>
            <div className="orbit-step orbit-step-c">
              <PlugZap size={18} />
              <span>邮箱连接</span>
            </div>
          </div>
        </section>

        <OnboardingSteps />
      </div>
    )
  }

  return (
    <div className="dashboard-page">
      <section className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <div className="dashboard-eyebrow">Today in MailPilot</div>
          <h1>今天的邮件处理台</h1>
          <p>优先处理未读、重要事项和即将到期的提醒。</p>
        </div>
        <div className="dashboard-health-strip" aria-label="今日处理概览">
          <div>
            <span>总邮件</span>
            <strong>{data.total_emails}</strong>
          </div>
          <div>
            <span>待处理</span>
            <strong>{data.pending_emails}</strong>
          </div>
          <div>
            <span>提醒</span>
            <strong>{data.pending_reminders}</strong>
          </div>
        </div>
      </section>

      <div className="dashboard-metrics">
        <div className="dashboard-metric metric-mail">
          <div className="metric-icon"><Clock3 size={20} /></div>
          <span>待处理邮件</span>
          <strong>{data.pending_emails}</strong>
          <small>{data.pending_emails > 0 ? '需要归档或阅读' : '当前清爽'}</small>
        </div>
        <div className="dashboard-metric metric-important">
          <div className="metric-icon"><Star size={20} /></div>
          <span>重要邮件</span>
          <strong>{data.important_emails}</strong>
          <small>{data.important_emails > 0 ? '建议优先查看' : '暂无高优先级'}</small>
        </div>
        <div className="dashboard-metric metric-reminder">
          <div className="metric-icon"><Bell size={20} /></div>
          <span>待办提醒</span>
          <strong>{data.pending_reminders}</strong>
          <small>{data.pending_reminders > 0 ? '有事项待完成' : '没有悬而未决'}</small>
        </div>
      </div>

      <div className="dashboard-work-grid">
        <section className="dashboard-section">
          <div className="dashboard-section-header">
            <div>
              <span className="dashboard-section-kicker">Priority</span>
              <h2><Star size={18} /> 最近重要邮件</h2>
            </div>
            <Link to="/emails" className="dashboard-link">全部邮件 <ArrowRight size={14} /></Link>
          </div>
          {data.recent_important_emails.length === 0 ? (
            <div className="dashboard-inline-empty">
              <CheckCircle2 size={22} />
              <span>暂无重要邮件</span>
            </div>
          ) : (
            <div className="dashboard-list">
              {data.recent_important_emails.map((e) => (
                <button key={e.id} className="dashboard-mail-row" onClick={() => navigate(`/emails/${e.id}`)}>
                  <span className="mail-score">{e.importance_score}</span>
                  <span className="mail-main">
                    <strong>{e.subject}</strong>
                    <small>{e.sender}</small>
                  </span>
                  <span className="mail-meta">
                    <CategoryBadge category={e.category} />
                    <small>{formatDate(e.received_at)}</small>
                  </span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="dashboard-section">
          <div className="dashboard-section-header">
            <div>
              <span className="dashboard-section-kicker">Action</span>
              <h2><Bell size={18} /> 近期提醒</h2>
            </div>
            <Link to="/reminders" className="dashboard-link">全部提醒 <ArrowRight size={14} /></Link>
          </div>
          {data.upcoming_reminders.length === 0 ? (
            <div className="dashboard-inline-empty">
              <Sparkles size={22} />
              <span>暂无提醒</span>
            </div>
          ) : (
            <div className="dashboard-list">
              {data.upcoming_reminders.map((r) => (
                <div key={r.id} className="dashboard-reminder-row">
                  <span className="reminder-type"><AlertCircle size={16} /></span>
                  <div>
                    <strong>{r.title}</strong>
                    <small>{r.email_subject}</small>
                    <span>{formatDate(r.due_at)} · {r.reminder_type}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
