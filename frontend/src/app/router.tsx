import { Routes, Route } from 'react-router-dom'
import { Layout } from '../components/Layout'
import { DashboardPage } from '../pages/DashboardPage'
import { EmailsPage } from '../pages/EmailsPage'
import { EmailDetailPage } from '../pages/EmailDetailPage'
import { DraftsPage } from '../pages/DraftsPage'
import { RemindersPage } from '../pages/RemindersPage'
import { SettingsPage } from '../pages/SettingsPage'

export function AppRouter() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/emails" element={<EmailsPage />} />
        <Route path="/emails/:id" element={<EmailDetailPage />} />
        <Route path="/drafts" element={<DraftsPage />} />
        <Route path="/reminders" element={<RemindersPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
