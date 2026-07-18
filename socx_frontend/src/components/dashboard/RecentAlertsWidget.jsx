import { Link } from 'react-router-dom'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'
import { alertsApi } from '../../api/alertsApi'
import { formatRelativeTime } from '../../utils/formatters'
import { Skeleton } from '../common/Skeleton'
import Badge from '../common/Badge'
import EmptyState from '../common/EmptyState'
import { WidgetErrorBlock, WidgetErrorInline } from './WidgetError'
import WidgetCard from './WidgetCard'

const fetchRecentAlerts = () => alertsApi.list({ limit: 5 })

export default function RecentAlertsWidget() {
  const { data, loading, refreshing, error, lastUpdated, reload } = useAutoRefresh(
    fetchRecentAlerts,
    { intervalMs: 10000 }
  )

  return (
    <WidgetCard
      title="Recent Alerts"
      refreshing={refreshing}
      lastUpdated={lastUpdated}
      action={
        <Link to="/alerts" className="text-xs text-accent-500 hover:text-accent-400">
          View all
        </Link>
      }
    >
      {loading ? (
        <div className="flex flex-col divide-y divide-base-600/70">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between gap-3 py-3">
              <div className="flex-1">
                <Skeleton className="h-3.5 w-40" />
                <Skeleton className="mt-2 h-3 w-24" />
              </div>
              <Skeleton className="h-5 w-16" />
            </div>
          ))}
        </div>
      ) : error && !data ? (
        <WidgetErrorBlock message={error} onRetry={reload} />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="No alerts yet"
          description="Alerts will appear here once the Detection Engine matches a rule."
        />
      ) : (
        <>
          {error && <WidgetErrorInline message={error} />}
          <ul className="flex flex-col divide-y divide-base-600/70">
            {data.items.map((alert) => (
              <li key={alert.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate text-sm text-ink-100">{alert.rule.name}</p>
                  <p className="text-xs text-ink-600">{formatRelativeTime(alert.created_at)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge kind="severity" value={alert.severity} />
                  <Badge kind="status" value={alert.status} />
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </WidgetCard>
  )
}
