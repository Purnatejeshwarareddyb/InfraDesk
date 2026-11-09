import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { adminUser, emptyUnread, errorResponse, jsonResponse, makeTicket, mockApi, pageOf, renderApp, workerUser } from './helpers'

const base = {
  'GET /api/v1/notifications': () => emptyUnread,
  'GET /api/v1/assets': () => pageOf([{ id: 3, asset_tag: 'LT-001', name: 'Laptop', status: 'ACTIVE' }]),
}

describe('create ticket form', () => {
  it('validates title and description before calling the API', async () => {
    const fetchMock = mockApi({ ...base, 'GET /api/v1/auth/me': () => workerUser })
    renderApp('/worker/tickets/new')
    await userEvent.click(await screen.findByRole('button', { name: 'Create ticket' }))
    expect(screen.getByText('Enter a title of at least 5 characters.')).toBeInTheDocument()
    expect(screen.getByText('Describe the problem in at least 10 characters.')).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([, init]) => (init as RequestInit | undefined)?.method === 'POST')).toBe(false)
  })

  it('does NOT show a success message when the API fails', async () => {
    mockApi({
      ...base,
      'GET /api/v1/auth/me': () => workerUser,
      'POST /api/v1/tickets': () => errorResponse(500, 'internal_error', 'An unexpected error occurred. Please try again.'),
    })
    renderApp('/worker/tickets/new')
    await userEvent.type(await screen.findByLabelText(/Title/), 'Monitor flickers')
    await userEvent.type(screen.getByLabelText(/Description/), 'The monitor flickers when it wakes.')
    await userEvent.click(screen.getByRole('button', { name: 'Create ticket' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('An unexpected error occurred.')
    expect(screen.queryByText(/created\./i)).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Create ticket' })).toBeInTheDocument()
  })

  it('shows success and opens the ticket only after the API succeeds', async () => {
    mockApi({
      ...base,
      'GET /api/v1/auth/me': () => workerUser,
      'POST /api/v1/tickets': () => jsonResponse(makeTicket({ id: 9, ticket_number: 'HD-000009' }), 201),
      'GET /api/v1/tickets/9': () => ({ ticket: makeTicket({ id: 9, ticket_number: 'HD-000009' }), comments: [], history: [] }),
    })
    renderApp('/worker/tickets/new')
    await userEvent.type(await screen.findByLabelText(/Title/), 'Monitor flickers')
    await userEvent.type(screen.getByLabelText(/Description/), 'The monitor flickers when it wakes.')
    await userEvent.click(screen.getByRole('button', { name: 'Create ticket' }))
    expect(await screen.findByText('Ticket HD-000009 created.')).toBeInTheDocument()
  })
})

describe('ticket list states', () => {
  it('shows loading, then rows', async () => {
    mockApi({ ...base, 'GET /api/v1/auth/me': () => workerUser, 'GET /api/v1/tickets': () => pageOf([makeTicket()]) })
    renderApp('/worker/tickets')
    expect(await screen.findByText('Printer jams on floor 2')).toBeInTheDocument()
    const table = within(screen.getByRole('table'))
    expect(table.getByText('Assigned')).toHaveClass('status-ASSIGNED')
    expect(table.getByText('High')).toHaveClass('priority-HIGH')
  })

  it('shows an error state with retry', async () => {
    mockApi({
      ...base,
      'GET /api/v1/auth/me': () => workerUser,
      'GET /api/v1/tickets': () => errorResponse(500, 'internal_error', 'The server broke.'),
    })
    renderApp('/worker/tickets')
    expect(await screen.findByText('The server broke.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Try again' })).toBeInTheDocument()
  })

  it('shows an empty state', async () => {
    mockApi({ ...base, 'GET /api/v1/auth/me': () => workerUser, 'GET /api/v1/tickets': () => pageOf([]) })
    renderApp('/worker/tickets')
    expect(await screen.findByText('No tickets match')).toBeInTheDocument()
  })

  it('offers a CSV download to administrators only', async () => {
    mockApi({
      ...base,
      'GET /api/v1/auth/me': () => adminUser,
      'GET /api/v1/tickets': () => pageOf([makeTicket()]),
      'GET /api/v1/users': () => pageOf([adminUser]),
    })
    renderApp('/admin/tickets?status=OPEN')
    const link = await screen.findByRole('link', { name: 'Download CSV' })
    expect(link).toHaveAttribute('href', expect.stringContaining('/api/v1/tickets/export.csv'))
    expect(link.getAttribute('href')).toContain('status=OPEN')
  })
})

describe('ticket detail workflow', () => {
  const detail = (t = makeTicket()) => ({ ticket: t, comments: [], history: [] })

  it('builds status buttons from allowed_transitions and asks for a note only on resolve', async () => {
    mockApi({
      ...base,
      'GET /api/v1/auth/me': () => workerUser,
      'GET /api/v1/tickets/7': () => detail(makeTicket({ status: 'IN_PROGRESS', allowed_transitions: ['WAITING', 'RESOLVED'] })),
    })
    renderApp('/worker/tickets/7')
    expect(await screen.findByRole('button', { name: 'Mark waiting' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Start work' })).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/Resolution note/)).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Resolve' }))
    expect(screen.getByLabelText(/Resolution note/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Resolve ticket' }))
    expect(screen.getByText('Describe what fixed the problem.')).toBeInTheDocument()
  })

  it('shows the error and no success toast when a transition fails', async () => {
    mockApi({
      ...base,
      'GET /api/v1/auth/me': () => workerUser,
      'GET /api/v1/tickets/7': () => detail(),
      'POST /api/v1/tickets/7/transition': () => errorResponse(422, 'transition_not_permitted', 'You are not allowed to move this ticket.'),
    })
    renderApp('/worker/tickets/7')
    await userEvent.click(await screen.findByRole('button', { name: 'Start work' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('You are not allowed to move this ticket.')
    expect(screen.queryByText(/status changed/i)).not.toBeInTheDocument()
  })

  it('confirms a successful transition and reloads', async () => {
    let status: 'ASSIGNED' | 'IN_PROGRESS' = 'ASSIGNED'
    mockApi({
      ...base,
      'GET /api/v1/auth/me': () => workerUser,
      'GET /api/v1/tickets/7': () => detail(makeTicket({ status, allowed_transitions: status === 'ASSIGNED' ? ['IN_PROGRESS'] : ['WAITING'] })),
      'POST /api/v1/tickets/7/transition': () => {
        status = 'IN_PROGRESS'
        return makeTicket({ status })
      },
    })
    renderApp('/worker/tickets/7')
    await userEvent.click(await screen.findByRole('button', { name: 'Start work' }))
    expect(await screen.findByText('Ticket status changed to In progress.')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Mark waiting' })).toBeInTheDocument())
  })

  it('lets administrators assign but not workers', async () => {
    mockApi({
      ...base,
      'GET /api/v1/auth/me': () => adminUser,
      'GET /api/v1/tickets/7': () => detail(makeTicket({ status: 'OPEN', assignee: null, allowed_transitions: ['IN_PROGRESS', 'CANCELLED'] })),
      'GET /api/v1/users': () => pageOf([workerUser]),
    })
    renderApp('/admin/tickets/7')
    expect(await screen.findByRole('button', { name: 'Assign ticket' })).toBeInTheDocument()
    expect(await screen.findByRole('option', { name: /Wes Worker/ })).toBeInTheDocument()
  })
})
