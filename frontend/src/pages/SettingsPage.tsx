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
      setMessage(`成功导入 ${data.imported} 封邮件。`)
      queryClient.invalidateQueries()
    },
    onError: (err: Error) => setMessage(`导入失败：${err.message}`),
  })

  return (
    <div>
      <div className="page-header"><h1>设置</h1></div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
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
          {message && (
            <div style={{
              marginTop: '0.75rem', padding: '0.5rem 0.75rem', borderRadius: 'var(--radius)',
              background: message.startsWith('成功') ? '#f0fdf4' : '#fef2f2',
              color: message.startsWith('成功') ? '#166534' : '#991b1b',
              fontSize: '0.875rem',
            }}>
              {message}
            </div>
          )}
        </div>

        <div className="card">
          <h2 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Brain size={18} /> AI 提供商
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            当前提供商：<strong>Mock（基于规则）</strong>。Mock AI 提供商使用关键词和正则匹配进行邮件分类、摘要生成、草稿生成和提醒提取。后续版本将支持接入真实大模型 API。
          </p>
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
            演示环境默认使用 SQLite（本地文件）。生产环境请切换到 PostgreSQL，修改 <code>.env</code> 中的 <code>DATABASE_URL</code> 并运行 <code>docker compose up -d db</code>。
          </p>
        </div>
      </div>
    </div>
  )
}
