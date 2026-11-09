export const STATUSES = ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'WAITING', 'RESOLVED', 'CLOSED', 'CANCELLED'] as const
export const PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'URGENT'] as const
export const CATEGORIES = ['HARDWARE', 'SOFTWARE', 'NETWORK', 'ACCOUNT_ACCESS', 'PRINTER', 'OTHER'] as const
export const ASSET_STATUSES = ['ACTIVE', 'IN_REPAIR', 'RETIRED'] as const
export const ASSET_TYPES = ['COMPUTER', 'LAPTOP', 'PRINTER', 'NETWORK', 'PERIPHERAL', 'OTHER'] as const
export const ROLES = ['ADMIN', 'WORKER'] as const
export const SORTS = ['newest', 'oldest', 'updated', 'priority'] as const

export type TicketStatus = (typeof STATUSES)[number]
export type Priority = (typeof PRIORITIES)[number]
export type Category = (typeof CATEGORIES)[number]
export type AssetStatus = (typeof ASSET_STATUSES)[number]
export type AssetType = (typeof ASSET_TYPES)[number]
export type Role = (typeof ROLES)[number]
export type TicketSort = (typeof SORTS)[number]

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface UserBrief {
  id: number
  username: string
  display_name: string
}

export interface User extends UserBrief {
  role: Role
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginResponse {
  user: User
  expires_in: number
}

export interface AssetBrief {
  id: number
  asset_tag: string
  name: string
  status: AssetStatus
}

export interface Asset extends AssetBrief {
  asset_type: AssetType
  location: string
  serial_number: string | null
  notes: string
  created_at: string
  updated_at: string
}

export interface Ticket {
  id: number
  ticket_number: string
  title: string
  description: string
  category: Category
  priority: Priority
  status: TicketStatus
  reporter: UserBrief
  assignee: UserBrief | null
  related_asset: AssetBrief | null
  resolution_note: string | null
  created_at: string
  updated_at: string
  resolved_at: string | null
  closed_at: string | null
  allowed_transitions: TicketStatus[]
}

export interface Comment {
  id: number
  ticket_id: number
  author: UserBrief
  body: string
  created_at: string
}

export interface AuditEvent {
  id: number
  ticket_id: number | null
  actor: UserBrief | null
  event_type: string
  old_value: string | null
  new_value: string | null
  detail: string
  created_at: string
}

export interface TicketDetail {
  ticket: Ticket
  comments: Comment[]
  history: AuditEvent[]
}

export interface CountItem {
  key: string
  label: string
  count: number
}

export interface Summary {
  scope: string
  total: number
  open: number
  in_progress: number
  resolved: number
  high_priority_active: number
  by_status: CountItem[]
  by_priority: CountItem[]
  recent_activity: AuditEvent[]
}

export interface TicketReport {
  date_from: string | null
  date_to: string | null
  total: number
  by_status: CountItem[]
  by_category: CountItem[]
  by_priority: CountItem[]
  by_assignee: CountItem[]
}

export interface Notification {
  id: number
  ticket_id: number | null
  type: string
  message: string
  read_at: string | null
  created_at: string
}

export interface NotificationList extends Page<Notification> {
  unread_count: number
}

export interface Health {
  status: string
  app: string
  version: string
}

export interface TicketFilters {
  q?: string
  status?: TicketStatus | ''
  priority?: Priority | ''
  category?: Category | ''
  assignee_id?: string
  sort?: TicketSort
  created_from?: string
  created_to?: string
  mine?: boolean
}
