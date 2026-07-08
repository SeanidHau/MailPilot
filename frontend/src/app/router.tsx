import { Routes, Route } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { ProtectedRoute } from '../components/ProtectedRoute'
import { DashboardPage } from '../pages/DashboardPage'
import { EmailsPage } from '../pages/EmailsPage'
import { EmailDetailPage } from '../pages/EmailDetailPage'
import { DraftsPage } from '../pages/DraftsPage'
import { RemindersPage } from '../pages/RemindersPage'
import { SettingsPage } from '../pages/SettingsPage'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/emails" element={<ProtectedRoute><EmailsPage /></ProtectedRoute>} />
        <Route path="/emails/:id" element={<ProtectedRoute><EmailDetailPage /></ProtectedRoute>} />
        <Route path="/drafts" element={<ProtectedRoute><DraftsPage /></ProtectedRoute>} />
        <Route path="/reminders" element={<ProtectedRoute><RemindersPage /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
      </Route>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
    </Routes>
  )
}
