import { Link } from 'react-router-dom'
import type { AuditEvent } from '../api/types'
import { formatDateTime } from '../utils/date'
import { describeEvent } from '../utils/events'
import { eventLabel } from '../utils/labels'

interface Props {
  events: AuditEvent[]
  ticketBase?: string
  showTicketLink?: boolean
}

/** A vertical timeline: the rail and dots are CSS only. */
export function EventList({ events, ticketBase, showTicketLink }: Props) {
  return (
    <ol className="timeline">
      {events.map((e) => (
        <li key={e.id} className="timeline-item">
          <div className="timeline-head">
            <strong>{eventLabel(e.event_type)}</strong>
            <span className="muted">
              {e.actor ? ` by ${e.actor.display_name}` : ''}
            </span>
            {showTicketLink && ticketBase && e.ticket_id !== null && (
              <Link to={`${ticketBase}/tickets/${e.ticket_id}`} className="timeline-link">
                Open ticket #{e.ticket_id}
              </Link>
            )}
          </div>
          {describeEvent(e) && <p className="timeline-detail">{describeEvent(e)}</p>}
          <time className="timeline-time" dateTime={e.created_at}>
            {formatDateTime(e.created_at)}
          </time>
        </li>
      ))}
    </ol>
  )
}
