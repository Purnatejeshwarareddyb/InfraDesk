import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiUrl } from '../../api/client'
import { ticketsApi, usersApi } from '../../api/endpoints'
import {
  CATEGORIES, PRIORITIES, SORTS, STATUSES,
  type Category, type Priority, type Ticket, type TicketSort, type TicketStatus,
} from '../../api/types'
import { PriorityBadge, StatusBadge } from '../../components/Badges'
import { DataTable, type Column } from '../../components/DataTable'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { DataState } from '../../components/StateViews'
import { useAsync } from '../../hooks/useAsync'
import { useDebounced } from '../../hooks/useDebounced'
import { useQueryState } from '../../hooks/useQueryState'
import { formatDateTime } from '../../utils/date'
import { CATEGORY_LABEL, PRIORITY_LABEL, STATUS_LABEL } from '../../utils/labels'

const PAGE_SIZE = 20
const SORT_LABEL: Record<TicketSort, string> = {
  newest: 'Newest first',
  oldest: 'Oldest first',
  updated: 'Recently updated',
  priority: 'Highest priority',
}

export function TicketList({ admin }: { admin: boolean }) {
  const base = admin ? '/admin' : '/worker'
  const [f, update] = useQueryState({
    q: '', status: '', priority: '', category: '', assignee_id: '', sort: 'newest', page: '1',
  })
  const [search, setSearch] = useState(f.q ?? '')
  const debounced = useDebounced(search)
  useEffect(() => {
    if (debounced !== f.q) update({ q: debounced })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced])

  const page = Math.max(1, Number(f.page) || 1)
  const filters = {
    q: f.q, status: f.status as TicketStatus | '', priority: f.priority as Priority | '',
    category: f.category as Category | '', assignee_id: f.assignee_id, sort: f.sort as TicketSort,
  }
  const key = JSON.stringify([filters, page])
  const list = useAsync((signal) => ticketsApi.list({ ...filters, page, page_size: PAGE_SIZE }, signal), [key])
  const workers = useAsync(
    () => (admin ? usersApi.list({ active: true, page_size: 100 }) : Promise.resolve(null)),
    [admin],
  )

  const columns: Column<Ticket>[] = [
    {
      key: 'ticket',
      header: 'Ticket',
      render: (t) => (
        <>
          <Link to={`${base}/tickets/${t.id}`} className="ticket-link">
            <span className="mono">{t.ticket_number}</span> {t.title}
          </Link>
        </>
      ),
    },
    { key: 'status', header: 'Status', render: (t) => <StatusBadge status={t.status} /> },
    { key: 'priority', header: 'Priority', render: (t) => <PriorityBadge priority={t.priority} /> },
    { key: 'category', header: 'Category', render: (t) => CATEGORY_LABEL[t.category] },
    { key: 'reporter', header: 'Reported by', render: (t) => t.reporter.display_name },
    { key: 'assignee', header: 'Assigned to', render: (t) => t.assignee?.display_name ?? 'Unassigned' },
    { key: 'updated', header: 'Updated', render: (t) => formatDateTime(t.updated_at) },
  ]

  const csvHref = apiUrl('/api/v1/tickets/export.csv', { ...filters })

  return (
    <>
      <PageHeader
        title={admin ? 'Tickets' : 'My tickets'}
        subtitle={admin ? 'Every ticket in the help desk.' : 'Tickets you reported or are assigned to.'}
        actions={
          <>
            {admin && (
              <a className="btn" href={csvHref}>
                Download CSV
              </a>
            )}
            <Link className="btn btn-primary" to={`${base}/tickets/new`}>
              Create ticket
            </Link>
          </>
        }
      />
      <form className="filters" role="search" aria-label="Filter tickets" onSubmit={(e) => e.preventDefault()}>
        <div className="field field-grow">
          <label htmlFor="t-search">Search</label>
          <input
            id="t-search"
            type="search"
            placeholder="Ticket number, title or person"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            maxLength={80}
          />
        </div>
        <div className="field">
          <label htmlFor="t-status">Status</label>
          <select id="t-status" value={f.status} onChange={(e) => update({ status: e.target.value })}>
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="t-priority">Priority</label>
          <select id="t-priority" value={f.priority} onChange={(e) => update({ priority: e.target.value })}>
            <option value="">All priorities</option>
            {PRIORITIES.map((p) => <option key={p} value={p}>{PRIORITY_LABEL[p]}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="t-category">Category</label>
          <select id="t-category" value={f.category} onChange={(e) => update({ category: e.target.value })}>
            <option value="">All categories</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{CATEGORY_LABEL[c]}</option>)}
          </select>
        </div>
        {admin && (
          <div className="field">
            <label htmlFor="t-assignee">Assignee</label>
            <select id="t-assignee" value={f.assignee_id} onChange={(e) => update({ assignee_id: e.target.value })}>
              <option value="">Anyone</option>
              {workers.data?.items.map((u) => <option key={u.id} value={u.id}>{u.display_name}</option>)}
            </select>
          </div>
        )}
        <div className="field">
          <label htmlFor="t-sort">Sort</label>
          <select id="t-sort" value={f.sort} onChange={(e) => update({ sort: e.target.value })}>
            {SORTS.map((s) => <option key={s} value={s}>{SORT_LABEL[s]}</option>)}
          </select>
        </div>
      </form>

      <DataState
        loading={list.loading}
        error={list.error}
        onRetry={list.reload}
        hasData={list.data !== null}
        empty={list.data !== null && list.data.total === 0}
        emptyTitle="No tickets match"
        emptyHint="Clear a filter or create a new ticket."
      >
        {list.data && (
          <>
            <DataTable
              caption="Tickets"
              columns={columns}
              rows={list.data.items}
              rowKey={(t) => t.id}
              rowClass={(t) => `led led-${t.priority}`}
            />
            <Pagination
              page={list.data.page}
              pages={list.data.pages}
              total={list.data.total}
              pageSize={list.data.page_size}
              onPage={(p) => update({ page: String(p) }, false)}
            />
          </>
        )}
      </DataState>
    </>
  )
}
