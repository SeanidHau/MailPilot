const CATEGORIES = ['', 'important', 'normal', 'promotion', 'bill', 'school_work', 'needs_reply', 'spam']

interface Props {
  filters: { q: string; category: string; is_read: string; min_importance: string }
  onChange: (f: any) => void
}

export function EmailFilters({ filters, onChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
      <input
        placeholder="Search emails..."
        value={filters.q}
        onChange={(e) => onChange({ ...filters, q: e.target.value })}
        style={{ flex: '1 1 200px' }}
      />
      <select value={filters.category} onChange={(e) => onChange({ ...filters, category: e.target.value })}>
        {CATEGORIES.map((c) => (
          <option key={c} value={c}>{c ? c.replace('_', ' ') : 'All Categories'}</option>
        ))}
      </select>
      <select value={filters.is_read} onChange={(e) => onChange({ ...filters, is_read: e.target.value })}>
        <option value="">All</option>
        <option value="true">Read</option>
        <option value="false">Unread</option>
      </select>
      <select value={filters.min_importance} onChange={(e) => onChange({ ...filters, min_importance: e.target.value })}>
        <option value="">Any Importance</option>
        {[1, 2, 3, 4, 5].map((s) => (
          <option key={s} value={s}>{s}+ Stars</option>
        ))}
      </select>
    </div>
  )
}
