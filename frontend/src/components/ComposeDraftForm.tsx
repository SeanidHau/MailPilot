import { useState } from 'react'

interface Props {
  onSave: (values: { recipient: string; subject: string; content: string }) => void
  onCancel: () => void
  isSaving?: boolean
}

export function ComposeDraftForm({ onSave, onCancel, isSaving = false }: Props) {
  const [recipient, setRecipient] = useState('')
  const [subject, setSubject] = useState('')
  const [content, setContent] = useState('')

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    onSave({ recipient: recipient.trim(), subject: subject.trim(), content })
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '0.75rem' }}>
      <div className="compose-form-header">
        <div>
          <h2 style={{ fontSize: '1rem' }}>写邮件</h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>新建一封邮件草稿，确认后再发送。</p>
        </div>
      </div>
      <label style={{ display: 'grid', gap: '0.25rem' }}>
        <span>收件人</span>
        <input
          type="email"
          value={recipient}
          onChange={(event) => setRecipient(event.target.value)}
          placeholder="name@example.com"
          required
        />
      </label>
      <label style={{ display: 'grid', gap: '0.25rem' }}>
        <span>主题</span>
        <input
          value={subject}
          onChange={(event) => setSubject(event.target.value)}
          required
        />
      </label>
      <label style={{ display: 'grid', gap: '0.25rem' }}>
        <span>正文</span>
        <textarea
          value={content}
          onChange={(event) => setContent(event.target.value)}
          rows={10}
          style={{ width: '100%', resize: 'vertical' }}
          required
        />
      </label>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <button className="btn-primary" type="submit" disabled={isSaving}>
          {isSaving ? '保存中...' : '保存草稿'}
        </button>
        <button className="btn-secondary" type="button" onClick={onCancel} disabled={isSaving}>取消</button>
      </div>
    </form>
  )
}
