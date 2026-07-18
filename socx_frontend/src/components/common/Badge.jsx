const SEVERITY_STYLES = {
  critical: 'bg-severity-critical/15 text-severity-critical border-severity-critical/30',
  high: 'bg-severity-high/15 text-severity-high border-severity-high/30',
  medium: 'bg-severity-medium/15 text-severity-medium border-severity-medium/30',
  low: 'bg-severity-low/15 text-severity-low border-severity-low/30',
  info: 'bg-severity-info/15 text-severity-info border-severity-info/30',
}

const STATUS_STYLES = {
  open: 'bg-statuscolor-open/15 text-statuscolor-open border-statuscolor-open/30',
  investigating:
    'bg-statuscolor-investigating/15 text-statuscolor-investigating border-statuscolor-investigating/30',
  contained: 'bg-statuscolor-contained/15 text-statuscolor-contained border-statuscolor-contained/30',
  resolved: 'bg-statuscolor-resolved/15 text-statuscolor-resolved border-statuscolor-resolved/30',
  closed: 'bg-statuscolor-closed/15 text-statuscolor-closed border-statuscolor-closed/30',
  pending: 'bg-statuscolor-pending/15 text-statuscolor-pending border-statuscolor-pending/30',
  parsing: 'bg-statuscolor-parsing/15 text-statuscolor-parsing border-statuscolor-parsing/30',
  completed: 'bg-statuscolor-completed/15 text-statuscolor-completed border-statuscolor-completed/30',
  partial: 'bg-statuscolor-partial/15 text-statuscolor-partial border-statuscolor-partial/30',
  failed: 'bg-statuscolor-failed/15 text-statuscolor-failed border-statuscolor-failed/30',
}

// Reuses the existing severity color scale rather than inventing new
// tokens — difficulty and severity both express "how much this demands
// your attention," so the same visual language fits.
const DIFFICULTY_STYLES = {
  beginner: 'bg-severity-low/15 text-severity-low border-severity-low/30',
  intermediate: 'bg-severity-medium/15 text-severity-medium border-severity-medium/30',
  advanced: 'bg-severity-high/15 text-severity-high border-severity-high/30',
}

const STYLE_MAPS = {
  severity: SEVERITY_STYLES,
  status: STATUS_STYLES,
  difficulty: DIFFICULTY_STYLES,
}

function normalize(value) {
  return String(value ?? '').toLowerCase()
}

/** kind="severity" | "status" | "difficulty" picks which color map to use; value is matched case-insensitively. */
export default function Badge({ kind = 'status', value, children }) {
  const key = normalize(value)
  const styles = STYLE_MAPS[kind] || STATUS_STYLES
  const className = styles[key] || 'bg-base-600/50 text-ink-500 border-base-500'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-xs font-medium capitalize ${className}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {children || value}
    </span>
  )
}
