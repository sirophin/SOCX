import { useAutoRefresh } from '../../hooks/useAutoRefresh'
import { alertsApi } from '../../api/alertsApi'
import { detectionRulesApi } from '../../api/detectionRulesApi'
import { investigationApi } from '../../api/investigationApi'
import StatCard from '../common/StatCard'
import { Skeleton } from '../common/Skeleton'
import { WidgetErrorBlock, WidgetErrorInline } from './WidgetError'

async function fetchKpis() {
  const [allAlerts, criticalAlerts, openAlerts, enabledRules, parsedEntries] = await Promise.all([
    alertsApi.list({ limit: 1 }),
    alertsApi.list({ severity: 'critical', limit: 1 }),
    alertsApi.list({ status: 'Open', limit: 1 }),
    detectionRulesApi.list({ enabled: true, limit: 1 }),
    investigationApi.list({ limit: 1 }),
  ])
  return {
    totalAlerts: allAlerts.total,
    criticalAlerts: criticalAlerts.total,
    openAlerts: openAlerts.total,
    enabledRules: enabledRules.total,
    parsedEntries: parsedEntries.total,
  }
}

export default function KpiRow() {
  const { data, loading, refreshing, error, reload } = useAutoRefresh(fetchKpis, {
    intervalMs: 10000,
  })

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="rounded-md border border-base-600 bg-base-800 p-5">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="mt-3 h-7 w-14" />
          </div>
        ))}
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="rounded-md border border-base-600 bg-base-800 shadow-panel">
        <WidgetErrorBlock message={error} onRetry={reload} />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {error && data && <WidgetErrorInline message={error} />}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <StatCard label="Total Alerts" value={data.totalAlerts} />
        <StatCard
          label="Critical Alerts"
          value={data.criticalAlerts}
          accent={data.criticalAlerts > 0 ? 'text-severity-critical' : 'text-ink-100'}
        />
        <StatCard
          label="Open Alerts"
          value={data.openAlerts}
          accent={data.openAlerts > 0 ? 'text-statuscolor-open' : 'text-ink-100'}
        />
        <StatCard label="Enabled Rules" value={data.enabledRules} />
        <StatCard label="Parsed Log Entries" value={data.parsedEntries.toLocaleString()} />
      </div>
      {refreshing && (
        <span className="self-end text-[11px] text-ink-700">Refreshing…</span>
      )}
    </div>
  )
}
