export function Field({ label, hint, error, htmlFor, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={htmlFor} className="text-xs font-medium text-ink-300">
          {label}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-ink-600">{hint}</p>}
      {error && <p className="text-xs text-severity-critical">{error}</p>}
    </div>
  )
}

const baseFieldClass =
  'w-full rounded border border-base-500 bg-base-900 px-3 py-2 text-sm text-ink-100 placeholder:text-ink-700 transition-colors duration-150 focus:border-accent-500 disabled:opacity-50'

export function Input(props) {
  return <input className={baseFieldClass} {...props} />
}

export function Textarea(props) {
  return <textarea className={`${baseFieldClass} min-h-[80px] resize-y`} {...props} />
}

export function Select({ children, ...props }) {
  return (
    <select className={baseFieldClass} {...props}>
      {children}
    </select>
  )
}

export function Checkbox({ label, ...props }) {
  return (
    <label className="flex items-center gap-2 text-sm text-ink-300">
      <input
        type="checkbox"
        className="h-4 w-4 rounded border-base-500 bg-base-900 text-accent-600 focus:ring-accent-500"
        {...props}
      />
      {label}
    </label>
  )
}
