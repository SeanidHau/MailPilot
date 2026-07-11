import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Brain, Database, ExternalLink, FileJson, Mail, RefreshCw, Save, Unlink, Upload } from 'lucide-react'
import { importEmails, uploadEmails } from '../api/emails'
import { syncGmailInbox, syncOutlookInbox } from '../api/sync'
import {
  disconnectGmail,
  disconnectOutlook,
  fetchAISettings,
  fetchGmailAuthorizationUrl,
  fetchGmailStatus,
  fetchOutlookAuthorizationUrl,
  fetchOutlookStatus,
  refreshGmailToken,
  refreshOutlookToken,
  updateAISettings,
} from '../api/settings'
import type { AIProvider, AIProviderConfig } from '../types/settings'

const PROVIDERS: { value: AIProvider; label: string }[] = [
  { value: 'mock', label: '本地规则模拟' },
  { value: 'openai', label: 'OpenAI 兼容接口' },
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

function isAuthError(err: Error) {
  const message = err.message.toLowerCase()
  return message.includes('not authenticated') || message.includes('unauthorized') || message.includes('401')
}

export function SettingsPage() {
  const queryClient = useQueryClient()
  const [importMsg, setImportMsg] = useState('')
  const [uploadMsg, setUploadMsg] = useState('')
  const [jsonText, setJsonText] = useState('')
  const [saveMsg, setSaveMsg] = useState('')
  const [gmailMsg, setGmailMsg] = useState('')
  const [outlookMsg, setOutlookMsg] = useState('')
  const [config, setConfig] = useState<AIProviderConfig>(defaultConfig)

  const { data: savedConfig, error: settingsError } = useQuery({
    queryKey: ['aiSettings'],
    queryFn: fetchAISettings,
  })

  const { data: gmailStatus } = useQuery({
    queryKey: ['gmailStatus'],
    queryFn: fetchGmailStatus,
  })

  const { data: outlookStatus } = useQuery({
    queryKey: ['outlookStatus'],
    queryFn: fetchOutlookStatus,
  })

  useEffect(() => {
    if (savedConfig) setConfig(savedConfig)
  }, [savedConfig])

  const importMut = useMutation({
    mutationFn: importEmails,
    onSuccess: (data) => {
      setImportMsg(`已导入 ${data.imported} 封邮件。`)
      queryClient.invalidateQueries()
    },
    onError: (err: Error) => setImportMsg(`导入失败：${err.message}`),
  })

  const uploadMut = useMutation({
    mutationFn: (emails: Record<string, any>[]) => uploadEmails(emails),
    onSuccess: (data) => {
      setUploadMsg(`已导入 ${data.imported} 条，跳过 ${data.skipped} 条${data.errors.length ? `，${data.errors.length} 个错误` : ''}。`)
      if (data.errors.length > 0) {
        setUploadMsg((m) => m + ` 首个错误：${data.errors[0]}`)
      }
      queryClient.invalidateQueries()
    },
    onError: (err: Error) => setUploadMsg(`上传失败：${err.message}`),
  })

  const handleJsonUpload = () => {
    setUploadMsg('')
    try {
      const emails = JSON.parse(jsonText)
      if (!Array.isArray(emails)) throw new Error('JSON 必须是数组')
      uploadMut.mutate(emails)
    } catch (err: any) {
      setUploadMsg(`JSON 无效：${err.message}`)
    }
  }

  const saveMut = useMutation({
    mutationFn: updateAISettings,
    onSuccess: () => {
      setSaveMsg('AI 设置已保存。')
      queryClient.invalidateQueries({ queryKey: ['aiSettings'] })
    },
    onError: (err: Error) => {
      if (isAuthError(err)) {
        setSaveMsg('保存失败：登录状态已失效，请重新登录后再保存认证设置。')
        return
      }
      setSaveMsg(`保存失败：${err.message}`)
    },
  })

  const connectGmailMut = useMutation({
    mutationFn: fetchGmailAuthorizationUrl,
    onSuccess: ({ authorization_url }) => {
      window.location.href = authorization_url
    },
    onError: (err: Error) => setGmailMsg(`Gmail 授权失败：${err.message}`),
  })

  const refreshGmailMut = useMutation({
    mutationFn: refreshGmailToken,
    onSuccess: () => {
      setGmailMsg('Gmail Token 已刷新。')
      queryClient.invalidateQueries({ queryKey: ['gmailStatus'] })
    },
    onError: (err: Error) => setGmailMsg(`刷新失败：${err.message}`),
  })

  const disconnectGmailMut = useMutation({
    mutationFn: disconnectGmail,
    onSuccess: () => {
      setGmailMsg('Gmail 已断开连接。')
      queryClient.invalidateQueries({ queryKey: ['gmailStatus'] })
    },
    onError: (err: Error) => setGmailMsg(`断开连接失败：${err.message}`),
  })

  const syncGmailMut = useMutation({
    mutationFn: syncGmailInbox,
    onSuccess: (data) => {
      setGmailMsg(`同步完成：新增 ${data.new} 封，跳过 ${data.skipped} 封${data.errors.length ? `，${data.errors.length} 个错误` : ''}。`)
      queryClient.invalidateQueries()
    },
    onError: (err: Error) => setGmailMsg(`同步失败：${err.message}`),
  })

  const connectOutlookMut = useMutation({
    mutationFn: fetchOutlookAuthorizationUrl,
    onSuccess: ({ authorization_url }) => {
      window.location.href = authorization_url
    },
    onError: (err: Error) => setOutlookMsg(`Outlook 授权失败：${err.message}`),
  })

  const refreshOutlookMut = useMutation({
    mutationFn: refreshOutlookToken,
    onSuccess: () => {
      setOutlookMsg('Outlook Token 已刷新。')
      queryClient.invalidateQueries({ queryKey: ['outlookStatus'] })
    },
    onError: (err: Error) => setOutlookMsg(`刷新失败：${err.message}`),
  })

  const disconnectOutlookMut = useMutation({
    mutationFn: disconnectOutlook,
    onSuccess: () => {
      setOutlookMsg('Outlook 已断开连接。')
      queryClient.invalidateQueries({ queryKey: ['outlookStatus'] })
    },
    onError: (err: Error) => setOutlookMsg(`断开连接失败：${err.message}`),
  })

  const syncOutlookMut = useMutation({
    mutationFn: syncOutlookInbox,
    onSuccess: (data) => {
      setOutlookMsg(`同步完成：新增 ${data.new} 封，跳过 ${data.skipped} 封${data.errors.length ? `，${data.errors.length} 个错误` : ''}。`)
      queryClient.invalidateQueries()
    },
    onError: (err: Error) => setOutlookMsg(`同步失败：${err.message}`),
  })

  const update = (patch: Partial<AIProviderConfig>) => setConfig((c) => ({ ...c, ...patch }))

  return (
    <div>
      <div className="page-header"><h1>设置</h1></div>
      {settingsError && isAuthError(settingsError) && (
        <div style={{ ...noticeStyle(false), marginBottom: '1rem' }}>
          登录状态已失效。请重新登录后再保存 AI 设置、连接邮箱或导入邮箱数据。
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div id="ai-provider" className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Brain size={18} /> AI 提供方
          </h2>

          <label style={labelStyle}>提供方</label>
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
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>OpenAI 兼容接口</h3>
              <label style={labelStyle}>API 密钥</label>
              <input type="password" placeholder="sk-..." value={config.openai_api_key} onChange={(e) => update({ openai_api_key: e.target.value })} style={inputStyle} />
              <label style={labelStyle}>基础 URL</label>
              <input type="text" placeholder="https://api.openai.com/v1" value={config.openai_base_url} onChange={(e) => update({ openai_base_url: e.target.value })} style={inputStyle} />
              <label style={labelStyle}>模型</label>
              <input type="text" placeholder="gpt-4o" value={config.openai_model} onChange={(e) => update({ openai_model: e.target.value })} style={inputStyle} />
            </div>
          )}

          {config.provider === 'anthropic' && (
            <div style={panelStyle}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Anthropic</h3>
              <label style={labelStyle}>API 密钥</label>
              <input type="password" placeholder="sk-ant-..." value={config.anthropic_api_key} onChange={(e) => update({ anthropic_api_key: e.target.value })} style={inputStyle} />
              <label style={labelStyle}>基础 URL</label>
              <input type="text" placeholder="https://api.anthropic.com" value={config.anthropic_base_url} onChange={(e) => update({ anthropic_base_url: e.target.value })} style={inputStyle} />
              <label style={labelStyle}>模型</label>
              <input type="text" placeholder="claude-sonnet-4-5-20250929" value={config.anthropic_model} onChange={(e) => update({ anthropic_model: e.target.value })} style={inputStyle} />
            </div>
          )}

          {config.provider === 'mock' && (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
              本地规则模拟使用内置规则，不需要 API 密钥。
            </p>
          )}

          <button className="btn-primary" onClick={() => saveMut.mutate(config)} disabled={saveMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Save size={14} />
            {saveMut.isPending ? '正在保存...' : '保存 AI 设置'}
          </button>
          {saveMsg && <div style={noticeStyle(saveMsg.startsWith('AI 设置'))}>{saveMsg}</div>}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mail size={18} /> Gmail 集成
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            通过 OAuth 连接 Gmail。访问令牌和刷新令牌会加密后再存储。
          </p>
          <div style={{ marginBottom: '0.75rem', fontSize: '0.875rem' }}>
            状态：{gmailStatus?.connected ? `已连接${gmailStatus.email ? `：${gmailStatus.email}` : ''}` : '未连接'}
            {gmailStatus?.expires_at && (
              <span style={{ color: 'var(--color-text-muted)' }}> · 到期时间 {new Date(gmailStatus.expires_at).toLocaleString()}</span>
            )}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <button className="btn-primary" onClick={() => connectGmailMut.mutate()} disabled={connectGmailMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <ExternalLink size={14} />
              {gmailStatus?.connected ? '重新连接 Gmail' : '连接 Gmail'}
            </button>
            <button className="btn-secondary" onClick={() => refreshGmailMut.mutate()} disabled={!gmailStatus?.connected || refreshGmailMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <RefreshCw size={14} />
              刷新 Token
            </button>
            <button className="btn-secondary" onClick={() => syncGmailMut.mutate()} disabled={!gmailStatus?.connected || syncGmailMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Upload size={14} />
              同步收件箱
            </button>
            <button className="btn-secondary" onClick={() => disconnectGmailMut.mutate()} disabled={!gmailStatus?.connected || disconnectGmailMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Unlink size={14} />
              断开连接
            </button>
          </div>
          {gmailMsg && <div style={noticeStyle(!gmailMsg.includes('失败'))}>{gmailMsg}</div>}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mail size={18} /> Outlook 集成
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            通过 OAuth 连接 Outlook / Microsoft 365。访问令牌和刷新令牌会加密后再存储。
          </p>
          <div style={{ marginBottom: '0.75rem', fontSize: '0.875rem' }}>
            状态：{outlookStatus?.connected ? `已连接${outlookStatus.email ? `：${outlookStatus.email}` : ''}` : '未连接'}
            {outlookStatus?.expires_at && (
              <span style={{ color: 'var(--color-text-muted)' }}> · 到期时间 {new Date(outlookStatus.expires_at).toLocaleString()}</span>
            )}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <button className="btn-primary" onClick={() => connectOutlookMut.mutate()} disabled={connectOutlookMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <ExternalLink size={14} />
              {outlookStatus?.connected ? '重新连接 Outlook' : '连接 Outlook'}
            </button>
            <button className="btn-secondary" onClick={() => refreshOutlookMut.mutate()} disabled={!outlookStatus?.connected || refreshOutlookMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <RefreshCw size={14} />
              刷新 Token
            </button>
            <button className="btn-secondary" onClick={() => syncOutlookMut.mutate()} disabled={!outlookStatus?.connected || syncOutlookMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Upload size={14} />
              同步收件箱
            </button>
            <button className="btn-secondary" onClick={() => disconnectOutlookMut.mutate()} disabled={!outlookStatus?.connected || disconnectOutlookMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Unlink size={14} />
              断开连接
            </button>
          </div>
          {outlookMsg && <div style={noticeStyle(!outlookMsg.includes('失败'))}>{outlookMsg}</div>}
        </div>

        <div id="import" className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <FileJson size={18} /> JSON 上传导入
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            上传 JSON 文件，或粘贴邮件对象数组。每个对象需要包含：message_id、sender、recipients、subject、body、received_at。
          </p>
          <label style={labelStyle}>JSON 文件（选择后自动导入）</label>
          <input type="file" accept=".json" onChange={(e) => {
            const file = e.target.files?.[0]
            if (!file) return
            setUploadMsg('')
            const reader = new FileReader()
            reader.onload = (ev) => {
              try {
                const emails = JSON.parse(ev.target?.result as string)
                if (!Array.isArray(emails)) throw new Error('JSON 必须是数组')
                uploadMut.mutate(emails)
              } catch (err: any) {
                setUploadMsg(`JSON 无效：${err.message}`)
              }
            }
            reader.readAsText(file)
          }}
          style={{ ...inputStyle, border: 'none', padding: '0.375rem 0' }} />
          <label style={labelStyle}>或粘贴 JSON</label>
          <textarea
            rows={5}
            placeholder='[{"message_id":"msg-001","sender":"a@b.com","recipients":"me@b.com","subject":"Hello","body":"...","received_at":"2026-01-01T00:00:00"}]'
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            style={{ ...inputStyle, fontFamily: 'monospace', fontSize: '0.75rem' }}
          />
          {jsonText.trim() && (
            <button className="btn-primary" onClick={handleJsonUpload} disabled={uploadMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Upload size={14} />
              {uploadMut.isPending ? '正在上传...' : '上传粘贴的 JSON'}
            </button>
          )}
          {uploadMsg && <div style={noticeStyle(uploadMsg.startsWith('已导入'))}>{uploadMsg}</div>}
        </div>

        <div id="mock-import" className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Upload size={18} /> 示例数据导入
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            导入内置示例邮件数据，用于本地开发和演示。
          </p>
          <button className="btn-primary" onClick={() => importMut.mutate()} disabled={importMut.isPending}>
            {importMut.isPending ? '正在导入...' : '导入示例邮件'}
          </button>
          {importMsg && <div style={noticeStyle(importMsg.startsWith('已导入'))}>{importMsg}</div>}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Database size={18} /> 数据库
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            默认使用 PostgreSQL。先运行 <code>docker compose up -d db</code> 启动数据库，再执行后端迁移。
          </p>
        </div>
      </div>
    </div>
  )
}
