import KpiRow from '../components/dashboard/KpiRow'
import AlertsBySeverityChart from '../components/dashboard/AlertsBySeverityChart'
import AlertsByStatusChart from '../components/dashboard/AlertsByStatusChart'
import AlertVolumeChart from '../components/dashboard/AlertVolumeChart'
import RecentAlertsWidget from '../components/dashboard/RecentAlertsWidget'
import RecentLogsWidget from '../components/dashboard/RecentLogsWidget'

/**
 * Every widget below is fully independent: its own fetch, its own 10s
 * auto-refresh, its own loading skeleton, its own error handling. One
 * widget failing or being slow never blocks or blanks the others — see
 * useAutoRefresh (src/hooks) and WidgetCard/WidgetError
 * (src/components/dashboard) for the shared mechanics behind that.
 */
export default function Dashboard() {
  return (
    <div className="flex flex-col gap-6">
      <KpiRow />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <AlertsBySeverityChart />
        <AlertsByStatusChart />
        <AlertVolumeChart />
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <RecentAlertsWidget />
        <RecentLogsWidget />
      </div>
    </div>
  )
}
