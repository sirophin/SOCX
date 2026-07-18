export default function ErrorBanner({ message, onDismiss }) {
  if (!message) return null

  return (
    <div className="flex items-start justify-between gap-3 rounded border border-severity-critical/30 bg-severity-critical/10 px-4 py-3 text-sm text-severity-critical">
      <span>{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="shrink-0 text-severity-critical/70 transition-colors duration-150 hover:text-severity-critical"
          aria-label="Dismiss"
        >
          ✕
        </button>
      )}
    </div>
  )
}
