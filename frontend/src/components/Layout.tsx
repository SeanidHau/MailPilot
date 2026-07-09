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
    <div className="app-shell">
      <aside className="app-sidebar">
        <h2 className="app-brand">
          MailPilot
        </h2>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => `app-nav-link${isActive ? ' active' : ''}`}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
        <div className="app-account">
          {user ? (
            <>
              <div className="app-account-email">
                <User size={14} /> {user.email}
              </div>
              <button
                onClick={() => { logout(); navigate('/login'); }}
                className="app-logout"
              >
                <LogOut size={16} /> 退出登录
              </button>
            </>
          ) : (
            <NavLink to="/login" className={({ isActive }) => `app-nav-link${isActive ? ' active' : ''}`}>
              <User size={18} /> 登录
            </NavLink>
          )}
        </div>
      </aside>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}
