import { useAuth } from '../hooks/useAuth'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import Badge from '../components/common/Badge'

export default function Settings() {
  const { user, logout } = useAuth()

  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <Card title="Account">
        <dl className="grid grid-cols-2 gap-x-6 gap-y-4">
          <div>
            <dt className="text-xs text-ink-600">Username</dt>
            <dd className="mt-0.5 text-sm text-ink-100">{user?.username}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-600">Email</dt>
            <dd className="mt-0.5 text-sm text-ink-100">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-600">Role</dt>
            <dd className="mt-0.5 text-sm text-ink-100">{user?.role}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-600">Status</dt>
            <dd className="mt-0.5">
              <Badge kind="status" value={user?.is_active ? 'completed' : 'closed'}>
                {user?.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </dd>
          </div>
        </dl>
      </Card>

      <Card title="Session">
        <p className="mb-4 text-sm text-ink-500">
          Your access token refreshes automatically while you're active. Signing out revokes your
          session on this device.
        </p>
        <Button variant="danger" onClick={logout}>
          Sign out
        </Button>
      </Card>

      <p className="text-xs text-ink-700">
        Profile editing, password changes, and notification preferences aren't available yet —
        contact an administrator for account changes.
      </p>
    </div>
  )
}
