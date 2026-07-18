import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useAutoRefresh } from '../../hooks/useAutoRefresh'
import { alertsApi } from '../../api/alertsApi'
import { ALERT_STATUSES } from '../../utils/constants'
import { STATUS_COLORS, CHART_THEME } from '../../utils/chartColors'
import { Skeleton } from '../common/Skeleton'
import { WidgetErrorBlock, WidgetErrorInline } from './WidgetError'
import WidgetCard from './WidgetCard'
import EmptyState from '../common/EmptyState'

async function fetchStatusCounts() {
  const results = await Promise.all(
    ALERT_STATUSES.map((status) => alertsApi.list({ status, limit: 1 }))
  )
  return ALERT_STATUSES.map((status, i) => ({
    key: status,
    label: status,
    count: results[i].total,
  }))
}

export default function AlertsByStatusChart() {
  const { data, loading, refreshing, error, lastUpdated, reload } = useAutoRefresh(
    fetchStatusCounts,
    { intervalMs: 10000 }
  )

  const total = data?.reduce((sum, d) => sum + d.count, 0) ?? 0

  return (
    <WidgetCard title="Alerts by Status" refreshing={refreshing} lastUpdated={lastUpdated}>
      {loading ? (
        <Skeleton className="h-56 w-full" />
      ) : error && !data ? (
        <WidgetErrorBlock message={error} onRetry={reload} />
      ) : total === 0 ? (
        <EmptyState title="No alerts yet" />
      ) : (
        <>
          {error && <WidgetErrorInline message={error} />}
          <span className="sr-only">
            {data.map((d) => `${d.label}: ${d.count} alerts.`).join(' ')}
          </span>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
              <XAxis
                type="number"
                allowDecimals={false}
                tick={{ fill: CHART_THEME.axisText, fontSize: 12 }}
                axisLine={{ stroke: CHART_THEME.grid }}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="label"
                width={84}
                tick={{ fill: CHART_THEME.axisText, fontSize: 12 }}
                axisLine={{ stroke: CHART_THEME.grid }}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: CHART_THEME.grid, opacity: 0.4 }}
                contentStyle={{
                  background: CHART_THEME.tooltipBg,
                  border: `1px solid ${CHART_THEME.tooltipBorder}`,
                  borderRadius: 6,
                  fontSize: 12,
                }}
                labelStyle={{ color: '#E7ECF3' }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]} maxBarSize={28}>
                {data.map((entry) => (
                  <Cell key={entry.key} fill={STATUS_COLORS[entry.key]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </>
      )}
    </WidgetCard>
  )
}
