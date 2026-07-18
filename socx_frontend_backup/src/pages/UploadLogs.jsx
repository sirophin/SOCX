import { useEffect, useRef, useState } from 'react'
import { logsApi, UPLOADABLE_SOURCE_TYPES } from '../api/logsApi'
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
import { formatBytes, formatDateTime, titleCase } from '../utils/formatters'

const LIMIT = 20

export default function UploadLogs() {
  const [sourceType, setSourceType] = useState(UPLOADABLE_SOURCE_TYPES[0].value)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadError, setUploadError] = useState('')
  const fileInputRef = useRef(null)

  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState('')

  const [statsLog, setStatsLog] = useState(null)

  function loadLogs() {
    setListLoading(true)
    setListError('')
    logsApi
      .list({ limit: LIMIT, offset })
      .then((data) => {
        setLogs(data.items)
        setTotal(data.total)
      })
      .catch((err) => setListError(getErrorMessage(err, 'Could not load uploaded logs.')))
      .finally(() => setListLoading(false))
  }

  useEffect(() => {
    loadLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset])

  async function handleUpload(e) {
    e.preventDefault()
    if (!file) return

    setUploading(true)
    setUploadError('')
    setUploadProgress(0)
    try {
      await logsApi.upload(file, sourceType, (progressEvent) => {
        if (progressEvent.total) {
          setUploadProgress(Math.round((progressEvent.loaded / progressEvent.total) * 100))
        }
      })
      setFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
      setOffset(0)
      loadLogs()
    } catch (err) {
      setUploadError(getErrorMessage(err, 'Upload failed.'))
    } finally {
      setUploading(false)
    }
  }

  async function handleReparse(logId) {
    try {
      await logsApi.parse(logId, true)
      loadLogs()
    } catch (err) {
      setListError(getErrorMessage(err, 'Re-parse failed.'))
    }
  }

  const selectedSourceMeta = UPLOADABLE_SOURCE_TYPES.find((s) => s.value === sourceType)

  return (
    <div className="flex flex-col gap-6">
      <Card title="Upload a log file">
        <form onSubmit={handleUpload} className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="w-full sm:w-56">
            <Field label="Source type" htmlFor="source_type">
              <Select
                id="source_type"
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                disabled={uploading}
              >
                {UPLOADABLE_SOURCE_TYPES.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </Select>
            </Field>
          </div>

          <div className="flex-1">
            <Field
              label="File"
              htmlFor="file"
              hint={selectedSourceMeta ? `Accepted: ${selectedSourceMeta.extensions}` : undefined}
            >
              <input
                id="file"
                ref={fileInputRef}
                type="file"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                disabled={uploading}
                className="block w-full text-sm text-ink-300 file:mr-3 file:rounded file:border-0 file:bg-base-600 file:px-3 file:py-2 file:text-sm file:font-medium file:text-ink-100 hover:file:bg-base-500"
              />
            </Field>
          </div>

          <Button type="submit" disabled={!file || uploading} className="sm:w-40">
            {uploading ? `Uploading… ${uploadProgress}%` : 'Upload & Parse'}
          </Button>
        </form>

        {uploadError && (
          <div className="mt-4">
            <ErrorBanner message={uploadError} onDismiss={() => setUploadError('')} />
          </div>
        )}

        {uploading && (
          <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-base-600">
            <div
              className="h-full bg-accent-500 transition-[width] duration-150"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        )}

        <p className="mt-4 text-xs text-ink-600">
          Files are parsed automatically right after upload — the table below reflects the final
          parse outcome (completed, partial, or failed) once it's done.
        </p>
      </Card>

      <Card title="Uploaded Logs">
        {listError && (
          <div className="mb-4">
            <ErrorBanner message={listError} onDismiss={() => setListError('')} />
          </div>
        )}

        {listLoading ? (
          <div className="flex justify-center py-10">
            <LoadingSpinner label="Loading logs…" />
          </div>
        ) : logs.length === 0 ? (
          <EmptyState title="No logs uploaded yet" description="Upload a file above to get started." />
        ) : (
          <>
            <Table>
              <THead>
                <TR>
                  <TH>Filename</TH>
                  <TH>Source</TH>
                  <TH>Size</TH>
                  <TH>Uploaded</TH>
                  <TH>Uploaded By</TH>
                  <TH>Parse Status</TH>
                  <TH>Actions</TH>
                </TR>
              </THead>
              <TBody>
                {logs.map((log) => (
                  <TR key={log.id}>
                    <TD className="font-mono text-ink-100">{log.original_filename}</TD>
                    <TD>{titleCase(log.source_type)}</TD>
                    <TD className="table-cell-mono">{formatBytes(log.file_size_bytes)}</TD>
                    <TD>{formatDateTime(log.ingested_at)}</TD>
                    <TD>{log.uploaded_by?.username || '—'}</TD>
                    <TD>
                      <Badge kind="status" value={log.parse_status} />
                    </TD>
                    <TD>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => setStatsLog(log)}
                          className="text-xs text-accent-500 hover:text-accent-400"
                          disabled={!log.parse_stats}
                        >
                          View stats
                        </button>
                        {(log.parse_status === 'failed' || log.parse_status === 'partial') && (
                          <button
                            onClick={() => handleReparse(log.id)}
                            className="text-xs text-ink-500 hover:text-ink-200"
                          >
                            Re-parse
                          </button>
                        )}
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

      {statsLog && (
        <Modal title={`Parse stats — ${statsLog.original_filename}`} onClose={() => setStatsLog(null)}>
          <ParseStatsView log={statsLog} />
        </Modal>
      )}
    </div>
  )
}

function ParseStatsView({ log }) {
  const stats = log.parse_stats
  if (!stats) {
    return <p className="text-sm text-ink-500">No parse statistics available yet.</p>
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatBox label="Total" value={stats.total_rows} />
        <StatBox label="Parsed" value={stats.parsed_rows} accent="text-statuscolor-completed" />
        <StatBox label="Skipped" value={stats.skipped_rows} accent="text-statuscolor-partial" />
        <StatBox label="Failed" value={stats.failed_rows} accent="text-severity-critical" />
      </div>

      {stats.error && (
        <div>
          <p className="mb-1 text-xs font-medium text-ink-500">Error</p>
          <p className="rounded border border-severity-critical/30 bg-severity-critical/10 p-3 font-mono text-xs text-severity-critical">
            {stats.error}
          </p>
        </div>
      )}

      {stats.sample_errors?.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-medium text-ink-500">Sample errors</p>
          <ul className="flex flex-col gap-1.5 rounded border border-base-600 bg-base-900 p-3">
            {stats.sample_errors.map((msg, i) => (
              <li key={i} className="font-mono text-xs text-ink-500">
                {msg}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function StatBox({ label, value, accent = 'text-ink-100' }) {
  return (
    <div className="rounded border border-base-600 bg-base-900 p-3 text-center">
      <p className={`font-display text-xl font-semibold ${accent}`}>{value ?? '—'}</p>
      <p className="mt-0.5 text-xs text-ink-600">{label}</p>
    </div>
  )
}
