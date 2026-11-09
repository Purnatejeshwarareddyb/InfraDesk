import { Link } from 'react-router-dom'
import { reportsApi } from '../../api/endpoints'
import { useAsync } from '../../hooks/useAsync'
import { BarList } from '../../components/BarList'
import { DataState } from '../../components/StateViews'
import { EventList } from '../../components/EventList'
import { PageHeader } from '../../components/PageHeader'
import { StatCard } from '../../components/StatCard'
import { useAuth } from '../../auth/authContext'

export function Dashboard({ admin }: { admin: boolean }) {
  const { user } = useAuth()
  const base = admin ? '/admin' : '/worker'
  const { data, error, loading, reload } = useAsync(() => reportsApi.summary(), [])

  return (
    <>
      <PageHeader
        title={admin ? 'Dashboard' : 'My dashboard'}
        subtitle={
          admin
            ? 'Live counts across every ticket.'
            : `Tickets you reported or are working on${user ? `, ${user.display_name}` : ''}.`
        }
        actions={
          <Link className="btn btn-primary" to={`${base}/tickets/new`}>
            Create ticket
          </Link>
        }
      />
      <DataState loading={loading} error={error} onRetry={reload} hasData={data !== null}>
        {data && (
          <>
            <dl className="stats">
              <StatCard label="Total tickets" value={data.total} />
              <StatCard label="Open" value={data.open} hint="Open or assigned" />
              <StatCard label="In progress" value={data.in_progress} hint="Working or waiting" />
              <StatCard label="Resolved" value={data.resolved} hint="Resolved or closed" />
              <StatCard label="High and urgent" value={data.high_priority_active} hint="Still active" />
            </dl>
            <div className="grid-2">
              <BarList title="Tickets by status" items={data.by_status} toneClass={(k) => `status-${k}`} />
              <BarList title="Tickets by priority" items={data.by_priority} toneClass={(k) => `priority-${k}`} />
            </div>
            <section className="panel" aria-label="Recent activity">
              <h2 className="panel-title">Recent activity</h2>
              {data.recent_activity.length === 0 ? (
                <p className="muted">No activity yet.</p>
              ) : (
                <EventList events={data.recent_activity} ticketBase={base} showTicketLink />
              )}
            </section>
          </>
        )}
      </DataState>
    </>
  )
}
