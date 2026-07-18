import { useEffect, useState } from 'react'
import { usersApi } from '../api/usersApi'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import Card from '../components/common/Card'
import ErrorBanner from '../components/common/ErrorBanner'
import EmptyState from '../components/common/EmptyState'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Modal from '../components/common/Modal'
import Button from '../components/common/Button'
import { Table, THead, TBody, TR, TH, TD } from '../components/common/Table'

export default function Users() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [confirming, setConfirming] = useState(null)

  function load() {
    setLoading(true)
    setError('')
    usersApi
      .list()
      .then(setUsers)
      .catch((err) => setError(getErrorMessage(err, 'Could not load users.')))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function handleDeactivate(id) {
    try {
      await usersApi.deactivate(id)
      setConfirming(null)
      load()
    } catch (err) {
      setError(getErrorMessage(err, 'Could not deactivate user.'))
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card title="Users" subtitle={`${users.length} account${users.length === 1 ? '' : 's'}`}>
        {error && (
          <div className="mb-4">
            <ErrorBanner message={error} onDismiss={() => setError('')} />
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-10">
            <LoadingSpinner label="Loading users…" />
          </div>
        ) : users.length === 0 ? (
          <EmptyState title="No users found" />
        ) : (
          <Table>
            <THead>
              <TR>
                <TH>Username</TH>
                <TH>Email</TH>
                <TH>Role</TH>
                <TH>Status</TH>
                <TH>Actions</TH>
              </TR>
            </THead>
            <TBody>
              {users.map((u) => (
                <TR key={u.id}>
                  <TD className="text-ink-100">{u.username}</TD>
                  <TD>{u.email}</TD>
                  <TD>{u.role}</TD>
                  <TD>
                    {u.is_active ? (
                      <span className="text-xs text-statuscolor-completed">Active</span>
                    ) : (
                      <span className="text-xs text-ink-600">Deactivated</span>
                    )}
                  </TD>
                  <TD>
                    {u.is_active && u.id !== currentUser?.id && (
                      <button
                        onClick={() => setConfirming(u)}
                        className="text-xs text-severity-critical hover:text-severity-critical/80"
                      >
                        Deactivate
                      </button>
                    )}
                    {u.id === currentUser?.id && <span className="text-xs text-ink-700">You</span>}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>

      <p className="text-xs text-ink-600">
        New accounts are provisioned directly by an administrator and are not created from this
        screen.
      </p>

      {confirming && (
        <Modal
          title="Deactivate user"
          onClose={() => setConfirming(null)}
          footer={
            <>
              <Button variant="secondary" onClick={() => setConfirming(null)}>
                Cancel
              </Button>
              <Button variant="danger" onClick={() => handleDeactivate(confirming.id)}>
                Deactivate
              </Button>
            </>
          }
        >
          <p className="text-sm text-ink-300">
            Deactivate <span className="font-medium text-ink-100">{confirming.username}</span>?
            They will no longer be able to sign in.
          </p>
        </Modal>
      )}
    </div>
  )
}
