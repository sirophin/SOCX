export default function StatCard({ label, value, accent = 'text-ink-100', icon }) {
  return (
    <div className="rounded-md border border-base-600 bg-base-800 p-5 shadow-panel">
      <div className="flex items-start justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-ink-600">{label}</span>
        {icon && <span className="text-ink-700">{icon}</span>}
      </div>
      <p className={`mt-3 font-display text-2xl font-semibold ${accent}`}>{value}</p>
    </div>
  )
}
