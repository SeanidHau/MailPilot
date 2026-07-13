import { useState } from 'react'

interface Props {
  content: string
  recipient?: string | null
  subject?: string | null
  onSave: (content: string, fields?: { recipient: string; subject: string }) => void
  onCancel?: () => void
}

export function DraftEditor({ content: initial, recipient: initialRecipient, subject: initialSubject, onSave, onCancel }: Props) {
  const [content, setContent] = useState(initial)
  const [recipient, setRecipient] = useState(initialRecipient || '')
  const [subject, setSubject] = useState(initialSubject || '')
  const showFields = initialRecipient !== undefined || initialSubject !== undefined
  return (
    <div>
      {showFields && (
        <div style={{ display: 'grid', gap: '0.625rem', marginBottom: '0.75rem' }}>
          <label style={{ display: 'grid', gap: '0.25rem' }}>
            <span>收件人</span>
            <input value={recipient} onChange={(e) => setRecipient(e.target.value)} required />
          </label>
          <label style={{ display: 'grid', gap: '0.25rem' }}>
            <span>主题</span>
            <input value={subject} onChange={(e) => setSubject(e.target.value)} required />
          </label>
        </div>
      )}
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={10}
        style={{ width: '100%', resize: 'vertical', fontFamily: 'monospace', fontSize: '0.875rem' }}
      />
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
        <button className="btn-primary" onClick={() => onSave(content, showFields ? { recipient: recipient.trim(), subject: subject.trim() } : undefined)}>保存</button>
        {onCancel && <button className="btn-secondary" onClick={onCancel}>取消</button>}
      </div>
    </div>
  )
}
