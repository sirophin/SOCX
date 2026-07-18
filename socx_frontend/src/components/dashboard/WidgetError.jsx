/** No data has ever loaded successfully — nothing to show behind the error. */
export function WidgetErrorBlock({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center gap-3 py-8 text-center">
      <p className="text-sm text-severity-critical">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs font-medium text-accent-500 hover:text-accent-400"
        >
          Retry
        </button>
      )}
    </div>
  )
}

/** Data from a previous successful load is still on screen; only the most
 * recent background refresh failed. Shown above the (still-visible) stale
 * content rather than replacing it. */
export function WidgetErrorInline({ message }) {
  return (
    <div className="mb-3 rounded border border-severity-critical/30 bg-severity-critical/10 px-3 py-2 text-xs text-severity-critical">
      Last refresh failed — showing the most recent data. {message}
    </div>
  )
}
