export function ImportanceRating({ score, onChange }: { score: number; onChange?: (s: number) => void }) {
  return (
    <div style={{ display: 'flex', gap: 2 }}>
      {[1, 2, 3, 4, 5].map((s) => (
        <span
          key={s}
          onClick={() => onChange?.(s)}
          style={{
            cursor: onChange ? 'pointer' : 'default',
            color: s <= score ? '#f59e0b' : '#d1d5db',
            fontSize: '1.1rem',
          }}
        >
          &#9733;
        </span>
      ))}
    </div>
  )
}
