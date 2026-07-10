import { Link } from 'react-router-dom'
import { CheckCircle2, FileJson, Settings, UserPlus } from 'lucide-react'

const steps = [
  {
    icon: UserPlus,
    title: '创建账号',
    body: '你已登录，MailPilot 会把邮箱数据和 AI 设置绑定到当前用户。',
    done: true,
  },
  {
    icon: FileJson,
    title: '导入起步邮件',
    body: '导入内置示例邮件，或上传 JSON 数组，为演示和测试填充收件箱。',
    to: '/settings#import',
  },
  {
    icon: Settings,
    title: '选择 AI 提供方',
    body: '本地开发可继续使用规则模拟，也可以配置 OpenAI 兼容接口或 Anthropic 凭据。',
    to: '/settings#ai-provider',
  },
]

export function OnboardingSteps() {
  return (
    <div className="card" style={{ padding: '1rem' }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>新手引导</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
        {steps.map(({ icon: Icon, title, body, done, to }) => (
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
                打开
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
