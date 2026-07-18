import { useMemo, useState } from 'react'
import { CATEGORIES, SAMPLE_DATASETS } from '../data/sampleDatasets'
import DatasetFilters from '../components/datasets/DatasetFilters'
import CategorySection from '../components/datasets/CategorySection'
import EmptyState from '../components/common/EmptyState'

/**
 * Sample Datasets — browse and download curated sample log files for
 * testing/training against SOCX (Upload Logs, Detection Rules, etc).
 *
 * Frontend-only for now: the catalog is static data (src/data/
 * sampleDatasets.js) and Download links point directly at static files
 * in /public/sample-datasets/ — no backend endpoint exists for this
 * feature yet. "Import" is disabled everywhere for the same reason.
 */
export default function SampleDatasets() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase()
    return SAMPLE_DATASETS.filter((dataset) => {
      const matchesSearch = !query || dataset.name.toLowerCase().includes(query)
      const matchesCategory = !category || dataset.category === category
      return matchesSearch && matchesCategory
    })
  }, [search, category])

  const byCategory = useMemo(() => {
    const map = new Map(CATEGORIES.map((c) => [c, []]))
    for (const dataset of filtered) {
      map.get(dataset.category)?.push(dataset)
    }
    return map
  }, [filtered])

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-md border border-base-600 bg-base-800 p-5 shadow-panel">
        <DatasetFilters
          search={search}
          onSearchChange={setSearch}
          category={category}
          onCategoryChange={setCategory}
          categories={CATEGORIES}
          resultCount={filtered.length}
        />
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          title="No datasets match your filters"
          description="Try a different search term or clear the category filter."
        />
      ) : (
        <div className="flex flex-col gap-8">
          {CATEGORIES.map((cat) => (
            <CategorySection key={cat} category={cat} datasets={byCategory.get(cat) || []} />
          ))}
        </div>
      )}
    </div>
  )
}
