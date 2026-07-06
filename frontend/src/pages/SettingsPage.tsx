import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { importEmails } from '../api/emails'
import { Upload, Database, Brain, Mail } from 'lucide-react'

export function SettingsPage() {
  const queryClient = useQueryClient()
  const [message, setMessage] = useState('')

  const importMut = useMutation({
    mutationFn: importEmails,
    onSuccess: (data) => {
      setMessage(`Successfully imported ${data.imported} emails.`)
      queryClient.invalidateQueries()
    },
    onError: (err: Error) => setMessage(`Import failed: ${err.message}`),
  })

  return (
    <div>
      <div className="page-header"><h1>Settings</h1></div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Upload size={18} /> Mock Data Import
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            Import sample email data from the local mock JSON file. Duplicate emails (by Message-ID) will be skipped.
          </p>
          <button className="btn-primary" onClick={() => importMut.mutate()} disabled={importMut.isPending}>
            {importMut.isPending ? 'Importing...' : 'Import Mock Emails'}
          </button>
          {message && (
            <div style={{
              marginTop: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius)',
              background: message.startsWith('Success') ? '#f0fdf4' : '#fef2f2',
              color: message.startsWith('Success') ? '#166534' : '#991b1b',
              fontSize: '0.875rem',
            }}>
              {message}
            </div>
          )}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Brain size={18} /> AI Provider
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            Current provider: <strong>Mock (Rule-based)</strong>. The mock AI provider uses keyword and regex matching for classification, summarization, draft generation, and reminder extraction. Future versions will support real LLM API integration.
          </p>
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mail size={18} /> Mailbox Integration
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            Gmail and Outlook integration is planned for future releases. Currently using mock JSON data import as the only email source.
          </p>
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Database size={18} /> Database
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            SQLite (local file) is the default database for the demo. For production, switch to PostgreSQL by updating <code>DATABASE_URL</code> in <code>.env</code> and running <code>docker compose up -d db</code>.
          </p>
        </div>
      </div>
    </div>
  )
}
