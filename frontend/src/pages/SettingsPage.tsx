import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Brain, Edit3, ExternalLink, FileJson, Mail, RefreshCw, Save, Unlink, Upload } from 'lucide-react'
import { uploadEmails } from '../api/emails'
import { fetchJob } from '../api/jobs'
import { forgetAIJob, rememberAIJob } from '../components/AIJobMonitor'
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
  { value: 'mock', label: '内置规则引擎' },
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

const warningStyle: React.CSSProperties = {
  marginTop: '0.75rem',
  padding: '0.625rem 0.75rem',
  borderRadius: 'var(--radius)',
  background: '#fff7ed',
  color: '#9a3412',
  fontSize: '0.875rem',
  lineHeight: 1.5,
}

function isAuthError(err: Error) {
  const message = err.message.toLowerCase()
  return message.includes('not authenticated') || message.includes('unauthorized') || message.includes('401')
}

export function SettingsPage() {
  const queryClient = useQueryClient()
  const [uploadMsg, setUploadMsg] = useState('')
  const [jsonText, setJsonText] = useState('')
  const [saveMsg, setSaveMsg] = useState('')
  const [gmailMsg, setGmailMsg] = useState('')
  const [outlookMsg, setOutlookMsg] = useState('')
  const [config, setConfig] = useState<AIProviderConfig>(defaultConfig)
  const [isAiEditing, setIsAiEditing] = useState(true)
  const [uploadJobId, setUploadJobId] = useState<number | null>(null)
  const [aiJobId, setAiJobId] = useState<number | null>(null)
  const [gmailJobId, setGmailJobId] = useState<number | null>(null)
  const [outlookJobId, setOutlookJobId] = useState<number | null>(null)

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

  const uploadJobQuery = useQuery({
    queryKey: ['job', uploadJobId],
    queryFn: () => fetchJob(uploadJobId!),
    enabled: uploadJobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed' ? false : 1000
    },
  })

  const aiJobQuery = useQuery({
    queryKey: ['job', aiJobId],
    queryFn: () => fetchJob(aiJobId!),
    enabled: aiJobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed' ? false : 1000
    },
  })

  const gmailJobQuery = useQuery({
    queryKey: ['job', gmailJobId],
    queryFn: () => fetchJob(gmailJobId!),
    enabled: gmailJobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed' ? false : 1000
    },
  })

  const outlookJobQuery = useQuery({
    queryKey: ['job', outlookJobId],
    queryFn: () => fetchJob(outlookJobId!),
    enabled: outlookJobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'completed' || status === 'failed' ? false : 1000
    },
  })

  useEffect(() => {
    if (savedConfig) {
      setConfig(savedConfig)
      setIsAiEditing(false)
    }
  }, [savedConfig])

  useEffect(() => {
    const job = uploadJobQuery.data
    if (!job || job.status === 'queued' || job.status === 'running') return
    if (job.status === 'completed') {
      const result = job.result || {}
      setUploadMsg(`导入完成：新增 ${result.imported ?? 0} 条，跳过 ${result.skipped ?? 0} 条${result.errors?.length ? `，${result.errors.length} 个错误` : ''}。`)
      if (result.errors?.length) setUploadMsg((message) => `${message} 首个错误：${result.errors[0]}`)
      queryClient.invalidateQueries()
    } else {
      setUploadMsg(`导入失败：${job.error || '后台任务执行失败'}`)
    }
    setUploadJobId(null)
  }, [uploadJobQuery.data, queryClient])

  useEffect(() => {
    const job = aiJobQuery.data
    if (!job) return
    if (job.status === 'queued' || job.status === 'running' || job.status === 'pause_requested') {
      const progress = job.result || {}
      if (typeof progress.total === 'number') {
        setSaveMsg(job.status === 'pause_requested'
          ? `AI 设置已保存，正在暂停处理：${progress.processed ?? 0}/${progress.total}`
          : `AI 设置已保存，正在处理邮件：${progress.processed ?? 0}/${progress.total}`)
      }
      return
    }
    if (job.status === 'completed') {
      const result = job.result || {}
      setSaveMsg(`AI 设置已保存，邮件处理完成：处理 ${result.processed ?? 0} 封${result.failed ? `，失败 ${result.failed} 封` : ''}。`)
    } else if (job.status === 'paused') {
      const result = job.result || {}
      setSaveMsg(`AI 设置已保存，邮件处理已暂停：已处理 ${result.processed ?? 0} 封。`)
    } else {
      setSaveMsg(`AI 设置已保存，但邮件处理失败：${job.error || '后台任务执行失败'}`)
    }
    forgetAIJob(job.id)
    setAiJobId(null)
  }, [aiJobQuery.data])

  useEffect(() => {
    const job = gmailJobQuery.data
    if (!job || job.status === 'queued' || job.status === 'running') return
    if (job.status === 'completed') {
      const result = job.result || {}
      if (typeof result.ai_job_id === 'number') rememberAIJob(result.ai_job_id)
      setGmailMsg(`同步完成：新增 ${result.new ?? 0} 封，跳过 ${result.skipped ?? 0} 封${result.ai_job_id ? '，AI 处理已转入后台' : ''}${result.errors?.length ? `，${result.errors.length} 个错误` : ''}。`)
      queryClient.invalidateQueries()
    } else {
      setGmailMsg(`同步失败：${job.error || '后台任务执行失败'}`)
    }
    setGmailJobId(null)
  }, [gmailJobQuery.data, queryClient])

  useEffect(() => {
    const job = outlookJobQuery.data
    if (!job || job.status === 'queued' || job.status === 'running') return
    if (job.status === 'completed') {
      const result = job.result || {}
      if (typeof result.ai_job_id === 'number') rememberAIJob(result.ai_job_id)
      setOutlookMsg(`同步完成：新增 ${result.new ?? 0} 封，跳过 ${result.skipped ?? 0} 封${result.ai_job_id ? '，AI 处理已转入后台' : ''}${result.errors?.length ? `，${result.errors.length} 个错误` : ''}。`)
      queryClient.invalidateQueries()
    } else {
      setOutlookMsg(`同步失败：${job.error || '后台任务执行失败'}`)
    }
    setOutlookJobId(null)
  }, [outlookJobQuery.data, queryClient])

  const uploadMut = useMutation({
    mutationFn: (emails: Record<string, any>[]) => uploadEmails(emails),
    onSuccess: (data) => {
      setUploadJobId(data.job_id)
      setUploadMsg('导入任务已提交，正在后台处理...')
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
    onSuccess: (data) => {
      rememberAIJob(data.job_id)
      setAiJobId(data.job_id)
      setSaveMsg('AI 设置已保存，正在后台处理未完成的邮件...')
      setIsAiEditing(false)
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
      setGmailMsg('Gmail 令牌已刷新。')
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
      setGmailJobId(data.job_id)
      setGmailMsg('同步任务已提交，正在后台读取收件箱...')
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
      setOutlookMsg('Outlook 令牌已刷新。')
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
      setOutlookJobId(data.job_id)
      setOutlookMsg('同步任务已提交，正在后台读取收件箱...')
    },
    onError: (err: Error) => setOutlookMsg(`同步失败：${err.message}`),
  })

  const update = (patch: Partial<AIProviderConfig>) => setConfig((c) => ({ ...c, ...patch }))
  const gmailStatusLoaded = Boolean(gmailStatus)
  const outlookStatusLoaded = Boolean(outlookStatus)
  const gmailConfigured = gmailStatus?.configured ?? false
  const outlookConfigured = outlookStatus?.configured ?? false
  const gmailConnectDisabled = !gmailConfigured || connectGmailMut.isPending
  const outlookConnectDisabled = !outlookConfigured || connectOutlookMut.isPending

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
            disabled={!isAiEditing}
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
              <input type="password" placeholder="sk-..." value={config.openai_api_key} onChange={(e) => update({ openai_api_key: e.target.value })} disabled={!isAiEditing} style={inputStyle} />
              <label style={labelStyle}>基础 URL</label>
              <input type="text" placeholder="https://api.openai.com/v1" value={config.openai_base_url} onChange={(e) => update({ openai_base_url: e.target.value })} disabled={!isAiEditing} style={inputStyle} />
              <label style={labelStyle}>模型</label>
              <input type="text" placeholder="gpt-4o" value={config.openai_model} onChange={(e) => update({ openai_model: e.target.value })} disabled={!isAiEditing} style={inputStyle} />
            </div>
          )}

          {config.provider === 'anthropic' && (
            <div style={panelStyle}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Anthropic</h3>
              <label style={labelStyle}>API 密钥</label>
              <input type="password" placeholder="sk-ant-..." value={config.anthropic_api_key} onChange={(e) => update({ anthropic_api_key: e.target.value })} disabled={!isAiEditing} style={inputStyle} />
              <label style={labelStyle}>基础 URL</label>
              <input type="text" placeholder="https://api.anthropic.com" value={config.anthropic_base_url} onChange={(e) => update({ anthropic_base_url: e.target.value })} disabled={!isAiEditing} style={inputStyle} />
              <label style={labelStyle}>模型</label>
              <input type="text" placeholder="claude-sonnet-4-5-20250929" value={config.anthropic_model} onChange={(e) => update({ anthropic_model: e.target.value })} disabled={!isAiEditing} style={inputStyle} />
            </div>
          )}

          {config.provider === 'mock' && (
            <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
              内置规则引擎不依赖外部 API，适合在未配置大模型服务时保持分类、摘要和提醒能力可用。
            </p>
          )}

          {isAiEditing ? (
            <button className="btn-primary" onClick={() => saveMut.mutate(config)} disabled={saveMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Save size={14} />
              {saveMut.isPending ? '正在保存...' : '保存 AI 设置'}
            </button>
          ) : (
            <button className="btn-secondary" onClick={() => setIsAiEditing(true)} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Edit3 size={14} />
              修改
            </button>
          )}
          {saveMsg && <div style={noticeStyle(saveMsg.startsWith('AI 设置'))}>{saveMsg}</div>}
        </div>

        <div id="mailboxes" className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mail size={18} /> Gmail 集成
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            连接 Gmail 后可同步收件箱并发送草稿。访问令牌和刷新令牌会加密后再存储。
          </p>
          <div style={{ marginBottom: '0.75rem', fontSize: '0.875rem' }}>
            状态：{gmailStatus?.connected ? `已连接${gmailStatus.email ? `：${gmailStatus.email}` : ''}` : '未连接'}
            {gmailStatusLoaded && !gmailConfigured && <span style={{ color: 'var(--color-warning)' }}> · 连接服务未启用</span>}
            {gmailStatus?.expires_at && (
              <span style={{ color: 'var(--color-text-muted)' }}> · 到期时间 {new Date(gmailStatus.expires_at).toLocaleString()}</span>
            )}
          </div>
          {gmailStatusLoaded && !gmailConfigured && (
            <div style={warningStyle}>
              需要先在后端配置 Gmail OAuth 客户端：GMAIL_CLIENT_ID、GMAIL_CLIENT_SECRET 和 GMAIL_REDIRECT_URI。
            </div>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <button className="btn-primary" onClick={() => connectGmailMut.mutate()} disabled={gmailConnectDisabled} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <ExternalLink size={14} />
              {gmailStatus?.connected ? '重新连接 Gmail' : '连接 Gmail'}
            </button>
            <button className="btn-secondary" onClick={() => refreshGmailMut.mutate()} disabled={!gmailConfigured || !gmailStatus?.connected || refreshGmailMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <RefreshCw size={14} />
              刷新令牌
            </button>
            <button className="btn-secondary" onClick={() => syncGmailMut.mutate()} disabled={!gmailConfigured || !gmailStatus?.connected || syncGmailMut.isPending || gmailJobId !== null} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
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
            连接 Outlook / Microsoft 365 后可同步收件箱并发送草稿。访问令牌和刷新令牌会加密后再存储。
          </p>
          <div style={{ marginBottom: '0.75rem', fontSize: '0.875rem' }}>
            状态：{outlookStatus?.connected ? `已连接${outlookStatus.email ? `：${outlookStatus.email}` : ''}` : '未连接'}
            {outlookStatusLoaded && !outlookConfigured && <span style={{ color: 'var(--color-warning)' }}> · 连接服务未启用</span>}
            {outlookStatus?.expires_at && (
              <span style={{ color: 'var(--color-text-muted)' }}> · 到期时间 {new Date(outlookStatus.expires_at).toLocaleString()}</span>
            )}
          </div>
          {outlookStatusLoaded && !outlookConfigured && (
            <div style={warningStyle}>
              需要先在后端配置 Microsoft Graph OAuth 客户端：OUTLOOK_CLIENT_ID、OUTLOOK_CLIENT_SECRET 和 OUTLOOK_REDIRECT_URI。
            </div>
          )}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <button className="btn-primary" onClick={() => connectOutlookMut.mutate()} disabled={outlookConnectDisabled} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <ExternalLink size={14} />
              {outlookStatus?.connected ? '重新连接 Outlook' : '连接 Outlook'}
            </button>
            <button className="btn-secondary" onClick={() => refreshOutlookMut.mutate()} disabled={!outlookConfigured || !outlookStatus?.connected || refreshOutlookMut.isPending} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <RefreshCw size={14} />
              刷新令牌
            </button>
            <button className="btn-secondary" onClick={() => syncOutlookMut.mutate()} disabled={!outlookConfigured || !outlookStatus?.connected || syncOutlookMut.isPending || outlookJobId !== null} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
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
            <FileJson size={18} /> 批量导入
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            上传邮件归档 JSON 文件，或粘贴邮件对象数组。每条记录需要包含 message_id、sender、recipients、subject、body、received_at。
          </p>
          <label style={labelStyle}>邮件归档文件</label>
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
          disabled={uploadMut.isPending || uploadJobId !== null}
          style={{ ...inputStyle, border: 'none', padding: '0.375rem 0' }} />
          <label style={labelStyle}>粘贴邮件数据</label>
          <textarea
            rows={5}
            placeholder="粘贴邮件对象数组"
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            style={{ ...inputStyle, fontFamily: 'monospace', fontSize: '0.75rem' }}
          />
          {jsonText.trim() && (
            <button className="btn-primary" onClick={handleJsonUpload} disabled={uploadMut.isPending || uploadJobId !== null} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Upload size={14} />
              {uploadMut.isPending ? '正在导入...' : '导入粘贴数据'}
            </button>
          )}
          {uploadMsg && <div style={noticeStyle(uploadMsg.startsWith('已导入'))}>{uploadMsg}</div>}
        </div>
      </div>
    </div>
  )
}
