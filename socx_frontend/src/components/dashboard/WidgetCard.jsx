import { formatRelativeTime } from '../../utils/formatters'

/**
 * Chrome shared by every dashboard widget: title, a small pulsing dot
 * while a background refresh is in flight (not shown during the initial
 * load — that's what the skeleton is for), a "last updated" relative
 * timestamp, and an optional header action (e.g. a link to the full
 * page). The body itself is entirely up to the caller — each widget
 * decides for itself whether to render a skeleton, an error state, or
 * real content, since that decision depends on data shape they own.
 */
export default function WidgetCard({ title, subtitle, refreshing, lastUpdated, action, children }) {
  return (
    <div className="rounded-md border border-base-600 bg-base-800 shadow-panel">
      <div className="flex items-center justify-between border-b border-base-600 px-5 py-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-ink-100">{title}</h3>
            {refreshing && (
              <span
                className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-500"
                title="Refreshing…"
                role="status"
                aria-label="Refreshing"
              />
            )}
          </div>
          {subtitle && <p className="mt-0.5 text-xs text-ink-500">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-[11px] text-ink-700">
              Updated {formatRelativeTime(lastUpdated)}
            </span>
          )}
          {action}
        </div>
      </div>
      <div className="p-5">{children}</div>
    </div>
  )
}
