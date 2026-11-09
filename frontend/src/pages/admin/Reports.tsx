import { useState, type FormEvent } from 'react'
import { apiUrl } from '../../api/client'
import { reportsApi } from '../../api/endpoints'
import { BarList } from '../../components/BarList'
import { FormField } from '../../components/FormField'
import { PageHeader } from '../../components/PageHeader'
import { DataState } from '../../components/StateViews'
import { useAsync } from '../../hooks/useAsync'

export function Reports() {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [applied, setApplied] = useState({ from: '', to: '' })
  const [rangeError, setRangeError] = useState<string | null>(null)
  const { data, error, loading, reload } = useAsync(
    () => reportsApi.tickets({ date_from: applied.from || undefined, date_to: applied.to || undefined }),
    [applied.from, applied.to],
  )

  function apply(e: FormEvent) {
    e.preventDefault()
    if (from && to && from > to) {
      setRangeError('The start date must not be after the end date.')
      return
    }
    setRangeError(null)
    setApplied({ from, to })
  }

  function clear() {
    setFrom('')
    setTo('')
    setRangeError(null)
    setApplied({ from: '', to: '' })
  }

  const csv = apiUrl('/api/v1/tickets/export.csv', {
    created_from: applied.from || undefined,
    created_to: applied.to || undefined,
  })

  return (
    <>
      <PageHeader
        title="Reports"
        subtitle="Ticket counts by status, category, priority and assignee."
        actions={<a className="btn" href={csv}>Download CSV</a>}
      />
      <form className="filters" onSubmit={apply} noValidate aria-label="Report date range">
        <FormField label="Created from">{(c) => <input {...c} type="date" value={from} onChange={(e) => setFrom(e.target.value)} />}</FormField>
        <FormField label="Created to" error={rangeError}>{(c) => <input {...c} type="date" value={to} onChange={(e) => setTo(e.target.value)} />}</FormField>
        <div className="button-row filters-actions">
          <button type="submit" className="btn btn-primary">Apply range</button>
          <button type="button" className="btn" onClick={clear}>Clear</button>
        </div>
      </form>
      <DataState loading={loading} error={error} onRetry={reload} hasData={data !== null}>
        {data && (
          <>
            <p className="report-total">
              <strong>{data.total}</strong> tickets
              {data.date_from || data.date_to ? ` created ${data.date_from ?? 'from the start'} to ${data.date_to ?? 'today'}` : ' in total'}
            </p>
            <div className="grid-2">
              <BarList title="By status" items={data.by_status} toneClass={(k) => `status-${k}`} />
              <BarList title="By priority" items={data.by_priority} toneClass={(k) => `priority-${k}`} />
              <BarList title="By category" items={data.by_category} />
              <BarList title="By assignee" items={data.by_assignee} />
            </div>
          </>
        )}
      </DataState>
    </>
  )
}
