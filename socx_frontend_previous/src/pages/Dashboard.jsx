import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { alertsApi } from '../api/alertsApi'
import { logsApi } from '../api/logsApi'
import { detectionRulesApi } from '../api/detectionRulesApi'
import { investigationApi } from '../api/investigationApi'
import { getErrorMessage } from '../api/client'
import StatCard from '../components/common/StatCard'
import Card from '../components/common/Card'
import Badge from '../components/common/Badge'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorBanner from '../components/common/ErrorBanner'
import EmptyState from '../components/common/EmptyState'
import { formatRelativeTime, titleCase } from '../utils/formatters'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [stats, setStats] = useState(null)
  const [recentAlerts, setRecentAlerts] = useState([])
  const [recentLogs, setRecentLogs] = useState([])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    Promise.all([
      alertsApi.list({ limit: 1 }),
      alertsApi.list({ severity: 'critical', limit: 1 }),
      alertsApi.list({ status: 'Open', limit: 1 }),
      detectionRulesApi.list({ enabled: true, limit: 1 }),
      investigationApi.list({ limit: 1 }),
      alertsApi.list({ limit: 5 }),
      logsApi.list({ limit: 5 }),
    ])
      .then(
        ([
          allAlerts,
          criticalAlerts,
          openAlerts,
          enabledRules,
          normalizedEntries,
          recentAlertsResp,
          recentLogsResp,
        ]) => {
          if (cancelled) return
          setStats({
            totalAlerts: allAlerts.total,
            criticalAlerts: criticalAlerts.total,
            openAlerts: openAlerts.total,
            enabledRules: enabledRules.total,
            parsedEntries: normalizedEntries.total,
          })
          setRecentAlerts(recentAlertsResp.items)
          setRecentLogs(recentLogsResp.items)
        }
      )
      .catch((err) => {
        if (!cancelled) setError(getErrorMessage(err, 'Could not load dashboard data.'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner label="Loading dashboard…" />
      </div>
    )
  }

  if (error) {
    return <ErrorBanner message={error} />
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <StatCard label="Total Alerts" value={stats.totalAlerts} />
        <StatCard
          label="Critical Alerts"
          value={stats.criticalAlerts}
          accent={stats.criticalAlerts > 0 ? 'text-severity-critical' : 'text-ink-100'}
        />
        <StatCard
          label="Open Alerts"
          value={stats.openAlerts}
          accent={stats.openAlerts > 0 ? 'text-statuscolor-open' : 'text-ink-100'}
        />
        <StatCard label="Enabled Rules" value={stats.enabledRules} />
        <StatCard label="Parsed Log Entries" value={stats.parsedEntries.toLocaleString()} />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <Card
          title="Recent Alerts"
          action={
            <Link to="/alerts" className="text-xs text-accent-500 hover:text-accent-400">
              View all
            </Link>
          }
        >
          {recentAlerts.length === 0 ? (
            <EmptyState title="No alerts yet" description="Alerts will appear here once the Detection Engine matches a rule." />
          ) : (
            <ul className="flex flex-col divide-y divide-base-600/70">
              {recentAlerts.map((alert) => (
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
          )}
        </Card>

        <Card
          title="Recent Log Uploads"
          action={
            <Link to="/upload" className="text-xs text-accent-500 hover:text-accent-400">
              Upload more
            </Link>
          }
        >
          {recentLogs.length === 0 ? (
            <EmptyState title="No logs uploaded yet" description="Upload a log file to get started." />
          ) : (
            <ul className="flex flex-col divide-y divide-base-600/70">
              {recentLogs.map((log) => (
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
          )}
        </Card>
      </div>
    </div>
  )
}
