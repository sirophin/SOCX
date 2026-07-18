export default function EmptyState({ icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
      {icon && <div className="mb-2 text-ink-600">{icon}</div>}
      <p className="text-sm font-medium text-ink-300">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-600">{description}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  )
}
