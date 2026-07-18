import { NavLink } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { canViewPage, PAGES } from '../../utils/permissions'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: IconGrid, end: true, page: PAGES.DASHBOARD },
  { to: '/upload', label: 'Upload Logs', icon: IconUpload, page: PAGES.UPLOAD_LOGS },
  { to: '/investigation', label: 'Investigation', icon: IconSearch, page: PAGES.INVESTIGATION },
  { to: '/alerts', label: 'Alerts', icon: IconBell, page: PAGES.ALERTS },
  { to: '/detection-rules', label: 'Detection Rules', icon: IconShield, page: PAGES.DETECTION_RULES },
  { to: '/sample-datasets', label: 'Sample Datasets', icon: IconDatabase, page: PAGES.SAMPLE_DATASETS },
  { to: '/users', label: 'Users', icon: IconUsers, page: PAGES.USERS },
  { to: '/settings', label: 'Settings', icon: IconSettings, page: PAGES.SETTINGS },
{
  to: '/simulation',
  label: 'Simulation',
  icon: IconPlay,
  page: PAGES.SIMULATION,
},
]

export default function Sidebar() {
  const { user } = useAuth()

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-base-600 bg-base-800">
      <div className="flex h-16 items-center gap-2 border-b border-base-600 px-5">
        <span className="font-mono text-lg font-semibold text-accent-500">[</span>
        <span className="font-display text-lg font-semibold tracking-tight text-ink-100">SOCX</span>
        <span className="font-mono text-lg font-semibold text-accent-500">]</span>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
        {NAV_ITEMS.filter((item) => canViewPage(user?.role, item.page)).map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors duration-150 ${
                isActive
                  ? 'border-l-2 border-accent-500 bg-accent-500/10 pl-[10px] text-ink-100'
                  : 'border-l-2 border-transparent text-ink-500 hover:bg-base-700 hover:text-ink-200'
              }`
            }
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-base-600 px-4 py-3 text-[11px] text-ink-700">
        <p>SOCX Platform</p>
        <p>v1.0.0</p>
      </div>
    </aside>
  )
}

/* Minimal inline icon set — kept dependency-free rather than pulling in
   an icon library for a handful of nav glyphs. */

function IconGrid(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" {...props}>
      <rect x="3" y="3" width="6" height="6" rx="1" />
      <rect x="11" y="3" width="6" height="6" rx="1" />
      <rect x="3" y="11" width="6" height="6" rx="1" />
      <rect x="11" y="11" width="6" height="6" rx="1" />
    </svg>
  )
}
function IconUpload(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" {...props}>
      <path d="M10 13V4M10 4L6.5 7.5M10 4l3.5 3.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 14v1.5A1.5 1.5 0 0 0 5.5 17h9a1.5 1.5 0 0 0 1.5-1.5V14" strokeLinecap="round" />
    </svg>
  )
}
function IconSearch(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" {...props}>
      <circle cx="8.5" cy="8.5" r="5" />
      <path d="M16 16l-3.5-3.5" strokeLinecap="round" />
    </svg>
  )
}
function IconBell(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" {...props}>
      <path
        d="M5 8a5 5 0 0 1 10 0c0 3.5 1 4.5 1 4.5H4S5 11.5 5 8Z"
        strokeLinejoin="round"
      />
      <path d="M8.5 15.5a1.5 1.5 0 0 0 3 0" strokeLinecap="round" />
    </svg>
  )
}
function IconShield(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" {...props}>
      <path
        d="M10 2.5l6 2.2v4.8c0 4-2.6 6.7-6 8-3.4-1.3-6-4-6-8V4.7l6-2.2Z"
        strokeLinejoin="round"
      />
      <path d="M7.3 10l1.9 1.9 3.5-3.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
function IconDatabase(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" {...props}>
      <ellipse cx="10" cy="4.5" rx="6" ry="2.2" />
      <path d="M4 4.5v11c0 1.2 2.7 2.2 6 2.2s6-1 6-2.2v-11" strokeLinecap="round" />
      <path d="M4 10c0 1.2 2.7 2.2 6 2.2s6-1 6-2.2" strokeLinecap="round" />
    </svg>
  )
}
function IconUsers(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" {...props}>
      <circle cx="7" cy="7" r="2.5" />
      <path d="M2.5 16c0-2.5 2-4 4.5-4s4.5 1.5 4.5 4" strokeLinecap="round" />
      <circle cx="14.5" cy="7.5" r="2" />
      <path d="M12.8 8.3c.3-.1.6-.1 1-.1 2 0 3.7 1.2 3.7 3.3" strokeLinecap="round" />
    </svg>
  )
}
function IconSettings(props) {
  return (
    <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" {...props}>
      <circle cx="10" cy="10" r="2.5" />
      <path
        d="M10 2.8v1.6M10 15.6v1.6M17.2 10h-1.6M4.4 10H2.8M15 5l-1.1 1.1M6.1 13.9 5 15M15 15l-1.1-1.1M6.1 6.1 5 5"
        strokeLinecap="round"
      />
    </svg>
  )
}
function IconPlay(props) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      {...props}
    >
      <polygon
        points="7,5 15,10 7,15"
        fill="currentColor"
      />
    </svg>
  )
}
