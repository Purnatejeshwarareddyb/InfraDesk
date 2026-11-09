import { Link } from 'react-router-dom'
import type { Role } from '../api/types'
import { homePath } from '../auth/authContext'
import { useUnread } from './unread'

export function NotificationBell({ role }: { role: Role }) {
  const { unread } = useUnread()
  const to = `${homePath(role)}/notifications`
  return (
    <Link
      to={to}
      className="bell"
      aria-label={unread > 0 ? `Notifications, ${unread} unread` : 'Notifications, none unread'}
    >
      <span>Notifications</span>
      <span className={unread > 0 ? 'bell-count bell-count-active' : 'bell-count'} aria-hidden="true">
        {unread > 99 ? '99+' : unread}
      </span>
    </Link>
  )
}
