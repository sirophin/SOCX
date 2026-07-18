import Badge from '../common/Badge'
import Button from '../common/Button'

/**
 * One dataset's card. Download is a real anchor pointing at the static
 * file in /public/sample-datasets/ (see src/data/sampleDatasets.js for
 * why these work with no backend yet). Import is disabled everywhere —
 * there's no import endpoint yet, so it's honestly labeled rather than
 * wired to do nothing silently.
 */
export default function DatasetCard({ dataset }) {
  return (
    <div className="flex flex-col rounded-md border border-base-600 bg-base-800 p-5 shadow-panel">
      <div className="flex items-start justify-between gap-3">
        <h4 className="text-sm font-semibold leading-snug text-ink-100">{dataset.name}</h4>
        <Badge kind="difficulty" value={dataset.difficulty} />
      </div>

      <p className="mt-2 flex-1 text-xs leading-relaxed text-ink-500">{dataset.description}</p>

      <dl className="mt-4 grid grid-cols-3 gap-3 border-t border-base-600 pt-3">
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-ink-700">Expected Alerts</dt>
          <dd className="mt-0.5 text-sm text-ink-100">{dataset.expectedAlerts}</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-ink-700">File Size</dt>
          <dd className="mt-0.5 font-mono text-sm text-ink-100">{dataset.fileSize}</dd>
        </div>
        <div>
          <dt className="text-[11px] uppercase tracking-wide text-ink-700">Format</dt>
          <dd className="mt-0.5 text-sm text-ink-100">{dataset.format}</dd>
        </div>
      </dl>

      <div className="mt-4 flex items-center gap-2">
        <a
          href={`/sample-datasets/${dataset.fileName}`}
          download
          className="flex-1"
        >
          <Button variant="primary" size="sm" className="w-full">
            Download
          </Button>
        </a>
        <Button
          variant="secondary"
          size="sm"
          disabled
          title="Importing sample datasets directly into SOCX isn't available yet"
          className="flex-1"
        >
          Import (Coming Soon)
        </Button>
      </div>
    </div>
  )
}
