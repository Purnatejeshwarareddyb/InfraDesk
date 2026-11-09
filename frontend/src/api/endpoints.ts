import { request } from './client'
import type {
  Asset, AssetStatus, AssetType, AuditEvent, Category, Comment, Health, LoginResponse, NotificationList,
  Notification, Page, Priority, Role, Summary, Ticket, TicketDetail, TicketFilters, TicketReport, TicketStatus, User,
} from './types'

export interface Paging {
  page?: number
  page_size?: number
}

export const authApi = {
  login: (username: string, password: string) =>
    request<LoginResponse>('/api/v1/auth/login', {
      method: 'POST', body: { username, password }, skipUnauthorizedHandler: true,
    }),
  logout: () => request<{ message: string }>('/api/v1/auth/logout', { method: 'POST', skipUnauthorizedHandler: true }),
  me: () => request<User>('/api/v1/auth/me', { skipUnauthorizedHandler: true }),
  changePassword: (current_password: string, new_password: string) =>
    request<{ message: string }>('/api/v1/auth/change-password', {
      method: 'POST', body: { current_password, new_password },
    }),
}

export const healthApi = {
  health: () => request<Health>('/health', { skipUnauthorizedHandler: true }),
}

export const ticketsApi = {
  list: (filters: TicketFilters & Paging, signal?: AbortSignal) =>
    request<Page<Ticket>>('/api/v1/tickets', { query: { ...filters }, signal }),
  get: (id: number | string) => request<TicketDetail>(`/api/v1/tickets/${id}`),
  create: (data: {
    title: string; description: string; category: Category; priority: Priority; related_asset_id?: number | null
  }) => request<Ticket>('/api/v1/tickets', { method: 'POST', body: data }),
  update: (id: number, data: Partial<{
    title: string; description: string; category: Category; priority: Priority
    related_asset_id: number | null; clear_related_asset: boolean
  }>) => request<Ticket>(`/api/v1/tickets/${id}`, { method: 'PATCH', body: data }),
  assign: (id: number, assignee_id: number, note?: string) =>
    request<Ticket>(`/api/v1/tickets/${id}/assign`, {
      method: 'POST', body: { assignee_id, note: note || null },
    }),
  transition: (id: number, status: TicketStatus, resolution_note?: string) =>
    request<Ticket>(`/api/v1/tickets/${id}/transition`, {
      method: 'POST', body: { status, resolution_note: resolution_note ?? null },
    }),
  comment: (id: number, body: string) =>
    request<Comment>(`/api/v1/tickets/${id}/comments`, { method: 'POST', body: { body } }),
}

export const usersApi = {
  list: (query: { q?: string; role?: Role | ''; active?: boolean | ''; page?: number; page_size?: number }) =>
    request<Page<User>>('/api/v1/users', {
      query: { ...query, active: query.active === '' ? undefined : query.active === undefined ? undefined : String(query.active) },
    }),
  create: (data: { username: string; display_name: string; password: string; role: Role }) =>
    request<User>('/api/v1/users', { method: 'POST', body: data }),
  update: (id: number, data: { display_name?: string; role?: Role; password?: string }) =>
    request<User>(`/api/v1/users/${id}`, { method: 'PATCH', body: data }),
  activate: (id: number) => request<User>(`/api/v1/users/${id}/activate`, { method: 'POST' }),
  deactivate: (id: number) => request<User>(`/api/v1/users/${id}/deactivate`, { method: 'POST' }),
}

export interface AssetInput {
  asset_tag: string
  name: string
  asset_type: AssetType
  location: string
  serial_number: string | null
  status: AssetStatus
  notes: string
}

export const assetsApi = {
  list: (query: {
    q?: string; status?: AssetStatus | ''; asset_type?: AssetType | ''; include_retired?: boolean
    page?: number; page_size?: number
  }) =>
    request<Page<Asset>>('/api/v1/assets', {
      query: { ...query, include_retired: query.include_retired === undefined ? undefined : String(query.include_retired) },
    }),
  create: (data: AssetInput) => request<Asset>('/api/v1/assets', { method: 'POST', body: data }),
  update: (id: number, data: Partial<AssetInput>) =>
    request<Asset>(`/api/v1/assets/${id}`, { method: 'PATCH', body: data }),
  retire: (id: number) => request<Asset>(`/api/v1/assets/${id}/retire`, { method: 'POST' }),
}

export const notificationsApi = {
  list: (query: { unread_only?: boolean; page?: number; page_size?: number }) =>
    request<NotificationList>('/api/v1/notifications', { query }),
  markRead: (id: number) => request<Notification>(`/api/v1/notifications/${id}/read`, { method: 'POST' }),
  markAllRead: () => request<{ message: string }>('/api/v1/notifications/read-all', { method: 'POST' }),
}

export const reportsApi = {
  summary: () => request<Summary>('/api/v1/reports/summary'),
  tickets: (query: { date_from?: string; date_to?: string }) =>
    request<TicketReport>('/api/v1/reports/tickets', { query }),
}

export const activityApi = {
  list: (query: Paging) => request<Page<AuditEvent>>('/api/v1/activity', { query: { ...query } }),
}
