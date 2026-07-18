export default function LoadingSpinner({ label, size = 'md' }) {
  const sizeClass = size === 'sm' ? 'h-4 w-4 border-2' : 'h-6 w-6 border-2'

  return (
    <div className="flex items-center gap-3 text-ink-500">
      <span
        className={`${sizeClass} animate-spin rounded-full border-accent-500 border-t-transparent`}
        role="status"
        aria-label="Loading"
      />
      {label && <span className="text-sm">{label}</span>}
    </div>
  )
}
