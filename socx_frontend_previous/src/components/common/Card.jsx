export default function Card({ title, subtitle, action, children, className = '' }) {
  return (
    <div className={`rounded-md border border-base-600 bg-base-800 shadow-panel ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-base-600 px-5 py-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-ink-100">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-ink-500">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  )
}
