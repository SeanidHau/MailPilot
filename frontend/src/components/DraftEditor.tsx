import { useState } from 'react'

interface Props {
  content: string
  onSave: (content: string) => void
  onCancel?: () => void
}

export function DraftEditor({ content: initial, onSave, onCancel }: Props) {
  const [content, setContent] = useState(initial)
  return (
    <div>
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={10}
        style={{ width: '100%', resize: 'vertical', fontFamily: 'monospace', fontSize: '0.875rem' }}
      />
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
        <button className="btn-primary" onClick={() => onSave(content)}>保存</button>
        {onCancel && <button className="btn-secondary" onClick={onCancel}>取消</button>}
      </div>
    </div>
  )
}
