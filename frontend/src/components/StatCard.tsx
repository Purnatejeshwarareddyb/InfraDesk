export function StatCard({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <div className="stat">
      <dt>{label}</dt>
      <dd>{value}</dd>
      {hint && <p className="stat-hint">{hint}</p>}
    </div>
  )
}
