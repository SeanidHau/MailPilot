import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Brain, Database, ExternalLink, Mail, RefreshCw, Save, Unlink, Upload } from 'lucide-react'
import { importEmails } from '../api/emails'
import {
  disconnectGmail,
  fetchAISettings,
  fetchGmailAuthorizationUrl,
  fetchGmailStatus,
  refreshGmailToken,
  updateAISettings,
} from '../api/settings'
import type { AIProvider, AIProviderConfig } from '../types/settings'

const PROVIDERS: { value: AIProvider; label: string }[] = [
  { value: 'mock', label: 'Mock rules' },
  { value: 'openai', label: 'OpenAI compatible' },
  { value: 'anthropic', label: 'Anthropic' },
]

const defaultConfig: AIProviderConfig = {
  provider: 'mock',
  openai_api_key: '',
  openai_base_url: 'https://api.openai.com/v1',
  openai_model: 'gpt-4o',
  anthropic_api_key: '',
  anthropic_base_url: 'https://api.anthropic.com',
  anthropic_model: 'claude-sonnet-4-5-20250929',
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  marginTop: '0.375rem',
  marginBottom: '0.75rem',
}

const labelStyle: React.CSSProperties = {
  fontSize: '0.8125rem',
  fontWeight: 500,
  color: 'var(--color-text-muted)',
  marginTop: '0.5rem',
}

const panelStyle: React.CSSProperties = {
  padding: '0.75rem',
  background: '#f8fafc',
  borderRadius: 'var(--radius)',
  marginBottom: '0.5rem',
}

function noticeStyle(ok: boolean): React.CSSProperties {
  return {
    marginTop: '0.75rem',
    padding: '0.5rem 0.75rem',
    borderRadius: 'var(--radius)',
    background: ok ? '#f0fdf4' : '#fef2f2',
    color: ok ? '#166534' : '#991b1b',
    fontSize: '0.875rem',
  }
}

export function SettingsPage() {
  const queryClient = useQueryClient()
  const [importMsg, setImportMsg] = useState('')
  const [saveMsg, setSaveMsg] = useState('')
  const [gmailMsg, setGmailMsg] = useState('')
  const [config, setConfig] = useState<AIProviderConfig>(defaultConfig)

  const { data: savedConfig } = useQuery({
    queryKey: ['aiSettings'],
    queryFn: fetchAISettings,
  })

  const { data: gmailStatus } = useQuery({
    queryKey: ['gmailStatus'],
    queryFn: fetchGmailStatus,
  })

  useEffect(() => {
    if (savedConfig) setConfig(savedConfig)
  }, [savedConfig])

  const importMut = useMutation({
    mutationFn: importEmails,
    onSuccess: (data) => {
      setImportMsg(`Imported ${data.imported} emails.`)
      queryClient.invalidateQueries()
    },
    onError: (err: Error) => setImportMsg(`Import failed: ${err.message}`),
  })

  const saveMut = useMutation({
    mutationFn: updateAISettings,
    onSuccess: () => {
      setSaveMsg('AI settings saved.')
      queryClient.invalidateQueries({ queryKey: ['aiSettings'] })
    },
    onError: (err: Error) => setSaveMsg(`Save failed: ${err.message}`),
  })

  const connectGmailMut = useMutation({
    mutationFn: fetchGmailAuthorizationUrl,
    onSuccess: ({ authorization_url }) => {
      window.location.href = authorization_url
    },
    onError: (err: Error) => setGmailMsg(`Gmail authorization failed: ${err.message}`),
  })

  const refreshGmailMut = useMutation({
    mutationFn: refreshGmailToken,
    onSuccess: () => {
      setGmailMsg('Gmail token refreshed.')
      queryClient.invalidateQueries({ queryKey: ['gmailStatus'] })
    },
    onError: (err: Error) => setGmailMsg(`Refresh failed: ${err.message}`),
  })

  const disconnectGmailMut = useMutation({
    mutationFn: disconnectGmail,
    onSuccess: () => {
      setGmailMsg('Gmail disconnected.')
      queryClient.invalidateQueries({ queryKey: ['gmailStatus'] })
    },
    onError: (err: Error) => setGmailMsg(`Disconnect failed: ${err.message}`),
  })

  const update = (patch: Partial<AIProviderConfig>) => setConfig((c) => ({ ...c, ...patch }))

  return (
    <div>
      <div className="page-header"><h1>Settings</h1></div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Brain size={18} /> AI Provider
          </h2>

          <label style={labelStyle}>Provider</label>
          <select
            value={config.provider}
            onChange={(e) => update({ provider: e.target.value as AIProvider })}
            style={inputStyle}
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>

          {config.provider === 'openai' && (
            <div style={panelStyle}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>OpenAI compatible</h3>
              <label style={labelStyle}>API Key</label>
              <input type="password" placeholder="sk-..." value={config.openai_api_key} onChange={(e) => update({ openai_api_key: e.target.value })} style={inputStyle} />
              <label style={labelStyle}>Base URL</label>
              <input type="text" placeholder="https://api.openai.com/v1" value={config.openai_base_url} onChange={(e) => update({ openai_base_url: e.target.value })} style={inputStyle} />
              <label style={labelStyle}>Model</label>
              <input type="text" placeholder="gpt-4o" value={config.openai_model} onChange={(e) => update({ openai_model: e.target.value })} style={inputStyle} />
            </div>
          )}

          {config.provider === 'anthropic' && (
            <div style={panelStyle}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Anthropic</h3>
              <label style={labelStyle}>API Key</label>
              <input type="password" placeholder="sk-ant-..." value={config.anthropic_api_key} onChange={(e) => update({ anthropic_api_key: e.target.value })} style={inputStyle} />
              <label style={labelStyle}>Base URL</label>
              <input type="text" placeholder="https://api.anthropic.com" value={config.anthropic_base_url} onChange={(e) => update({ anthropic_base_url: e.target.value })} style={inputStyle} />
              <label style={labelStyle}>Model</label>
              <input type="text" placeholder="claude-sonnet-4-5-20250929" value={config.anthropic_model} onChange={(e) => update({ anthropic_model: e.target.value })} style={inputStyle} />
            </div>
          )}

          {config.provider === 'mock' && (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
              Mock uses local rules and does not need an API key.
            </p>
          )}

          <button className="btn-primary" onClick={() => saveMut.mutate(config)} disabled={saveMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Save size={14} />
            {saveMut.isPending ? 'Saving...' : 'Save AI Settings'}
          </button>
          {saveMsg && <div style={noticeStyle(saveMsg.startsWith('AI'))}>{saveMsg}</div>}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mail size={18} /> Gmail Integration
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            Connect Gmail with OAuth. Access and refresh tokens are encrypted before being stored.
          </p>
          <div style={{ marginBottom: '0.75rem', fontSize: '0.875rem' }}>
            Status: {gmailStatus?.connected ? `Connected${gmailStatus.email ? ` as ${gmailStatus.email}` : ''}` : 'Not connected'}
            {gmailStatus?.expires_at && (
              <span style={{ color: 'var(--color-text-muted)' }}> · expires {new Date(gmailStatus.expires_at).toLocaleString()}</span>
            )}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <button className="btn-primary" onClick={() => connectGmailMut.mutate()} disabled={connectGmailMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <ExternalLink size={14} />
              {gmailStatus?.connected ? 'Reconnect Gmail' : 'Connect Gmail'}
            </button>
            <button className="btn-secondary" onClick={() => refreshGmailMut.mutate()} disabled={!gmailStatus?.connected || refreshGmailMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <RefreshCw size={14} />
              Refresh Token
            </button>
            <button className="btn-secondary" onClick={() => disconnectGmailMut.mutate()} disabled={!gmailStatus?.connected || disconnectGmailMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Unlink size={14} />
              Disconnect
            </button>
          </div>
          {gmailMsg && <div style={noticeStyle(!gmailMsg.includes('failed'))}>{gmailMsg}</div>}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Upload size={18} /> Mock Data Import
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            Import bundled mock email data for local development.
          </p>
          <button className="btn-primary" onClick={() => importMut.mutate()} disabled={importMut.isPending}>
            {importMut.isPending ? 'Importing...' : 'Import Mock Emails'}
          </button>
          {importMsg && <div style={noticeStyle(importMsg.startsWith('Imported'))}>{importMsg}</div>}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Database size={18} /> Database
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            PostgreSQL is used by default. Start it with <code>docker compose up -d db</code>, then run backend migrations.
          </p>
        </div>
      </div>
    </div>
  )
}
