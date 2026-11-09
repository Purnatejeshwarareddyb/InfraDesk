import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { navItems } from '../components/nav'
import { adminUser, emptyUnread, errorResponse, makeTicket, mockApi, pageOf, renderApp, workerUser } from './helpers'

const summary = {
  scope: 'all', total: 0, open: 0, in_progress: 0, resolved: 0, high_priority_active: 0,
  by_status: [], by_priority: [], recent_activity: [],
}

describe('protected routes', () => {
  it('redirects to the login page when signed out', async () => {
    mockApi({ 'GET /api/v1/auth/me': () => errorResponse(401, 'not_authenticated', 'Authentication is required.') })
    renderApp('/admin/tickets')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    // The silent start-up probe is not a "session expired" event.
    expect(screen.queryByText(/session has expired/i)).not.toBeInTheDocument()
  })

  it('blocks a worker from the admin area', async () => {
    mockApi({ 'GET /api/v1/auth/me': () => workerUser, 'GET /api/v1/notifications': () => emptyUnread })
    renderApp('/admin/users')
    expect(await screen.findByRole('heading', { name: /do not have access/i })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Users' })).not.toBeInTheDocument()
  })

  it('blocks an administrator from the worker area', async () => {
    mockApi({ 'GET /api/v1/auth/me': () => adminUser, 'GET /api/v1/notifications': () => emptyUnread })
    renderApp('/worker')
    expect(await screen.findByRole('heading', { name: /do not have access/i })).toBeInTheDocument()
  })

  it('shows Not Found for unknown routes', async () => {
    mockApi({ 'GET /api/v1/auth/me': () => adminUser, 'GET /api/v1/notifications': () => emptyUnread })
    renderApp('/admin/does-not-exist')
    expect(await screen.findByRole('heading', { name: 'Page not found' })).toBeInTheDocument()
  })

  it('returns to login with an expiry message when an API call answers 401', async () => {
    mockApi({
      'GET /api/v1/auth/me': () => adminUser,
      'GET /api/v1/notifications': () => emptyUnread,
      'GET /api/v1/tickets': () => errorResponse(401, 'session_expired', 'Your session has expired. Please sign in again.'),
    })
    renderApp('/admin/tickets')
    expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
    expect(await screen.findByText('Your session has expired. Please sign in again.')).toBeInTheDocument()
  })
})

describe('role-aware navigation', () => {
  it('shows admin links to administrators', async () => {
    mockApi({
      'GET /api/v1/auth/me': () => adminUser,
      'GET /api/v1/notifications': () => emptyUnread,
      'GET /api/v1/reports/summary': () => summary,
    })
    renderApp('/admin')
    const nav = await screen.findByRole('navigation', { name: 'Main' })
    for (const name of ['Users', 'Assets', 'Reports', 'Activity', 'Settings and help']) {
      expect(nav).toHaveTextContent(name)
    }
    expect(screen.queryByRole('link', { name: 'My tickets' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Menu' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Skip to main content' })).toBeInTheDocument()
  })

  it('shows only worker links to workers', async () => {
    mockApi({
      'GET /api/v1/auth/me': () => workerUser,
      'GET /api/v1/notifications': () => emptyUnread,
      'GET /api/v1/reports/summary': () => ({ ...summary, scope: 'mine' }),
    })
    renderApp('/worker')
    const nav = await screen.findByRole('navigation', { name: 'Main' })
    expect(nav).toHaveTextContent('My tickets')
    expect(nav).toHaveTextContent('Create ticket')
    expect(nav).not.toHaveTextContent('Users')
    expect(nav).not.toHaveTextContent('Reports')
  })

  it('defines separate link sets per role', () => {
    expect(navItems('ADMIN').map((i) => i.label)).toContain('Users')
    expect(navItems('WORKER').map((i) => i.label)).not.toContain('Users')
  })

  it('shows the unread count in the notification bell', async () => {
    mockApi({
      'GET /api/v1/auth/me': () => workerUser,
      'GET /api/v1/notifications': () => ({ ...emptyUnread, unread_count: 4 }),
      'GET /api/v1/reports/summary': () => ({ ...summary, scope: 'mine' }),
    })
    renderApp('/worker')
    expect(await screen.findByRole('link', { name: 'Notifications, 4 unread' })).toBeInTheDocument()
  })

  it('opens the menu on small screens with the Menu button', async () => {
    mockApi({
      'GET /api/v1/auth/me': () => workerUser,
      'GET /api/v1/notifications': () => emptyUnread,
      'GET /api/v1/tickets': () => pageOf([makeTicket()]),
    })
    renderApp('/worker/tickets')
    const button = await screen.findByRole('button', { name: 'Menu' })
    expect(button).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'true')
  })
})
