import DatasetCard from './DatasetCard'

export default function CategorySection({ category, datasets }) {
  if (datasets.length === 0) return null

  return (
    <section>
      <div className="mb-3 flex items-baseline gap-2">
        <h2 className="font-display text-base font-semibold text-ink-100">{category}</h2>
        <span className="text-xs text-ink-600">
          {datasets.length} dataset{datasets.length === 1 ? '' : 's'}
        </span>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {datasets.map((dataset) => (
          <DatasetCard key={dataset.id} dataset={dataset} />
        ))}
      </div>
    </section>
  )
}
