import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { bulkUpdateReminders, fetchReminders, patchReminder, deleteReminder, type BulkReminderAction } from '../api/reminders'
import { ReminderList } from '../components/ReminderList'
import { useEffect, useState } from 'react'
import { CheckCheck, Trash2 } from 'lucide-react'

export function RemindersPage() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState('')
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [bulkMessage, setBulkMessage] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['reminders', filter],
    queryFn: () => fetchReminders(filter ? { status: filter } : {}),
  })

  const completeMut = useMutation({
    mutationFn: (id: number) => patchReminder(id, { status: 'done' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reminders'] }),
  })

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteReminder(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reminders'] }),
  })

  const bulkMut = useMutation({
    mutationFn: ({ action, ids }: { action: BulkReminderAction; ids: number[] }) => bulkUpdateReminders(ids, action),
    onSuccess: (result) => {
      setBulkMessage(`${result.updated} 条提醒已${result.action === 'delete' ? '删除' : '标记为已完成'}。`)
      setSelectedIds(new Set())
      queryClient.invalidateQueries({ queryKey: ['reminders'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: (error: Error) => setBulkMessage(`操作失败：${error.message}`),
  })

  if (isLoading) return <div className="empty-state">加载中...</div>

  const reminders = data?.items || []
  const selectableIds = reminders.filter((reminder) => reminder.status !== 'deleted').map((reminder) => reminder.id)
  const allSelected = selectableIds.length > 0 && selectableIds.every((id) => selectedIds.has(id))

  useEffect(() => {
    const visibleIds = new Set(reminders.map((reminder) => reminder.id))
    setSelectedIds((current) => new Set([...current].filter((id) => visibleIds.has(id))))
  }, [data?.items])

  const handleFilterChange = (value: string) => {
    setFilter(value)
    setSelectedIds(new Set())
    setBulkMessage('')
  }

  const toggleAll = (checked: boolean) => {
    setSelectedIds(checked ? new Set(selectableIds) : new Set())
  }

  const handleBulkAction = (action: BulkReminderAction) => {
    if (selectedIds.size === 0) return
    if (action === 'delete' && !window.confirm(`确定删除选中的 ${selectedIds.size} 条提醒吗？`)) return
    setBulkMessage('')
    bulkMut.mutate({ action, ids: [...selectedIds] })
  }

  return (
    <div>
      <div className="page-header">
        <h1>提醒</h1>
        <select value={filter} onChange={(e) => handleFilterChange(e.target.value)} style={{ fontSize: '0.875rem' }}>
          <option value="">全部活跃</option>
          <option value="pending">待处理</option>
          <option value="done">已完成</option>
        </select>
      </div>

      {reminders.length > 0 && (
        <div className="reminder-bulk-toolbar">
          <label className="reminder-select-all">
            <input type="checkbox" checked={allSelected} onChange={(e) => toggleAll(e.target.checked)} />
            <span>全选本页</span>
          </label>
          {selectedIds.size > 0 && (
            <>
              <span className="reminder-selected-count">已选 {selectedIds.size} 条</span>
              <button className="btn-secondary btn-sm" onClick={() => handleBulkAction('complete')} disabled={bulkMut.isPending}>
                <CheckCheck size={14} />
                <span>全部完成</span>
              </button>
              <button className="btn-danger btn-sm" onClick={() => handleBulkAction('delete')} disabled={bulkMut.isPending}>
                <Trash2 size={14} />
                <span>全部删除</span>
              </button>
            </>
          )}
        </div>
      )}
      {bulkMessage && <div className="reminder-bulk-message">{bulkMessage}</div>}

      <ReminderList
        reminders={reminders}
        selectedIds={selectedIds}
        onToggle={(id) => setSelectedIds((current) => {
          const next = new Set(current)
          if (next.has(id)) next.delete(id)
          else next.add(id)
          return next
        })}
        onComplete={(id) => completeMut.mutate(id)}
        onDelete={(id) => deleteMut.mutate(id)}
      />
    </div>
  )
}
