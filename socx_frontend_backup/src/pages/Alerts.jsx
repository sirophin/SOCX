import { useEffect, useState } from 'react'
import { alertsApi } from '../api/alertsApi'
import { getErrorMessage } from '../api/client'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import { Field, Select } from '../components/common/Field'
import ErrorBanner from '../components/common/ErrorBanner'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'
import Modal from '../components/common/Modal'
import Pagination from '../components/common/Pagination'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { Table, THead, TBody, TR, TH, TD } from '../components/common/Table'
import { formatDateTime } from '../utils/formatters'
import { SEVERITIES, ALERT_STATUSES, ALERT_SOURCES } from '../utils/constants'

const LIMIT = 20

export default function Alerts() {
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [source, setSource] = useState('')
  const [offset, setOffset] = useState(0)

  const [alerts, setAlerts] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [actionError, setActionError] = useState('')

  function load() {
    setLoading(true)
    setError('')
    alertsApi
      .list({ severity, status, source, limit: LIMIT, offset })
      .then((data) => {
        setAlerts(data.items)
        setTotal(data.total)
      })
      .catch((err) => setError(getErrorMessage(err, 'Could not load alerts.')))
      .finally(() => setLoading(false))
  }

  useEffect(load, [severity, status, source, offset])

  async function handleAcknowledge(alertId) {
    setActionError('')
    try {
      const updated = await alertsApi.acknowledge(alertId)
      applyUpdate(updated)
    } catch (err) {
      setActionError(getErrorMessage(err, 'Could not acknowledge alert.'))
    }
  }

  async function handleClose(alertId) {
    setActionError('')
    try {
      const updated = await alertsApi.close(alertId)
      applyUpdate(updated)
    } catch (err) {
      setActionError(getErrorMessage(err, 'Could not close alert.'))
    }
  }

  function applyUpdate(updated) {
    setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
    setSelected((prev) => (prev && prev.id === updated.id ? updated : prev))
  }

  return (
    <div className="flex flex-col gap-6">
      <Card title="Filters">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Field label="Severity">
            <Select
              value={severity}
              onChange={(e) => {
                setOffset(0)
                setSeverity(e.target.value)
              }}
            >
              <option value="">Any</option>
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Status">
            <Select
              value={status}
              onChange={(e) => {
                setOffset(0)
                setStatus(e.target.value)
              }}
            >
              <option value="">Any</option>
              {ALERT_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Source">
            <Select
              value={source}
              onChange={(e) => {
                setOffset(0)
                setSource(e.target.value)
              }}
            >
              <option value="">Any</option>
              {ALERT_SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s.replace('_', ' ')}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </Card>

      <Card title="Alerts" subtitle={`${total} alert${total === 1 ? '' : 's'}`}>
        {(error || actionError) && (
          <div className="mb-4">
            <ErrorBanner message={error || actionError} onDismiss={() => { setError(''); setActionError('') }} />
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-10">
            <LoadingSpinner label="Loading alerts…" />
          </div>
        ) : alerts.length === 0 ? (
          <EmptyState
            title="No alerts match these filters"
            description="Alerts appear here automatically when the Detection Engine matches a rule against incoming log entries."
          />
        ) : (
          <>
            <Table>
              <THead>
                <TR>
                  <TH>Rule</TH>
                  <TH>Severity</TH>
                  <TH>Status</TH>
                  <TH>Source</TH>
                  <TH>Analyst</TH>
                  <TH>Created</TH>
                  <TH>Actions</TH>
                </TR>
              </THead>
              <TBody>
                {alerts.map((alert) => (
                  <TR key={alert.id} onClick={() => setSelected(alert)}>
                    <TD className="text-ink-100">{alert.rule.name}</TD>
                    <TD>
                      <Badge kind="severity" value={alert.severity} />
                    </TD>
                    <TD>
                      <Badge kind="status" value={alert.status} />
                    </TD>
                    <TD>{alert.source.replace('_', ' ')}</TD>
                    <TD>{alert.analyst?.username || '—'}</TD>
                    <TD className="whitespace-nowrap">{formatDateTime(alert.created_at)}</TD>
                    <TD>
                      <div
                        className="flex items-center gap-3"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          disabled={alert.status === 'Closed'}
                          onClick={() => handleAcknowledge(alert.id)}
                          className="text-xs text-accent-500 hover:text-accent-400 disabled:cursor-not-allowed disabled:text-ink-700"
                        >
                          Acknowledge
                        </button>
                        <button
                          disabled={alert.status === 'Closed'}
                          onClick={() => handleClose(alert.id)}
                          className="text-xs text-ink-500 hover:text-ink-200 disabled:cursor-not-allowed disabled:text-ink-700"
                        >
                          Close
                        </button>
                      </div>
                    </TD>
                  </TR>
                ))}
              </TBody>
            </Table>
            <Pagination total={total} limit={LIMIT} offset={offset} onOffsetChange={setOffset} />
          </>
        )}
      </Card>

      {selected && (
        <Modal title="Alert Detail" onClose={() => setSelected(null)} width="max-w-2xl">
          <AlertDetail
            alert={selected}
            onAcknowledge={() => handleAcknowledge(selected.id)}
            onClose={() => handleClose(selected.id)}
          />
        </Modal>
      )}
    </div>
  )
}

function AlertDetail({ alert, onAcknowledge, onClose }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-ink-100">{alert.rule.name}</p>
          <p className="text-xs text-ink-600">{formatDateTime(alert.created_at)}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge kind="severity" value={alert.severity} />
          <Badge kind="status" value={alert.status} />
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
        <div>
          <dt className="text-xs text-ink-600">Source</dt>
          <dd className="mt-0.5 text-sm text-ink-100">{alert.source.replace('_', ' ')}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-600">Assigned Analyst</dt>
          <dd className="mt-0.5 text-sm text-ink-100">{alert.analyst?.username || 'Unassigned'}</dd>
        </div>
      </dl>

      <div>
        <p className="mb-1 text-xs text-ink-600">Evidence</p>
        <pre className="max-h-64 overflow-auto rounded border border-base-600 bg-base-900 p-3 font-mono text-xs text-ink-300">
          {JSON.stringify(alert.evidence, null, 2)}
        </pre>
      </div>

      <div className="flex justify-end gap-2 border-t border-base-600 pt-4">
        <Button variant="secondary" disabled={alert.status === 'Closed'} onClick={onAcknowledge}>
          Acknowledge
        </Button>
        <Button variant="danger" disabled={alert.status === 'Closed'} onClick={onClose}>
          Close Alert
        </Button>
      </div>
    </div>
  )
}
