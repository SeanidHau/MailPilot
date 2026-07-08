import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Mail, FileText, Bell, Settings, LogOut, User } from 'lucide-react'
import { useAuth } from '../app/AuthContext'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/emails', icon: Mail, label: '邮件' },
  { to: '/drafts', icon: FileText, label: '草稿' },
  { to: '/reminders', icon: Bell, label: '提醒' },
  { to: '/settings', icon: Settings, label: '设置' },
]

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

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
        <div style={{ marginTop: 'auto', borderTop: '1px solid var(--color-border)', paddingTop: '0.75rem' }}>
          {user ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '0.5rem 0.75rem', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                <User size={14} /> {user.email}
              </div>
              <button
                onClick={() => { logout(); navigate('/login'); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '0.5rem 0.75rem',
                  borderRadius: 'var(--radius)', fontSize: '0.875rem', cursor: 'pointer',
                  background: 'transparent', color: 'var(--color-text)', border: 'none',
                }}
              >
                <LogOut size={16} /> 退出登录
              </button>
            </>
          ) : (
            <NavLink to="/login" style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '0.5rem 0.75rem', borderRadius: 'var(--radius)',
              background: isActive ? 'var(--color-primary)' : 'transparent',
              color: isActive ? '#fff' : 'var(--color-text)',
              textDecoration: 'none', fontSize: '0.9rem',
            })}>
              <User size={18} /> 登录
            </NavLink>
          )}
        </div>
      </aside>
      <main style={{ flex: 1, padding: '2rem', maxWidth: 1100 }}>
        <Outlet />
      </main>
    </div>
  )
}
