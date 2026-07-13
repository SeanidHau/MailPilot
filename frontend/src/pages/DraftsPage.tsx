import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { createDraft, fetchDrafts, patchDraft, sendDraft, deleteDraft, type MailboxProvider } from '../api/drafts'
import { fetchGmailStatus, fetchOutlookStatus } from '../api/settings'
import { DraftEditor } from '../components/DraftEditor'
import { ComposeDraftForm } from '../components/ComposeDraftForm'
import { Mail, Send, Trash2 } from 'lucide-react'
import type { DraftResponse } from '../types/draft'

const TONE_LABELS: Record<string, string> = { formal: '正式', brief: '简洁', polite_decline: '礼貌拒绝', ask_info: '询问信息' }
const STATUS_LABELS: Record<string, string> = {
  draft: '草稿', saved: '已保存', ready_to_send: '待发送', sent: '已发送', send_failed: '发送失败', deleted: '已删除',
}

export function DraftsPage() {
  const queryClient = useQueryClient()
  const [editingId, setEditingId] = useState<number | null>(null)
  const [sendConfirmId, setSendConfirmId] = useState<number | null>(null)
  const [sendProvider, setSendProvider] = useState<MailboxProvider | ''>('')
  const [showComposer, setShowComposer] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['drafts'],
    queryFn: () => fetchDrafts(),
  })

  const { data: gmailStatus } = useQuery({
    queryKey: ['gmail-status'],
    queryFn: fetchGmailStatus,
  })

  const { data: outlookStatus } = useQuery({
    queryKey: ['outlook-status'],
    queryFn: fetchOutlookStatus,
  })

  const saveMut = useMutation({
    mutationFn: ({ id, content, fields }: { id: number; content: string; fields?: { recipient: string; subject: string } }) =>
      patchDraft(id, { content, status: 'saved', ...fields }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      setEditingId(null)
    },
  })

  const createMut = useMutation({
    mutationFn: createDraft,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      setShowComposer(false)
    },
  })

  const sendMut = useMutation({
    mutationFn: ({ id, provider }: { id: number; provider: MailboxProvider }) => sendDraft(id, provider),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      setSendConfirmId(null)
      setSendProvider('')
    },
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteDraft(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['drafts'] }),
  })

  const handleDelete = (id: number) => {
    if (window.confirm('确定删除这封草稿吗？删除后将无法在草稿列表中恢复。')) {
      deleteMut.mutate(id)
    }
  }

  if (isLoading) return <div className="empty-state">加载中...</div>

  const drafts = data?.items || []
  const connectedProviders: MailboxProvider[] = [
    ...(gmailStatus?.connected ? ['gmail' as const] : []),
    ...(outlookStatus?.connected ? ['outlook' as const] : []),
  ]

  const openSendConfirmation = (id: number) => {
    setSendConfirmId(id)
    setSendProvider(connectedProviders.length === 1 ? connectedProviders[0] : '')
    sendMut.reset()
  }

  return (
    <div>
      <div className="page-header">
        <h1>草稿</h1>
        <button className="btn-primary" onClick={() => setShowComposer(true)}>
          <Mail size={16} />
          写邮件
        </button>
      </div>

      {showComposer && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <ComposeDraftForm
            onSave={(values) => createMut.mutate(values)}
            onCancel={() => { setShowComposer(false); createMut.reset() }}
            isSaving={createMut.isPending}
          />
          {createMut.isError && <p style={{ color: 'var(--color-danger)' }}>{(createMut.error as Error).message}</p>}
        </div>
      )}

      {drafts.length === 0 ? (
        <div className="empty-state">暂无草稿。请在邮件详情页生成草稿。</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {drafts.map((draft: DraftResponse) => (
            <div key={draft.id} className="card">
              <div className="draft-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <div>
                  <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>
                    {draft.subject || `回复草稿 #${draft.id}`}
                  </span>
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
                  {draft.recipient && (
                    <div style={{ marginTop: '0.25rem', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                      收件人：{draft.recipient}
                    </div>
                  )}
                  {(draft.send_error || (sendMut.isError && sendMut.variables?.id === draft.id)) && (
                    <span style={{ marginLeft: '0.5rem', fontSize: '0.75rem', color: 'var(--color-danger)' }}>
                      {draft.send_error || (sendMut.error as Error)?.message || '发送失败'}
                    </span>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  {draft.status !== 'sent' && draft.status !== 'deleted' && (
                    <>
                      <button className="btn-secondary btn-sm" onClick={() => setEditingId(editingId === draft.id ? null : draft.id)}>
                        {editingId === draft.id ? '取消' : '编辑'}
                      </button>
                      <button
                        className="btn-primary btn-sm"
                        onClick={() => openSendConfirmation(draft.id)}
                        disabled={sendMut.isPending}
                        style={{ display: 'flex', alignItems: 'center', gap: 4 }}
                      >
                        <Send size={12} />
                        发送
                      </button>
                      <button
                        className="btn-danger btn-sm"
                        onClick={() => handleDelete(draft.id)}
                        disabled={deleteMut.isPending && deleteMut.variables === draft.id}
                        title="删除草稿"
                        aria-label={`删除草稿 ${draft.id}`}
                      >
                        <Trash2 size={14} />
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Send confirmation */}
              {sendConfirmId === draft.id && (
                <div style={{
                  marginBottom: '0.5rem', padding: '0.75rem',
                  background: '#fef3c7', borderRadius: 'var(--radius)', fontSize: '0.875rem',
                }}>
                  <p style={{ marginBottom: '0.5rem' }}>
                    确认通过已连接的邮箱发送此邮件？草稿内容将作为邮件正文发送。
                  </p>
                  {connectedProviders.length > 1 ? (
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                      <span>发送账号</span>
                      <select
                        value={sendProvider}
                        onChange={(event) => setSendProvider(event.target.value as MailboxProvider)}
                        disabled={sendMut.isPending}
                      >
                        <option value="">请选择邮箱</option>
                        <option value="gmail">Gmail{gmailStatus?.email ? ` (${gmailStatus.email})` : ''}</option>
                        <option value="outlook">Outlook{outlookStatus?.email ? ` (${outlookStatus.email})` : ''}</option>
                      </select>
                    </label>
                  ) : connectedProviders.length === 1 ? (
                    <p style={{ marginBottom: '0.75rem', color: 'var(--color-text-muted)' }}>
                      发送账号：{connectedProviders[0] === 'gmail' ? 'Gmail' : 'Outlook'}
                    </p>
                  ) : (
                    <p style={{ marginBottom: '0.75rem', color: 'var(--color-danger)' }}>
                      请先在设置中连接 Gmail 或 Outlook。
                    </p>
                  )}
                  {sendMut.isError && sendMut.variables?.id === draft.id && (
                    <p style={{ marginBottom: '0.75rem', color: 'var(--color-danger)' }}>
                      {(sendMut.error as Error)?.message || '发送失败，请稍后重试。'}
                    </p>
                  )}
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      className="btn-primary btn-sm"
                      onClick={() => sendProvider && sendMut.mutate({ id: draft.id, provider: sendProvider })}
                      disabled={sendMut.isPending || !sendProvider}
                    >
                      {sendMut.isPending ? '发送中...' : '确认发送'}
                    </button>
                    <button className="btn-secondary btn-sm" onClick={() => { setSendConfirmId(null); setSendProvider(''); sendMut.reset() }}>
                      取消
                    </button>
                  </div>
                </div>
              )}

              {editingId === draft.id ? (
                <DraftEditor
                  content={draft.content}
                  recipient={draft.email_id === null ? draft.recipient : undefined}
                  subject={draft.email_id === null ? draft.subject : undefined}
                  onSave={(content, fields) => saveMut.mutate({ id: draft.id, content, fields })}
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
