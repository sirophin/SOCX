import { Link } from 'react-router-dom'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'
import { logsApi } from '../../api/logsApi'
import { formatRelativeTime, titleCase } from '../../utils/formatters'
import { Skeleton } from '../common/Skeleton'
import Badge from '../common/Badge'
import EmptyState from '../common/EmptyState'
import { WidgetErrorBlock, WidgetErrorInline } from './WidgetError'
import WidgetCard from './WidgetCard'

const fetchRecentLogs = () => logsApi.list({ limit: 5 })

export default function RecentLogsWidget() {
  const { data, loading, refreshing, error, lastUpdated, reload } = useAutoRefresh(
    fetchRecentLogs,
    { intervalMs: 10000 }
  )

  return (
    <WidgetCard
      title="Recent Log Uploads"
      refreshing={refreshing}
      lastUpdated={lastUpdated}
      action={
        <Link to="/upload" className="text-xs text-accent-500 hover:text-accent-400">
          Upload more
        </Link>
      }
    >
      {loading ? (
        <div className="flex flex-col divide-y divide-base-600/70">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex items-center justify-between gap-3 py-3">
              <div className="flex-1">
                <Skeleton className="h-3.5 w-48" />
                <Skeleton className="mt-2 h-3 w-28" />
              </div>
              <Skeleton className="h-5 w-16" />
            </div>
          ))}
        </div>
      ) : error && !data ? (
        <WidgetErrorBlock message={error} onRetry={reload} />
      ) : data.items.length === 0 ? (
        <EmptyState title="No logs uploaded yet" description="Upload a log file to get started." />
      ) : (
        <>
          {error && <WidgetErrorInline message={error} />}
          <ul className="flex flex-col divide-y divide-base-600/70">
            {data.items.map((log) => (
              <li key={log.id} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate font-mono text-sm text-ink-100">
                    {log.original_filename}
                  </p>
                  <p className="text-xs text-ink-600">
                    {titleCase(log.source_type)} · {formatRelativeTime(log.ingested_at)}
                  </p>
                </div>
                <Badge kind="status" value={log.parse_status} />
              </li>
            ))}
          </ul>
        </>
      )}
    </WidgetCard>
  )
}
