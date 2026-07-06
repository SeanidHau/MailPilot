interface Props {
  label: string
  value: number
  color?: string
}

export function StatCard({ label, value, color = 'var(--color-primary)' }: Props) {
  return (
    <div className="card" style={{ textAlign: 'center', flex: 1, minWidth: 140 }}>
      <div style={{ fontSize: '2rem', fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', marginTop: 4 }}>{label}</div>
    </div>
  )
}
