import { Link } from 'react-router-dom'
import Button from '../components/common/Button'

export default function NotFound() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-3 bg-base-900 text-center">
      <p className="font-mono text-sm text-accent-500">404</p>
      <h1 className="font-display text-xl font-semibold text-ink-100">Page not found</h1>
      <p className="max-w-sm text-sm text-ink-600">
        The page you're looking for doesn't exist or may have moved.
      </p>
      <Link to="/" className="mt-2">
        <Button variant="secondary">Back to Dashboard</Button>
      </Link>
    </div>
  )
}
