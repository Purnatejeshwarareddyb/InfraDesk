import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { adminUser, errorResponse, mockApi, renderApp, workerUser } from './helpers'

const signedOut = { 'GET /api/v1/auth/me': () => errorResponse(401, 'not_authenticated', 'Authentication is required.') }

describe('login page', () => {
  it('asks for both fields when submitted empty and does not call the API', async () => {
    const fetchMock = mockApi(signedOut)
    renderApp('/login')
    await screen.findByRole('heading', { name: 'Sign in' })
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(screen.getByText('Enter your username.')).toBeInTheDocument()
    expect(screen.getByText('Enter your password.')).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([url]) => String(url).includes('/auth/login'))).toBe(false)
  })

  it('shows the server error message when sign in fails', async () => {
    mockApi({
      ...signedOut,
      'POST /api/v1/auth/login': () => errorResponse(401, 'invalid_credentials', 'Incorrect username or password.'),
    })
    renderApp('/login')
    await userEvent.type(await screen.findByLabelText('Username'), 'admin')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect username or password.')
  })

  it('sends an administrator to the admin dashboard', async () => {
    mockApi({
      ...signedOut,
      'POST /api/v1/auth/login': () => ({ user: adminUser, expires_in: 3600 }),
      'GET /api/v1/reports/summary': () => ({
        scope: 'all', total: 12, open: 3, in_progress: 2, resolved: 7, high_priority_active: 1,
        by_status: [], by_priority: [], recent_activity: [],
      }),
      'GET /api/v1/notifications': () => ({ items: [], total: 0, page: 1, page_size: 1, pages: 1, unread_count: 0 }),
    })
    renderApp('/login')
    await userEvent.type(await screen.findByLabelText('Username'), 'admin')
    await userEvent.type(screen.getByLabelText('Password'), 'Secret-Passw0rd')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByRole('heading', { name: 'Dashboard' })).toBeInTheDocument()
    expect(await screen.findByText('12')).toBeInTheDocument()
  })

  it('sends a worker to the worker dashboard', async () => {
    mockApi({
      ...signedOut,
      'POST /api/v1/auth/login': () => ({ user: workerUser, expires_in: 3600 }),
      'GET /api/v1/reports/summary': () => ({
        scope: 'mine', total: 1, open: 1, in_progress: 0, resolved: 0, high_priority_active: 0,
        by_status: [], by_priority: [], recent_activity: [],
      }),
      'GET /api/v1/notifications': () => ({ items: [], total: 0, page: 1, page_size: 1, pages: 1, unread_count: 0 }),
    })
    renderApp('/login')
    await userEvent.type(await screen.findByLabelText('Username'), 'worker')
    await userEvent.type(screen.getByLabelText('Password'), 'Secret-Passw0rd')
    await userEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    await waitFor(() => expect(screen.getByRole('heading', { name: 'My dashboard' })).toBeInTheDocument())
  })
})
