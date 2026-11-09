import { useState } from 'react'
import { Link } from 'react-router-dom'
import { errorMessage } from '../../api/client'
import { notificationsApi } from '../../api/endpoints'
import { Chip } from '../../components/Badges'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { DataState } from '../../components/StateViews'
import { useToast } from '../../components/Toast'
import { useUnread } from '../../components/unread'
import { useAsync } from '../../hooks/useAsync'
import { formatDateTime } from '../../utils/date'

const PAGE_SIZE = 20

export function Notifications({ admin }: { admin: boolean }) {
  const base = admin ? '/admin' : '/worker'
  const toast = useToast()
  const { refresh } = useUnread()
  const [page, setPage] = useState(1)
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [busyId, setBusyId] = useState<number | 'all' | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const { data, error, loading, reload } = useAsync(
    () => notificationsApi.list({ page, page_size: PAGE_SIZE, unread_only: unreadOnly }),
    [page, unreadOnly],
  )

  async function markOne(id: number) {
    setBusyId(id)
    setActionError(null)
    try {
      await notificationsApi.markRead(id)
      reload()
      refresh()
    } catch (err) {
      setActionError(errorMessage(err))
    } finally {
      setBusyId(null)
    }
  }

  async function markAll() {
    setBusyId('all')
    setActionError(null)
    try {
      await notificationsApi.markAllRead()
      toast.success('All notifications marked as read.')
      reload()
      refresh()
    } catch (err) {
      setActionError(errorMessage(err))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <PageHeader
        title="Notifications"
        subtitle={data ? `${data.unread_count} unread` : undefined}
        actions={
          <button type="button" className="btn" onClick={markAll} disabled={busyId !== null || !data || data.unread_count === 0}>
            {busyId === 'all' ? 'Marking...' : 'Mark all as read'}
          </button>
        }
      />
      <div className="filters">
        <label className="check">
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={(e) => {
              setUnreadOnly(e.target.checked)
              setPage(1)
            }}
          />
          Show unread only
        </label>
      </div>
      {actionError && <p className="form-error" role="alert">{actionError}</p>}
      <DataState
        loading={loading}
        error={error}
        onRetry={reload}
        hasData={data !== null}
        empty={data !== null && data.total === 0}
        emptyTitle={unreadOnly ? 'No unread notifications' : 'No notifications yet'}
        emptyHint="Updates about your tickets will appear here."
      >
        {data && (
          <>
            <ul className="notifications">
              {data.items.map((n) => (
                <li key={n.id} className={n.read_at ? 'notification' : 'notification notification-unread'}>
                  <div className="notification-text">
                    <p>{n.message}</p>
                    <p className="muted small">
                      <time dateTime={n.created_at}>{formatDateTime(n.created_at)}</time>
                      {n.ticket_id !== null && (
                        <>
                          {' '}
                          <Link to={`${base}/tickets/${n.ticket_id}`}>Open ticket</Link>
                        </>
                      )}
                    </p>
                  </div>
                  <div className="notification-actions">
                    {n.read_at ? (
                      <Chip tone="muted">Read</Chip>
                    ) : (
                      <button type="button" className="btn btn-small" disabled={busyId !== null} onClick={() => markOne(n.id)}>
                        {busyId === n.id ? 'Marking...' : 'Mark as read'}
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
            <Pagination page={data.page} pages={data.pages} total={data.total} pageSize={data.page_size} onPage={setPage} />
          </>
        )}
      </DataState>
    </>
  )
}
