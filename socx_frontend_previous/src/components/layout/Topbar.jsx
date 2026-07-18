import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

export default function Topbar({ title }) {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const initials = (user?.username || '?').slice(0, 2).toUpperCase()

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-base-600 bg-base-800/60 px-6">
      <h1 className="font-display text-lg font-semibold text-ink-100">{title}</h1>

      <div className="relative">
        <button
          onClick={() => setMenuOpen((v) => !v)}
          className="flex items-center gap-3 rounded px-2 py-1.5 transition-colors duration-150 hover:bg-base-700"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-600 text-xs font-semibold text-white">
            {initials}
          </span>
          <span className="text-left">
            <span className="block text-sm text-ink-100">{user?.username}</span>
            <span className="block text-xs text-ink-600">{user?.role}</span>
          </span>
          <svg
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            className="h-3.5 w-3.5 text-ink-600"
          >
            <path d="M5 8l5 5 5-5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        {menuOpen && (
          <>
            {/* Click-outside catcher */}
            <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
            <div className="absolute right-0 z-20 mt-2 w-44 rounded-md border border-base-600 bg-base-800 py-1 shadow-panel">
              <Link
                to="/settings"
                onClick={() => setMenuOpen(false)}
                className="block px-3 py-2 text-sm text-ink-300 transition-colors duration-150 hover:bg-base-700 hover:text-ink-100"
              >
                Settings
              </Link>
              <button
                onClick={logout}
                className="block w-full px-3 py-2 text-left text-sm text-severity-critical transition-colors duration-150 hover:bg-base-700"
              >
                Log out
              </button>
            </div>
          </>
        )}
      </div>
    </header>
  )
}
