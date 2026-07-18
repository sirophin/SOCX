import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'
import { alertsApi } from '../../api/alertsApi'
import { CHART_THEME } from '../../utils/chartColors'
import { Skeleton } from '../common/Skeleton'
import { WidgetErrorBlock, WidgetErrorInline } from './WidgetError'
import WidgetCard from './WidgetCard'
import EmptyState from '../common/EmptyState'

const SAMPLE_SIZE = 100
const LOOKBACK_DAYS = 7

async function fetchAlertVolume() {
  // The backend has no time-bucketed aggregation endpoint, so this bucket
  // count is computed client-side from the most recent alerts. If there
  // are more than SAMPLE_SIZE alerts within the lookback window, older
  // ones within that window won't be reflected — the widget says so
  // explicitly rather than silently under-reporting.
  const resp = await alertsApi.list({ limit: SAMPLE_SIZE })

  const days = []
  const now = new Date()
  for (let i = LOOKBACK_DAYS - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    days.push({
      key: d.toISOString().slice(0, 10),
      label: d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      count: 0,
    })
  }
  const byDay = new Map(days.map((d) => [d.key, d]))

  for (const alert of resp.items) {
    const key = String(alert.created_at).slice(0, 10)
    const bucket = byDay.get(key)
    if (bucket) bucket.count += 1
  }

  return {
    days,
    sampledCount: resp.items.length,
    grandTotal: resp.total,
    isSampleIncomplete: resp.total > resp.items.length,
  }
}

export default function AlertVolumeChart() {
  const { data, loading, refreshing, error, lastUpdated, reload } = useAutoRefresh(
    fetchAlertVolume,
    { intervalMs: 10000 }
  )

  const hasAnyActivity = data?.days.some((d) => d.count > 0)

  return (
    <WidgetCard
      title="Alert Volume — last 7 days"
      subtitle={
        data?.isSampleIncomplete
          ? `Based on the most recent ${data.sampledCount} of ${data.grandTotal} alerts`
          : undefined
      }
      refreshing={refreshing}
      lastUpdated={lastUpdated}
    >
      {loading ? (
        <Skeleton className="h-56 w-full" />
      ) : error && !data ? (
        <WidgetErrorBlock message={error} onRetry={reload} />
      ) : !hasAnyActivity ? (
        <EmptyState title="No alert activity in the last 7 days" />
      ) : (
        <>
          {error && <WidgetErrorInline message={error} />}
          <span className="sr-only">
            {data.days.map((d) => `${d.label}: ${d.count} alerts.`).join(' ')}
          </span>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data.days} margin={{ left: -16, right: 16, top: 8 }}>
              <defs>
                <linearGradient id="alertVolumeFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={CHART_THEME.accent} stopOpacity={0.35} />
                  <stop offset="100%" stopColor={CHART_THEME.accent} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke={CHART_THEME.grid} vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fill: CHART_THEME.axisText, fontSize: 12 }}
                axisLine={{ stroke: CHART_THEME.grid }}
                tickLine={false}
              />
              <YAxis
                allowDecimals={false}
                tick={{ fill: CHART_THEME.axisText, fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                width={28}
              />
              <Tooltip
                contentStyle={{
                  background: CHART_THEME.tooltipBg,
                  border: `1px solid ${CHART_THEME.tooltipBorder}`,
                  borderRadius: 6,
                  fontSize: 12,
                }}
                labelStyle={{ color: '#E7ECF3' }}
              />
              <Area
                type="monotone"
                dataKey="count"
                name="Alerts"
                stroke={CHART_THEME.accent}
                strokeWidth={2}
                fill="url(#alertVolumeFill)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </>
      )}
    </WidgetCard>
  )
}
