export function Table({ children }) {
  return (
    <div className="overflow-x-auto rounded-md border border-base-600">
      <table className="w-full border-collapse text-left text-sm">{children}</table>
    </div>
  )
}

export function THead({ children }) {
  return <thead className="border-b border-base-600 bg-base-700/60">{children}</thead>
}

export function TBody({ children }) {
  return <tbody className="divide-y divide-base-600/70">{children}</tbody>
}

export function TR({ children, onClick, className = '' }) {
  return (
    <tr
      onClick={onClick}
      className={`${onClick ? 'cursor-pointer hover:bg-base-700/50' : ''} transition-colors duration-150 ${className}`}
    >
      {children}
    </tr>
  )
}

export function TH({ children, className = '' }) {
  return (
    <th
      className={`whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wide text-ink-600 ${className}`}
    >
      {children}
    </th>
  )
}

export function TD({ children, className = '' }) {
  return <td className={`px-4 py-3 align-middle text-ink-300 ${className}`}>{children}</td>
}
