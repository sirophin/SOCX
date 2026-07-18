import { useEffect, useState } from 'react'
import { investigationApi } from '../api/investigationApi'
import { getErrorMessage } from '../api/client'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import { Field, Input, Select } from '../components/common/Field'
import ErrorBanner from '../components/common/ErrorBanner'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'
import Modal from '../components/common/Modal'
import Pagination from '../components/common/Pagination'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { Table, THead, TBody, TR, TH, TD } from '../components/common/Table'
import { formatDateTime } from '../utils/formatters'
import { SEVERITIES } from '../utils/constants'

const LIMIT = 25
const EMPTY_FILTERS = {
  username: '',
  sourceIp: '',
  hostname: '',
  eventId: '',
  severity: '',
  timestampFrom: '',
  timestampTo: '',
}

export default function Investigation() {
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [appliedFilters, setAppliedFilters] = useState(EMPTY_FILTERS)
  const [offset, setOffset] = useState(0)

  const [entries, setEntries] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError('')
    investigationApi
      .list({ ...appliedFilters, limit: LIMIT, offset })
      .then((data) => {
        setEntries(data.items)
        setTotal(data.total)
      })
      .catch((err) => setError(getErrorMessage(err, 'Could not load log entries.')))
      .finally(() => setLoading(false))
  }, [appliedFilters, offset])

  function handleFilterSubmit(e) {
    e.preventDefault()
    setOffset(0)
    setAppliedFilters(filters)
  }

  function handleClear() {
    setFilters(EMPTY_FILTERS)
    setAppliedFilters(EMPTY_FILTERS)
    setOffset(0)
  }

  return (
    <div className="flex flex-col gap-6">
      <Card title="Filters">
        <form onSubmit={handleFilterSubmit} className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Field label="Username">
            <Input
              value={filters.username}
              onChange={(e) => setFilters({ ...filters, username: e.target.value })}
              placeholder="alice"
            />
          </Field>
          <Field label="Source IP">
            <Input
              value={filters.sourceIp}
              onChange={(e) => setFilters({ ...filters, sourceIp: e.target.value })}
              placeholder="203.0.113.5"
            />
          </Field>
          <Field label="Hostname">
            <Input
              value={filters.hostname}
              onChange={(e) => setFilters({ ...filters, hostname: e.target.value })}
              placeholder="WIN-DC01"
            />
          </Field>
          <Field label="Event ID">
            <Input
              value={filters.eventId}
              onChange={(e) => setFilters({ ...filters, eventId: e.target.value })}
              placeholder="4625"
            />
          </Field>
          <Field label="Severity">
            <Select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
            >
              <option value="">Any</option>
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="From">
            <Input
              type="datetime-local"
              value={filters.timestampFrom}
              onChange={(e) => setFilters({ ...filters, timestampFrom: e.target.value })}
            />
          </Field>
          <Field label="To">
            <Input
              type="datetime-local"
              value={filters.timestampTo}
              onChange={(e) => setFilters({ ...filters, timestampTo: e.target.value })}
            />
          </Field>
          <div className="flex items-end gap-2">
            <Button type="submit" className="flex-1">
              Apply
            </Button>
            <Button type="button" variant="secondary" onClick={handleClear}>
              Clear
            </Button>
          </div>
        </form>
      </Card>

      <Card title="Normalized Log Entries" subtitle={`${total.toLocaleString()} matching entries`}>
        {error && (
          <div className="mb-4">
            <ErrorBanner message={error} onDismiss={() => setError('')} />
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-10">
            <LoadingSpinner label="Searching…" />
          </div>
        ) : entries.length === 0 ? (
          <EmptyState
            title="No matching entries"
            description="Try widening your filters, or confirm logs have finished parsing."
          />
        ) : (
          <>
            <Table>
              <THead>
                <TR>
                  <TH>Timestamp</TH>
                  <TH>Severity</TH>
                  <TH>Event ID</TH>
                  <TH>Hostname</TH>
                  <TH>Username</TH>
                  <TH>Source IP</TH>
                  <TH>Process</TH>
                </TR>
              </THead>
              <TBody>
                {entries.map((entry) => (
                  <TR key={entry.id} onClick={() => setSelected(entry)}>
                    <TD className="table-cell-mono whitespace-nowrap">
                      {formatDateTime(entry.timestamp)}
                    </TD>
                    <TD>
                      <Badge kind="severity" value={entry.severity} />
                    </TD>
                    <TD className="table-cell-mono">{entry.event_id || '—'}</TD>
                    <TD>{entry.hostname || '—'}</TD>
                    <TD>{entry.username || '—'}</TD>
                    <TD className="table-cell-mono">{entry.source_ip || '—'}</TD>
                    <TD className="table-cell-mono">{entry.process_name || '—'}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
            <Pagination total={total} limit={LIMIT} offset={offset} onOffsetChange={setOffset} />
          </>
        )}
      </Card>

      {selected && (
        <Modal title="Log Entry Detail" onClose={() => setSelected(null)} width="max-w-2xl">
          <EntryDetail entry={selected} />
        </Modal>
      )}
    </div>
  )
}

function EntryDetail({ entry }) {
  const fields = [
    ['Timestamp', formatDateTime(entry.timestamp)],
    ['Event ID', entry.event_id],
    ['Hostname', entry.hostname],
    ['Username', entry.username],
    ['Process Name', entry.process_name],
    ['Source IP', entry.source_ip],
    ['Destination IP', entry.destination_ip],
    ['Status', entry.status],
    ['Command Line', entry.command_line],
  ]

  return (
    <div className="flex flex-col gap-4">
      <dl className="grid grid-cols-2 gap-x-6 gap-y-3">
        {fields.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs text-ink-600">{label}</dt>
            <dd className="mt-0.5 break-all font-mono text-sm text-ink-100">{value || '—'}</dd>
          </div>
        ))}
      </dl>
      <div>
        <p className="mb-1 text-xs text-ink-600">Raw Fields</p>
        <pre className="max-h-64 overflow-auto rounded border border-base-600 bg-base-900 p-3 font-mono text-xs text-ink-300">
          {JSON.stringify(entry.raw_fields, null, 2)}
        </pre>
      </div>
    </div>
  )
}
