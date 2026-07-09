import { Link } from 'react-router-dom'
import { CheckCircle2, FileJson, Settings, UserPlus } from 'lucide-react'

const steps = [
  {
    icon: UserPlus,
    title: 'Create your account',
    body: 'You are signed in, so MailPilot can keep mailbox data and AI settings tied to your user.',
    done: true,
  },
  {
    icon: FileJson,
    title: 'Import starter mail',
    body: 'Use bundled mock emails or upload a JSON array to populate the inbox for demos and testing.',
    to: '/settings#import',
  },
  {
    icon: Settings,
    title: 'Choose an AI provider',
    body: 'Keep mock rules for local work, or configure OpenAI-compatible or Anthropic credentials.',
    to: '/settings#ai-provider',
  },
]

export function OnboardingSteps() {
  return (
    <div className="card" style={{ padding: '1rem' }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>Getting started</h2>
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
                Open
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
