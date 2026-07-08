import { useState, useEffect } from 'react'
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
import { importEmails } from '../api/emails'
import { fetchAISettings, updateAISettings } from '../api/settings'
import type { AIProviderConfig, AIProvider } from '../types/settings'
import { Upload, Database, Brain, Mail, Save } from 'lucide-react'

const PROVIDERS: { value: AIProvider; label: string }[] = [
  { value: 'mock', label: 'Mock（基于规则）' },
  { value: 'openai', label: 'OpenAI 兼容' },
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

export function SettingsPage() {
  const queryClient = useQueryClient()
  const [importMsg, setImportMsg] = useState('')
  const [saveMsg, setSaveMsg] = useState('')
  const [config, setConfig] = useState<AIProviderConfig>(defaultConfig)

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ['aiSettings'],
    queryFn: fetchAISettings,
  })

  useEffect(() => {
    if (savedConfig) setConfig(savedConfig)
  }, [savedConfig])

  const importMut = useMutation({
    mutationFn: importEmails,
    onSuccess: (data) => {
      setImportMsg(`成功导入 ${data.imported} 封邮件。`)
      queryClient.invalidateQueries()
    },
    onError: (err: Error) => setImportMsg(`导入失败：${err.message}`),
  })

  const saveMut = useMutation({
    mutationFn: updateAISettings,
    onSuccess: () => {
      setSaveMsg('AI 配置已保存，下次 AI 请求生效。')
      queryClient.invalidateQueries({ queryKey: ['aiSettings'] })
    },
    onError: (err: Error) => setSaveMsg(`保存失败：${err.message}`),
  })

  const update = (patch: Partial<AIProviderConfig>) => setConfig((c) => ({ ...c, ...patch }))

  return (
    <div>
      <div className="page-header"><h1>设置</h1></div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* AI Provider Config */}
        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Brain size={18} /> AI 提供商配置
          </h2>

          {/* Provider selector */}
          <label style={labelStyle}>提供商</label>
          <select
            value={config.provider}
            onChange={(e) => update({ provider: e.target.value as AIProvider })}
            style={inputStyle}
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>

          {/* OpenAI fields */}
          {config.provider === 'openai' && (
            <div style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: 'var(--radius)', marginBottom: '0.5rem' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>OpenAI 兼容配置</h3>
              <label style={labelStyle}>API Key</label>
              <input
                type="password"
                placeholder="sk-..."
                value={config.openai_api_key}
                onChange={(e) => update({ openai_api_key: e.target.value })}
                style={inputStyle}
              />
              <label style={labelStyle}>Base URL</label>
              <input
                type="text"
                placeholder="https://api.openai.com/v1"
                value={config.openai_base_url}
                onChange={(e) => update({ openai_base_url: e.target.value })}
                style={inputStyle}
              />
              <label style={labelStyle}>模型</label>
              <input
                type="text"
                placeholder="gpt-4o"
                value={config.openai_model}
                onChange={(e) => update({ openai_model: e.target.value })}
                style={inputStyle}
              />
              <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                支持任意 OpenAI 兼容 API。
              </p>
            </div>
          )}

          {/* Anthropic fields */}
          {config.provider === 'anthropic' && (
            <div style={{ padding: '0.75rem', background: '#f8fafc', borderRadius: 'var(--radius)', marginBottom: '0.5rem' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>Anthropic 配置</h3>
              <label style={labelStyle}>API Key</label>
              <input
                type="password"
                placeholder="sk-ant-..."
                value={config.anthropic_api_key}
                onChange={(e) => update({ anthropic_api_key: e.target.value })}
                style={inputStyle}
              />
              <label style={labelStyle}>Base URL</label>
              <input
                type="text"
                placeholder="https://api.anthropic.com"
                value={config.anthropic_base_url}
                onChange={(e) => update({ anthropic_base_url: e.target.value })}
                style={inputStyle}
              />
              <label style={labelStyle}>模型</label>
              <input
                type="text"
                placeholder="claude-sonnet-4-5-20250929"
                value={config.anthropic_model}
                onChange={(e) => update({ anthropic_model: e.target.value })}
                style={inputStyle}
              />
            </div>
          )}

          {/* Mock info */}
          {config.provider === 'mock' && (
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
              Mock 提供商使用关键词和正则匹配，无需 API Key，无需联网。
            </p>
          )}

          <button
            className="btn-primary"
            onClick={() => saveMut.mutate(config)}
            disabled={saveMut.isPending}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <Save size={14} />
            {saveMut.isPending ? '正在保存...' : '保存 AI 配置'}
          </button>
          {saveMsg && (
            <div style={{
              marginTop: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius)',
              background: saveMsg.startsWith('AI') ? '#f0fdf4' : '#fef2f2',
              color: saveMsg.startsWith('AI') ? '#166534' : '#991b1b',
              fontSize: '0.875rem',
            }}>
              {saveMsg}
            </div>
          )}
        </div>

        {/* Mock Import */}
        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Upload size={18} /> 模拟数据导入
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.75rem' }}>
            从本地 mock JSON 文件导入示例邮件数据。重复邮件（按 Message-ID 去重）将被跳过。
          </p>
          <button className="btn-primary" onClick={() => importMut.mutate()} disabled={importMut.isPending}>
            {importMut.isPending ? '正在导入...' : '导入模拟邮件'}
          </button>
          {importMsg && (
            <div style={{
              marginTop: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius)',
              background: importMsg.startsWith('成功') ? '#f0fdf4' : '#fef2f2',
              color: importMsg.startsWith('成功') ? '#166534' : '#991b1b',
              fontSize: '0.875rem',
            }}>
              {importMsg}
            </div>
          )}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Mail size={18} /> 邮箱集成
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            Gmail 和 Outlook 集成计划在后续版本中实现。当前仅支持通过 mock JSON 数据导入作为邮件来源。
          </p>
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Database size={18} /> 数据库
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            默认使用 PostgreSQL。通过 <code>docker compose up -d db</code> 启动数据库，<code>.env</code> 中配置 <code>DATABASE_URL</code>。
          </p>
        </div>
      </div>
    </div>
  )
}
