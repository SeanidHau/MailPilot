import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchReminders, patchReminder, deleteReminder } from '../api/reminders'
import { ReminderList } from '../components/ReminderList'
import { useState } from 'react'

export function RemindersPage() {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState('')

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

  if (isLoading) return <div className="empty-state">Loading...</div>

  const reminders = data?.items || []

  return (
    <div>
      <div className="page-header">
        <h1>Reminders</h1>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ fontSize: '0.875rem' }}>
          <option value="">All Active</option>
          <option value="pending">Pending</option>
          <option value="done">Completed</option>
        </select>
      </div>

      <ReminderList
        reminders={reminders}
        onComplete={(id) => completeMut.mutate(id)}
        onDelete={(id) => deleteMut.mutate(id)}
      />
    </div>
  )
}
