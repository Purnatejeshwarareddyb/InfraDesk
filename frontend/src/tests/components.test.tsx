import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { PriorityBadge, StatusBadge } from '../components/Badges'
import { ConfirmDialog } from '../components/ConfirmDialog'
import { DataState } from '../components/StateViews'
import { Pagination } from '../components/Pagination'
import { STATUSES, PRIORITIES } from '../api/types'

describe('badges', () => {
  it('render readable status text', () => {
    render(<StatusBadge status="IN_PROGRESS" />)
    expect(screen.getByText('In progress')).toHaveClass('status-IN_PROGRESS')
  })
  it('render every status and priority with text, not just color', () => {
    for (const s of STATUSES) {
      const { unmount } = render(<StatusBadge status={s} />)
      expect(document.body.textContent?.length).toBeGreaterThan(0)
      unmount()
    }
    render(<PriorityBadge priority="URGENT" />)
    expect(screen.getByText('Urgent')).toBeInTheDocument()
    expect(PRIORITIES).toHaveLength(4)
  })
})

describe('Pagination', () => {
  it('shows the range and moves between pages', async () => {
    const onPage = vi.fn()
    render(<Pagination page={2} pages={3} total={45} pageSize={20} onPage={onPage} />)
    expect(screen.getByText('Showing 21-40 of 45')).toBeInTheDocument()
    expect(screen.getByText('Page 2 of 3')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Next' }))
    await userEvent.click(screen.getByRole('button', { name: 'Previous' }))
    expect(onPage).toHaveBeenNthCalledWith(1, 3)
    expect(onPage).toHaveBeenNthCalledWith(2, 1)
  })
  it('disables Previous on the first page and Next on the last', () => {
    const { rerender } = render(<Pagination page={1} pages={2} total={30} pageSize={20} onPage={() => undefined} />)
    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled()
    rerender(<Pagination page={2} pages={2} total={30} pageSize={20} onPage={() => undefined} />)
    expect(screen.getByRole('button', { name: 'Next' })).toBeDisabled()
  })
  it('renders nothing when there are no results', () => {
    const { container } = render(<Pagination page={1} pages={1} total={0} pageSize={20} onPage={() => undefined} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('DataState', () => {
  it('shows loading', () => {
    render(<DataState loading error={null} hasData={false}>content</DataState>)
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
  })
  it('shows an error with a retry action', async () => {
    const retry = vi.fn()
    render(<DataState loading={false} error="Boom" onRetry={retry} hasData={false}>content</DataState>)
    expect(screen.getByRole('alert')).toHaveTextContent('Boom')
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(retry).toHaveBeenCalled()
  })
  it('shows the empty state', () => {
    render(<DataState loading={false} error={null} hasData empty emptyTitle="No tickets match">content</DataState>)
    expect(screen.getByText('No tickets match')).toBeInTheDocument()
    expect(screen.queryByText('content')).not.toBeInTheDocument()
  })
  it('shows the content when data is present', () => {
    render(<DataState loading={false} error={null} hasData>content</DataState>)
    expect(screen.getByText('content')).toBeInTheDocument()
  })
})

describe('ConfirmDialog', () => {
  it('confirms, cancels and closes on Escape', async () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    render(
      <ConfirmDialog open title="Deactivate?" message="Sure?" confirmLabel="Deactivate user" danger onConfirm={onConfirm} onCancel={onCancel} />,
    )
    expect(screen.getByRole('alertdialog', { name: 'Deactivate?' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveFocus()
    await userEvent.click(screen.getByRole('button', { name: 'Deactivate user' }))
    expect(onConfirm).toHaveBeenCalled()
    await userEvent.keyboard('{Escape}')
    expect(onCancel).toHaveBeenCalled()
  })
  it('renders nothing when closed', () => {
    render(<ConfirmDialog open={false} title="x" message="y" confirmLabel="z" onConfirm={() => undefined} onCancel={() => undefined} />)
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })
})
