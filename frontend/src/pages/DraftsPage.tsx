import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchDrafts, patchDraft } from '../api/drafts'
import { DraftEditor } from '../components/DraftEditor'

const TONE_LABELS: Record<string, string> = { formal: '正式', brief: '简洁', polite_decline: '礼貌拒绝', ask_info: '询问信息' }
const STATUS_LABELS: Record<string, string> = { draft: '草稿', saved: '已保存' }

export function DraftsPage() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => fetchDrafts(),
  })

  const saveMut = useMutation({
    mutationFn: ({ id, content }: { id: number; content: string }) => patchDraft(id, { content, status: 'saved' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      setEditingId(null)
    },
  })

  if (isLoading) return <div className="empty-state">加载中...</div>

  const drafts = data?.items || []

  return (
    <div>
      <div className="page-header"><h1>草稿</h1></div>

      {drafts.length === 0 ? (
        <div className="empty-state">暂无草稿。请在邮件详情页生成草稿。</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {drafts.map((draft: any) => (
            <div key={draft.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div>
                  <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>草稿 #{draft.id}</span>
                  <span style={{
                    marginLeft: '0.75rem', fontSize: '0.75rem', padding: '0.125rem 0.5rem', borderRadius: 9999,
                    background: draft.tone === 'formal' ? '#dbeafe' : '#fef3c7',
                    color: draft.tone === 'formal' ? '#1d4ed8' : '#92400e',
                  }}>
                    {TONE_LABELS[draft.tone] || draft.tone}
                  </span>
                  <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    {STATUS_LABELS[draft.status] || draft.status}
                  </span>
                </div>
                <button className="btn-secondary btn-sm" onClick={() => setEditingId(editingId === draft.id ? null : draft.id)}>
                  {editingId === draft.id ? '取消' : '编辑'}
                </button>
              </div>
              {editingId === draft.id ? (
                <DraftEditor
                  content={draft.content}
                  onSave={(content) => saveMut.mutate({ id: draft.id, content })}
                  onCancel={() => setEditingId(null)}
                />
              ) : (
                <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                  {draft.content.slice(0, 300)}{draft.content.length > 300 ? '...' : ''}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
