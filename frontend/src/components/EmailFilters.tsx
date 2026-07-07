const CATEGORIES = ['', 'important', 'normal', 'promotion', 'bill', 'school_work', 'needs_reply', 'spam']

interface Props {
  filters: { q: string; category: string; is_read: string; min_importance: string }
  onChange: (f: any) => void
}

export function EmailFilters({ filters, onChange }: Props) {
  return (
    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
      <input
        placeholder="搜索邮件..."
        value={filters.q}
        onChange={(e) => onChange({ ...filters, q: e.target.value })}
        style={{ flex: '1 1 200px' }}
      />
      <select value={filters.category} onChange={(e) => onChange({ ...filters, category: e.target.value })}>
        {CATEGORIES.map((c) => (
          <option key={c} value={c}>{c ? ({important:'重要',normal:'普通',promotion:'促销',bill:'账单',school_work:'学业/工作',needs_reply:'待回复',spam:'垃圾邮件'}[c]||c) : '所有分类'}</option>
        ))}
      </select>
      <select value={filters.is_read} onChange={(e) => onChange({ ...filters, is_read: e.target.value })}>
        <option value="">全部</option>
        <option value="true">已读</option>
        <option value="false">未读</option>
      </select>
      <select value={filters.min_importance} onChange={(e) => onChange({ ...filters, min_importance: e.target.value })}>
        <option value="">任何重要性</option>
        {[1, 2, 3, 4, 5].map((s) => (
          <option key={s} value={s}>{s}+ 星</option>
        ))}
      </select>
    </div>
  )
}
