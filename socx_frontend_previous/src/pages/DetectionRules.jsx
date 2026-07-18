import { useEffect, useState } from 'react'
import { detectionRulesApi } from '../api/detectionRulesApi'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../hooks/useAuth'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import { Field, Input, Select, Textarea, Checkbox } from '../components/common/Field'
import ErrorBanner from '../components/common/ErrorBanner'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'
import Modal from '../components/common/Modal'
import Pagination from '../components/common/Pagination'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { Table, THead, TBody, TR, TH, TD } from '../components/common/Table'
import { SEVERITIES, RULE_MANAGER_ROLES } from '../utils/constants'

const LIMIT = 20

const EMPTY_FORM = {
  name: '',
  description: '',
  enabled: true,
  severity: 'medium',
  event_id: '',
  username: '',
  source_ip: '',
  process_name: '',
  command_contains: '',
}

export default function DetectionRules() {
  const { user } = useAuth()
  const canManage = RULE_MANAGER_ROLES.includes(user?.role)

  const [rules, setRules] = useState([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [editing, setEditing] = useState(null) // null = closed, {} = create, {...rule} = edit
  const [deleting, setDeleting] = useState(null)

  function load() {
    setLoading(true)
    setError('')
    detectionRulesApi
      .list({ limit: LIMIT, offset })
      .then((data) => {
        setRules(data.items)
        setTotal(data.total)
      })
      .catch((err) => setError(getErrorMessage(err, 'Could not load detection rules.')))
      .finally(() => setLoading(false))
  }

  useEffect(load, [offset])

  return (
    <div className="flex flex-col gap-6">
      <Card
        title="Detection Rules"
        subtitle={`${total} rule${total === 1 ? '' : 's'}`}
        action={
          canManage && (
            <Button size="sm" onClick={() => setEditing({ ...EMPTY_FORM })}>
              New Rule
            </Button>
          )
        }
      >
        {error && (
          <div className="mb-4">
            <ErrorBanner message={error} onDismiss={() => setError('')} />
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-10">
            <LoadingSpinner label="Loading rules…" />
          </div>
        ) : rules.length === 0 ? (
          <EmptyState
            title="No detection rules yet"
            description={
              canManage
                ? 'Create a rule to start matching incoming log entries.'
                : 'Ask an Admin or Tier 2 Analyst to create detection rules.'
            }
          />
        ) : (
          <>
            <Table>
              <THead>
                <TR>
                  <TH>Name</TH>
                  <TH>Severity</TH>
                  <TH>Conditions</TH>
                  <TH>Enabled</TH>
                  {canManage && <TH>Actions</TH>}
                </TR>
              </THead>
              <TBody>
                {rules.map((rule) => (
                  <TR key={rule.id}>
                    <TD className="text-ink-100">
                      {rule.name}
                      {rule.description && (
                        <p className="mt-0.5 max-w-xs truncate text-xs text-ink-600">
                          {rule.description}
                        </p>
                      )}
                    </TD>
                    <TD>
                      <Badge kind="severity" value={rule.severity} />
                    </TD>
                    <TD>
                      <RuleConditions rule={rule} />
                    </TD>
                    <TD>
                      {rule.enabled ? (
                        <span className="text-xs text-statuscolor-completed">Enabled</span>
                      ) : (
                        <span className="text-xs text-ink-600">Disabled</span>
                      )}
                    </TD>
                    {canManage && (
                      <TD>
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => setEditing(rule)}
                            className="text-xs text-accent-500 hover:text-accent-400"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setDeleting(rule)}
                            className="text-xs text-severity-critical hover:text-severity-critical/80"
                          >
                            Delete
                          </button>
                        </div>
                      </TD>
                    )}
                  </TR>
                ))}
              </TBody>
            </Table>
            <Pagination total={total} limit={LIMIT} offset={offset} onOffsetChange={setOffset} />
          </>
        )}
      </Card>

      {editing && (
        <RuleFormModal
          initial={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            load()
          }}
        />
      )}

      {deleting && (
        <Modal
          title="Delete detection rule"
          onClose={() => setDeleting(null)}
          footer={
            <>
              <Button variant="secondary" onClick={() => setDeleting(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={async () => {
                  await detectionRulesApi.remove(deleting.id)
                  setDeleting(null)
                  load()
                }}
              >
                Delete
              </Button>
            </>
          }
        >
          <p className="text-sm text-ink-300">
            Delete <span className="font-medium text-ink-100">{deleting.name}</span>? This cannot
            be undone.
          </p>
        </Modal>
      )}
    </div>
  )
}

function RuleConditions({ rule }) {
  const conditions = [
    rule.event_id && `event_id = ${rule.event_id}`,
    rule.username && `username = ${rule.username}`,
    rule.source_ip && `source_ip = ${rule.source_ip}`,
    rule.process_name && `process_name = ${rule.process_name}`,
    rule.command_contains && `command contains "${rule.command_contains}"`,
  ].filter(Boolean)

  if (conditions.length === 0) {
    return <span className="text-xs text-ink-700">No conditions set</span>
  }

  return (
    <div className="flex flex-col gap-0.5">
      {conditions.map((c) => (
        <span key={c} className="font-mono text-xs text-ink-500">
          {c}
        </span>
      ))}
    </div>
  )
}

function RuleFormModal({ initial, onClose, onSaved }) {
  const isEdit = Boolean(initial.id)
  const [form, setForm] = useState({
    name: initial.name ?? '',
    description: initial.description ?? '',
    enabled: initial.enabled ?? true,
    severity: initial.severity ?? 'medium',
    event_id: initial.event_id ?? '',
    username: initial.username ?? '',
    source_ip: initial.source_ip ?? '',
    process_name: initial.process_name ?? '',
    command_contains: initial.command_contains ?? '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    setError('')

    // Empty strings mean "no condition" — send null so the backend treats
    // the field as unset rather than an empty-string match.
    const payload = {
      ...form,
      event_id: form.event_id || null,
      username: form.username || null,
      source_ip: form.source_ip || null,
      process_name: form.process_name || null,
      command_contains: form.command_contains || null,
      description: form.description || null,
    }

    try {
      if (isEdit) {
        await detectionRulesApi.update(initial.id, payload)
      } else {
        await detectionRulesApi.create(payload)
      }
      onSaved()
    } catch (err) {
      setError(getErrorMessage(err, 'Could not save the rule.'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      title={isEdit ? 'Edit Detection Rule' : 'New Detection Rule'}
      onClose={onClose}
      width="max-w-xl"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={saving}>
            {saving ? 'Saving…' : 'Save Rule'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && <ErrorBanner message={error} onDismiss={() => setError('')} />}

        <Field label="Name" htmlFor="name">
          <Input
            id="name"
            value={form.name}
            onChange={(e) => update('name', e.target.value)}
            required
            maxLength={150}
          />
        </Field>

        <Field label="Description" htmlFor="description">
          <Textarea
            id="description"
            value={form.description}
            onChange={(e) => update('description', e.target.value)}
            placeholder="What does this rule detect, and why does it matter?"
          />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Severity" htmlFor="severity">
            <Select
              id="severity"
              value={form.severity}
              onChange={(e) => update('severity', e.target.value)}
            >
              {SEVERITIES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </Field>
          <div className="flex items-end pb-2">
            <Checkbox
              label="Enabled"
              checked={form.enabled}
              onChange={(e) => update('enabled', e.target.checked)}
            />
          </div>
        </div>

        <div className="border-t border-base-600 pt-4">
          <p className="mb-3 text-xs font-medium text-ink-500">
            Match conditions — leave blank to not filter on that field. All set conditions must
            match (AND). A rule with no conditions set will never match any log entry.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <Field label="Event ID" htmlFor="event_id">
              <Input
                id="event_id"
                value={form.event_id}
                onChange={(e) => update('event_id', e.target.value)}
                placeholder="4625"
              />
            </Field>
            <Field label="Username" htmlFor="username">
              <Input
                id="username"
                value={form.username}
                onChange={(e) => update('username', e.target.value)}
                placeholder="admin"
              />
            </Field>
            <Field label="Source IP" htmlFor="source_ip">
              <Input
                id="source_ip"
                value={form.source_ip}
                onChange={(e) => update('source_ip', e.target.value)}
                placeholder="203.0.113.5"
              />
            </Field>
            <Field label="Process Name" htmlFor="process_name">
              <Input
                id="process_name"
                value={form.process_name}
                onChange={(e) => update('process_name', e.target.value)}
                placeholder="powershell.exe"
              />
            </Field>
          </div>
          <div className="mt-4">
            <Field label="Command contains" htmlFor="command_contains">
              <Input
                id="command_contains"
                value={form.command_contains}
                onChange={(e) => update('command_contains', e.target.value)}
                placeholder="-enc"
              />
            </Field>
          </div>
        </div>
      </form>
    </Modal>
  )
}
