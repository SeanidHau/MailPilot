import { NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, Mail, FileText, Bell, Settings } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/emails', icon: Mail, label: 'Emails' },
  { to: '/drafts', icon: FileText, label: 'Drafts' },
  { to: '/reminders', icon: Bell, label: 'Reminders' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export function Layout() {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{
        width: 220, background: 'var(--color-surface)', borderRight: '1px solid var(--color-border)',
        padding: '1rem', display: 'flex', flexDirection: 'column', gap: 4,
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, padding: '0.5rem 0.75rem', marginBottom: '0.5rem' }}>
          MailPilot
        </h2>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '0.5rem 0.75rem', borderRadius: 'var(--radius)',
              background: isActive ? 'var(--color-primary)' : 'transparent',
              color: isActive ? '#fff' : 'var(--color-text)',
              textDecoration: 'none', fontSize: '0.9rem',
            })}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </aside>
      <main style={{ flex: 1, padding: '2rem', maxWidth: 1100 }}>
        <Outlet />
      </main>
    </div>
  )
}
