import { useState } from 'react'
import { Link } from 'react-router-dom'
import { activityApi } from '../../api/endpoints'
import type { AuditEvent } from '../../api/types'
import { DataTable, type Column } from '../../components/DataTable'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { DataState } from '../../components/StateViews'
import { useAsync } from '../../hooks/useAsync'
import { formatDateTime } from '../../utils/date'
import { describeEvent } from '../../utils/events'
import { eventLabel } from '../../utils/labels'

export function Activity() {
  const [page, setPage] = useState(1)
  const { data, error, loading, reload } = useAsync(() => activityApi.list({ page, page_size: 25 }), [page])
  const columns: Column<AuditEvent>[] = [
    { key: 'when', header: 'When', render: (e) => formatDateTime(e.created_at) },
    { key: 'who', header: 'Who', render: (e) => e.actor?.display_name ?? 'System' },
    { key: 'event', header: 'Event', render: (e) => <strong>{eventLabel(e.event_type)}</strong> },
    { key: 'detail', header: 'Details', render: (e) => describeEvent(e) || '-' },
    {
      key: 'ticket',
      header: 'Ticket',
      render: (e) => (e.ticket_id !== null ? <Link to={`/admin/tickets/${e.ticket_id}`}>Open ticket #{e.ticket_id}</Link> : '-'),
    },
  ]
  return (
    <>
      <PageHeader title="Activity" subtitle="Audit trail of ticket and administrative events." />
      <DataState
        loading={loading} error={error} onRetry={reload} hasData={data !== null}
        empty={data !== null && data.total === 0} emptyTitle="No activity recorded yet"
      >
        {data && (
          <>
            <DataTable caption="Activity" columns={columns} rows={data.items} rowKey={(e) => e.id} />
            <Pagination page={data.page} pages={data.pages} total={data.total} pageSize={data.page_size} onPage={setPage} />
          </>
        )}
      </DataState>
    </>
  )
}
