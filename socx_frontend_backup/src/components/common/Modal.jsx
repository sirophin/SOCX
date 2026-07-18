import { useEffect } from 'react'

export default function Modal({ title, onClose, children, footer, width = 'max-w-lg' }) {
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div
        className={`w-full ${width} rounded-md border border-base-600 bg-base-800 shadow-panel`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="flex items-center justify-between border-b border-base-600 px-5 py-4">
          <h3 className="text-sm font-semibold text-ink-100">{title}</h3>
          <button
            onClick={onClose}
            className="text-ink-500 transition-colors duration-150 hover:text-ink-100"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">{children}</div>
        {footer && (
          <div className="flex items-center justify-end gap-2 border-t border-base-600 px-5 py-4">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
