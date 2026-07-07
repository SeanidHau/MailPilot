const colors: Record<string, string> = {
  important: '#ef4444',
  normal: '#6b7280',
  promotion: '#f59e0b',
  bill: '#8b5cf6',
  school_work: '#3b82f6',
  needs_reply: '#22c55e',
  spam: '#9ca3af',
}

const labels: Record<string, string> = {
  important: '重要',
  normal: '普通',
  promotion: '促销',
  bill: '账单',
  school_work: '学业/工作',
  needs_reply: '待回复',
  spam: '垃圾邮件',
}

export function CategoryBadge({ category }: { category: string }) {
  return (
    <span style={{
      display: 'inline-block', padding: '0.125rem 0.5rem', borderRadius: 9999,
      background: (colors[category] || '#6b7280') + '20',
      color: colors[category] || '#6b7280',
      fontSize: '0.75rem', fontWeight: 600,
    }}>
      {labels[category] || category}
    </span>
  )
}
