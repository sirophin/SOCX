import Button from './Button'

export default function Pagination({ total, limit, offset, onOffsetChange }) {
  if (total === 0) return null

  const page = Math.floor(offset / limit) + 1
  const pageCount = Math.max(1, Math.ceil(total / limit))
  const start = total === 0 ? 0 : offset + 1
  const end = Math.min(offset + limit, total)

  return (
    <div className="flex items-center justify-between border-t border-base-600 px-4 py-3 text-xs text-ink-500">
      <span>
        Showing <span className="text-ink-300">{start}–{end}</span> of{' '}
        <span className="text-ink-300">{total}</span>
      </span>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          disabled={offset === 0}
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
        >
          Previous
        </Button>
        <span className="text-ink-600">
          Page {page} of {pageCount}
        </span>
        <Button
          variant="ghost"
          size="sm"
          disabled={offset + limit >= total}
          onClick={() => onOffsetChange(offset + limit)}
        >
          Next
        </Button>
      </div>
    </div>
  )
}
