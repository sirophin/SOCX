import { Field, Input, Select } from '../common/Field'

export default function DatasetFilters({
  search,
  onSearchChange,
  category,
  onCategoryChange,
  categories,
  resultCount,
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex flex-1 flex-col gap-4 sm:flex-row">
        <div className="flex-1">
          <Field label="Search">
            <Input
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search by dataset name…"
            />
          </Field>
        </div>
        <div className="w-full sm:w-56">
          <Field label="Category">
            <Select value={category} onChange={(e) => onCategoryChange(e.target.value)}>
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </Select>
          </Field>
        </div>
      </div>
      <p className="whitespace-nowrap pb-2 text-xs text-ink-600 sm:pb-2.5">
        {resultCount} dataset{resultCount === 1 ? '' : 's'}
      </p>
    </div>
  )
}
