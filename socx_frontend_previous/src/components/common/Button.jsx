const VARIANTS = {
  primary: 'bg-accent-600 text-white hover:bg-accent-700 disabled:bg-accent-600/40',
  secondary:
    'bg-base-700 text-ink-100 border border-base-500 hover:bg-base-600 disabled:opacity-40',
  ghost: 'text-ink-300 hover:bg-base-700 hover:text-ink-100 disabled:opacity-40',
  danger: 'bg-severity-critical/90 text-white hover:bg-severity-critical disabled:opacity-40',
}

const SIZES = {
  sm: 'px-2.5 py-1.5 text-xs',
  md: 'px-3.5 py-2 text-sm',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  children,
  ...props
}) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded font-medium transition-colors duration-150 disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
