import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getErrorMessage } from '../api/client'
import { Field, Input } from '../components/common/Field'
import Button from '../components/common/Button'
import ErrorBanner from '../components/common/ErrorBanner'

export default function Login() {
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to={location.state?.from?.pathname || '/'} replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(username, password)
      navigate(location.state?.from?.pathname || '/', { replace: true })
    } catch (err) {
      setError(getErrorMessage(err, 'Invalid username or password.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-base-900 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-2">
          <span className="font-mono text-2xl font-semibold text-accent-500">[</span>
          <span className="font-display text-2xl font-semibold tracking-tight text-ink-100">
            SOCX
          </span>
          <span className="font-mono text-2xl font-semibold text-accent-500">]</span>
        </div>

        <div className="rounded-md border border-base-600 bg-base-800 p-6 shadow-panel">
          <h1 className="mb-1 text-sm font-semibold text-ink-100">Sign in</h1>
          <p className="mb-5 text-xs text-ink-600">
            SOC Monitoring &amp; Incident Response Platform
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}

            <Field label="Username" htmlFor="username">
              <Input
                id="username"
                name="username"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
              />
            </Field>

            <Field label="Password" htmlFor="password">
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </Field>

            <Button type="submit" disabled={submitting} className="mt-1 w-full">
              {submitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-ink-700">
          Access is provisioned by your administrator.
        </p>
      </div>
    </div>
  )
}
