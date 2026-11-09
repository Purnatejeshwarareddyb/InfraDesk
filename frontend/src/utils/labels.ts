import type { AssetStatus, AssetType, Category, Priority, Role, TicketStatus } from '../api/types'

export const STATUS_LABEL: Record<TicketStatus, string> = {
  OPEN: 'Open',
  ASSIGNED: 'Assigned',
  IN_PROGRESS: 'In progress',
  WAITING: 'Waiting',
  RESOLVED: 'Resolved',
  CLOSED: 'Closed',
  CANCELLED: 'Cancelled',
}

export const PRIORITY_LABEL: Record<Priority, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
  URGENT: 'Urgent',
}

export const CATEGORY_LABEL: Record<Category, string> = {
  HARDWARE: 'Hardware',
  SOFTWARE: 'Software',
  NETWORK: 'Network',
  ACCOUNT_ACCESS: 'Account access',
  PRINTER: 'Printer',
  OTHER: 'Other',
}

export const ASSET_STATUS_LABEL: Record<AssetStatus, string> = {
  ACTIVE: 'Active',
  IN_REPAIR: 'In repair',
  RETIRED: 'Retired',
}

export const ASSET_TYPE_LABEL: Record<AssetType, string> = {
  COMPUTER: 'Computer',
  LAPTOP: 'Laptop',
  PRINTER: 'Printer',
  NETWORK: 'Network',
  PERIPHERAL: 'Peripheral',
  OTHER: 'Other',
}

export const ROLE_LABEL: Record<Role, string> = { ADMIN: 'Administrator', WORKER: 'Worker' }

/** Action wording for a status button (what clicking does). */
export const TRANSITION_ACTION: Record<TicketStatus, string> = {
  OPEN: 'Reopen',
  ASSIGNED: 'Assign',
  IN_PROGRESS: 'Start work',
  WAITING: 'Mark waiting',
  RESOLVED: 'Resolve',
  CLOSED: 'Close ticket',
  CANCELLED: 'Cancel ticket',
}

const EVENT_LABEL: Record<string, string> = {
  TICKET_CREATED: 'Ticket created',
  TICKET_UPDATED: 'Ticket updated',
  TICKET_ASSIGNED: 'Assigned',
  STATUS_CHANGED: 'Status changed',
  COMMENT_ADDED: 'Comment added',
  USER_CREATED: 'User created',
  USER_UPDATED: 'User updated',
  USER_ACTIVATED: 'User activated',
  USER_DEACTIVATED: 'User deactivated',
  ASSET_CREATED: 'Asset created',
  ASSET_UPDATED: 'Asset updated',
  ASSET_RETIRED: 'Asset retired',
}

export function eventLabel(type: string): string {
  return EVENT_LABEL[type] ?? type.toLowerCase().replace(/_/g, ' ')
}

/** Readable text for a raw enum-like value (status, priority, role) found in history rows. */
export function prettyValue(value: string | null): string {
  if (!value) return ''
  const s = (STATUS_LABEL as Record<string, string>)[value]
  if (s) return s
  const p = (PRIORITY_LABEL as Record<string, string>)[value]
  if (p) return p
  const c = (CATEGORY_LABEL as Record<string, string>)[value]
  return c ?? value
}

export function label<T extends string>(map: Record<T, string>, key: string): string {
  return (map as Record<string, string>)[key] ?? key
}
