import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchEmails } from '../api/emails'
import { EmailTable } from '../components/EmailTable'
import { EmailFilters } from '../components/EmailFilters'

export function EmailsPage() {
  const [filters, setFilters] = useState({ q: '', category: '', is_read: '', min_importance: '' })
  const [page, setPage] = useState(1)

  const params: Record<string, any> = { page, page_size: 20 }
  if (filters.q) params.q = filters.q
  if (filters.category) params.category = filters.category
  if (filters.is_read) params.is_read = filters.is_read === 'true'
  if (filters.min_importance) params.min_importance = Number(filters.min_importance)

  const { data, isLoading } = useQuery({
    queryKey: ['emails', params],
    queryFn: () => fetchEmails(params),
  })

  return (
    <div>
      <div className="page-header"><h1>邮件</h1></div>
      <EmailFilters filters={filters} onChange={setFilters} />

      {isLoading ? (
        <div className="empty-state">加载中...</div>
      ) : data ? (
        <>
          <EmailTable emails={data.items} />
          {data.total > data.page_size && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
              <button className="btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                上一页
              </button>
              <span style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}>
                第{data.page}页 / 共{Math.ceil(data.total / data.page_size)}页
              </span>
              <button className="btn-secondary btn-sm"
                disabled={page >= Math.ceil(data.total / data.page_size)}
                onClick={() => setPage(page + 1)}>
                下一页
              </button>
            </div>
          )}
        </>
      ) : null}
    </div>
  )
}
