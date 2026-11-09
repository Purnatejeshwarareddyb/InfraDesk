import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import { App } from '../App'
import type { Page, Ticket, User } from '../api/types'
import { AuthProvider } from '../auth/AuthProvider'
import { ToastProvider } from '../components/Toast'

// Fixtures live only in tests; the application itself never contains mock data.
export const adminUser: User = {
  id: 1, username: 'admin', display_name: 'Ada Admin', role: 'ADMIN', is_active: true,
  created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z',
}
export const workerUser: User = { ...adminUser, id: 2, username: 'worker', display_name: 'Wes Worker', role: 'WORKER' }

export function makeTicket(overrides: Partial<Ticket> = {}): Ticket {
  return {
    id: 7, ticket_number: 'HD-000007', title: 'Printer jams on floor 2', description: 'Paper jams every page.',
    category: 'PRINTER', priority: 'HIGH', status: 'ASSIGNED',
    reporter: { id: 2, username: 'worker', display_name: 'Wes Worker' },
    assignee: { id: 2, username: 'worker', display_name: 'Wes Worker' },
    related_asset: null, resolution_note: null,
    created_at: '2026-05-01T10:00:00Z', updated_at: '2026-05-01T10:00:00Z', resolved_at: null, closed_at: null,
    allowed_transitions: ['IN_PROGRESS', 'WAITING'],
    ...overrides,
  }
}

export function pageOf<T>(items: T[], extra: Partial<Page<T>> = {}): Page<T> {
  return { items, total: items.length, page: 1, page_size: 20, pages: 1, ...extra }
}

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

export function errorResponse(status: number, code: string, message: string, details?: unknown): Response {
  return jsonResponse({ error: { code, message, ...(details ? { details } : {}) } }, status)
}

type Handler = (url: URL, init: RequestInit | undefined) => Response | unknown

/** Replaces fetch for one test. Keys look like "GET /api/v1/auth/me". */
export function mockApi(handlers: Record<string, Handler>) {
  const fn = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost')
    const key = `${init?.method ?? 'GET'} ${url.pathname}`
    const handler = handlers[key]
    if (!handler) return errorResponse(404, 'not_found', `No mock for ${key}`)
    const result = handler(url, init)
    return result instanceof Response ? result : jsonResponse(result)
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

export function renderApp(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <ToastProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ToastProvider>
    </MemoryRouter>,
  )
}

export function renderWithRouter(ui: ReactElement, path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <ToastProvider>{ui}</ToastProvider>
    </MemoryRouter>,
  )
}

export const emptyUnread = { items: [], total: 0, page: 1, page_size: 1, pages: 1, unread_count: 0 }
