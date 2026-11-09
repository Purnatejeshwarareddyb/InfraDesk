import type { Priority, TicketStatus } from '../api/types'
import { PRIORITY_LABEL, STATUS_LABEL } from '../utils/labels'

export function StatusBadge({ status }: { status: TicketStatus }) {
  return <span className={`chip status-${status}`}>{STATUS_LABEL[status] ?? status}</span>
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  return <span className={`chip priority-${priority}`}>{PRIORITY_LABEL[priority] ?? priority}</span>
}

export function Chip({ tone, children }: { tone: 'good' | 'warn' | 'bad' | 'muted' | 'info'; children: string }) {
  return <span className={`chip tone-${tone}`}>{children}</span>
}
