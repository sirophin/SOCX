// Mirrors tailwind.config.js's `severity` / `statuscolor` / `base` / `ink`
// / `accent` scales. Kept in sync manually — SVG chart libraries need real
// color values, not Tailwind utility classes.

export const SEVERITY_COLORS = {
  critical: '#E0435C',
  high: '#F0834A',
  medium: '#E8B93F',
  low: '#5B9CF6',
  info: '#748097',
}

export const STATUS_COLORS = {
  Open: '#5B9CF6',
  Investigating: '#E8B93F',
  Contained: '#B07CE8',
  Resolved: '#3FCB7E',
  Closed: '#748097',
}

export const CHART_THEME = {
  grid: '#1E293B',
  axisText: '#748097',
  tooltipBg: '#111827',
  tooltipBorder: '#1E293B',
  accent: '#3B82F6',
}
