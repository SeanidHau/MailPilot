import { Link } from 'react-router-dom'
import { CheckCircle2, FileJson, Settings, UserPlus } from 'lucide-react'

const steps = [
  {
    icon: UserPlus,
    title: '创建账号',
    body: '邮箱数据、AI 配置和草稿会绑定到当前账号。',
    done: true,
  },
  {
    icon: FileJson,
    title: '接入邮件数据',
    body: '连接 Gmail 或 Outlook，也可以批量导入已有邮件归档。',
    to: '/settings#mailboxes',
    action: '连接邮箱',
  },
  {
    icon: Settings,
    title: '选择 AI 提供方',
    body: '使用内置规则引擎，或配置 OpenAI 兼容接口、Anthropic 凭据。',
    to: '/settings#ai-provider',
    action: '配置 AI',
  },
]

export function OnboardingSteps() {
  return (
    <div className="card" style={{ padding: '1rem' }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>接入清单</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
        {steps.map(({ icon: Icon, title, body, done, to, action }) => (
          <div
            key={title}
            style={{
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius)',
              padding: '0.875rem',
              background: '#fff',
              minHeight: 154,
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {done ? <CheckCircle2 size={18} color="var(--color-success)" /> : <Icon size={18} color="var(--color-primary)" />}
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 700 }}>{title}</h3>
            </div>
            <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem', lineHeight: 1.45, flex: 1 }}>{body}</p>
            {to && (
              <Link to={to} className="btn-secondary" style={{ alignSelf: 'flex-start', textDecoration: 'none' }}>
                {action}
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
