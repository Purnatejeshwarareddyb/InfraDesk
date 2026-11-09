import { useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, errorMessage } from '../../api/client'
import { ticketsApi, usersApi } from '../../api/endpoints'
import { CATEGORIES, PRIORITIES, type Category, type Priority, type Ticket, type TicketStatus } from '../../api/types'
import { PriorityBadge, StatusBadge } from '../../components/Badges'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { EventList } from '../../components/EventList'
import { FormField } from '../../components/FormField'
import { PageHeader } from '../../components/PageHeader'
import { DataState } from '../../components/StateViews'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../hooks/useAsync'
import { formatDateTime } from '../../utils/date'
import { CATEGORY_LABEL, PRIORITY_LABEL, ROLE_LABEL, STATUS_LABEL, TRANSITION_ACTION } from '../../utils/labels'
import { validateTicket } from '../../utils/validation'

const ASSIGNABLE: TicketStatus[] = ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'WAITING']
const CONFIRM_STATUSES: TicketStatus[] = ['CANCELLED', 'CLOSED']

export function TicketDetail({ admin }: { admin: boolean }) {
  const { id } = useParams()
  const base = admin ? '/admin' : '/worker'
  const { data, error, loading, reload } = useAsync(() => ticketsApi.get(id ?? ''), [id])

  const ticket = data?.ticket
  return (
    <>
      <p className="breadcrumb">
        <Link to={`${base}/tickets`}>Back to tickets</Link>
      </p>
      <PageHeader title={ticket ? `${ticket.ticket_number}: ${ticket.title}` : 'Ticket'} />
      <DataState loading={loading} error={error} onRetry={reload} hasData={data !== null}>
        {data && ticket && (
          <div className="detail-layout">
            <div className="detail-main">
              <section className="panel" aria-label="Ticket details">
                <div className="chip-row">
                  <StatusBadge status={ticket.status} />
                  <PriorityBadge priority={ticket.priority} />
                  <span className="chip tone-muted">{CATEGORY_LABEL[ticket.category]}</span>
                </div>
                <p className="description">{ticket.description}</p>
                {ticket.resolution_note && (
                  <div className="resolution">
                    <h3>Resolution note</h3>
                    <p>{ticket.resolution_note}</p>
                  </div>
                )}
                <dl className="facts">
                  <div><dt>Reported by</dt><dd>{ticket.reporter.display_name}</dd></div>
                  <div><dt>Assigned to</dt><dd>{ticket.assignee?.display_name ?? 'Unassigned'}</dd></div>
                  <div>
                    <dt>Related asset</dt>
                    <dd>{ticket.related_asset ? `${ticket.related_asset.asset_tag} - ${ticket.related_asset.name}` : 'None'}</dd>
                  </div>
                  <div><dt>Created</dt><dd>{formatDateTime(ticket.created_at)}</dd></div>
                  <div><dt>Last updated</dt><dd>{formatDateTime(ticket.updated_at)}</dd></div>
                  <div><dt>Resolved</dt><dd>{formatDateTime(ticket.resolved_at)}</dd></div>
                  <div><dt>Closed</dt><dd>{formatDateTime(ticket.closed_at)}</dd></div>
                </dl>
              </section>

              <StatusActions ticket={ticket} onChanged={reload} />
              <Comments ticketId={ticket.id} comments={data.comments} onChanged={reload} />
              <section className="panel" aria-label="History">
                <h2 className="panel-title">History</h2>
                {data.history.length === 0 ? <p className="muted">No history yet.</p> : <EventList events={data.history} />}
              </section>
            </div>
            {admin && (
              <aside className="detail-side" aria-label="Manage ticket">
                <AssignPanel ticket={ticket} onChanged={reload} />
                <EditPanel key={ticket.updated_at} ticket={ticket} onChanged={reload} />
              </aside>
            )}
          </div>
        )}
      </DataState>
    </>
  )
}

function StatusActions({ ticket, onChanged }: { ticket: Ticket; onChanged: () => void }) {
  const toast = useToast()
  const [resolving, setResolving] = useState(false)
  const [note, setNote] = useState('')
  const [noteError, setNoteError] = useState<string | null>(null)
  const [pending, setPending] = useState<TicketStatus | null>(null)
  const [confirm, setConfirm] = useState<TicketStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  const options = ticket.allowed_transitions
  if (options.length === 0) {
    return (
      <section className="panel" aria-label="Change status">
        <h2 className="panel-title">Status</h2>
        <p className="muted">You cannot change the status of this ticket right now.</p>
      </section>
    )
  }

  async function run(status: TicketStatus, resolution?: string) {
    setError(null)
    setPending(status)
    try {
      await ticketsApi.transition(ticket.id, status, resolution)
      toast.success(`Ticket status changed to ${STATUS_LABEL[status]}.`)
      setResolving(false)
      setNote('')
      setConfirm(null)
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
      setConfirm(null)
    } finally {
      setPending(null)
    }
  }

  function choose(status: TicketStatus) {
    setError(null)
    if (status === 'RESOLVED') {
      setResolving(true)
    } else {
      setResolving(false)
      if (CONFIRM_STATUSES.includes(status)) setConfirm(status)
      else void run(status)
    }
  }

  function submitResolve(e: FormEvent) {
    e.preventDefault()
    if (!note.trim()) {
      setNoteError('Describe what fixed the problem.')
      return
    }
    setNoteError(null)
    void run('RESOLVED', note.trim())
  }

  return (
    <section className="panel" aria-label="Change status">
      <h2 className="panel-title">Change status</h2>
      <div className="button-row">
        {options.map((s) => (
          <button
            key={s}
            type="button"
            className={s === 'CANCELLED' ? 'btn btn-danger-outline' : 'btn'}
            disabled={pending !== null}
            aria-pressed={s === 'RESOLVED' ? resolving : undefined}
            onClick={() => choose(s)}
          >
            {pending === s ? 'Working...' : TRANSITION_ACTION[s]}
          </button>
        ))}
      </div>
      {resolving && (
        <form onSubmit={submitResolve} className="resolve-form" noValidate>
          <FormField label="Resolution note" required error={noteError} hint="Shown to the reporter and kept in the history.">
            {(c) => <textarea {...c} rows={4} value={note} onChange={(e) => setNote(e.target.value)} />}
          </FormField>
          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={pending !== null}>
              {pending === 'RESOLVED' ? 'Resolving...' : 'Resolve ticket'}
            </button>
            <button type="button" className="btn" onClick={() => setResolving(false)} disabled={pending !== null}>
              Cancel
            </button>
          </div>
        </form>
      )}
      {error && <p className="form-error" role="alert">{error}</p>}
      <ConfirmDialog
        open={confirm !== null}
        title={confirm === 'CANCELLED' ? 'Cancel this ticket?' : 'Close this ticket?'}
        message={
          confirm === 'CANCELLED'
            ? 'A cancelled ticket cannot be reopened.'
            : 'Closing marks the work as finished. Only an administrator can reopen it.'
        }
        confirmLabel={confirm === 'CANCELLED' ? 'Cancel ticket' : 'Close ticket'}
        danger={confirm === 'CANCELLED'}
        busy={pending !== null}
        onConfirm={() => confirm && void run(confirm)}
        onCancel={() => setConfirm(null)}
      />
    </section>
  )
}

function Comments({ ticketId, comments, onChanged }: { ticketId: number; comments: { id: number; body: string; created_at: string; author: { display_name: string } }[]; onChanged: () => void }) {
  const toast = useToast()
  const [body, setBody] = useState('')
  const [fieldError, setFieldError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!body.trim()) {
      setFieldError('Write a comment first.')
      return
    }
    setFieldError(null)
    setBusy(true)
    try {
      await ticketsApi.comment(ticketId, body.trim())
      toast.success('Comment added.')
      setBody('')
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel" aria-label="Comments">
      <h2 className="panel-title">Comments and work notes</h2>
      {comments.length === 0 ? (
        <p className="muted">No comments yet.</p>
      ) : (
        <ul className="comments">
          {comments.map((c) => (
            <li key={c.id} className="comment">
              <p className="comment-meta">
                <strong>{c.author.display_name}</strong>{' '}
                <time dateTime={c.created_at}>{formatDateTime(c.created_at)}</time>
              </p>
              <p className="comment-body">{c.body}</p>
            </li>
          ))}
        </ul>
      )}
      <form onSubmit={submit} noValidate>
        <FormField label="Add a comment" error={fieldError}>
          {(c) => <textarea {...c} rows={3} value={body} maxLength={5000} onChange={(e) => setBody(e.target.value)} />}
        </FormField>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? 'Posting...' : 'Post comment'}
        </button>
      </form>
    </section>
  )
}

function AssignPanel({ ticket, onChanged }: { ticket: Ticket; onChanged: () => void }) {
  const toast = useToast()
  const users = useAsync(() => usersApi.list({ active: true, page_size: 100 }), [])
  const [assigneeId, setAssigneeId] = useState(ticket.assignee ? String(ticket.assignee.id) : '')
  const [note, setNote] = useState('')
  const [fieldError, setFieldError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const canAssign = ASSIGNABLE.includes(ticket.status)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!assigneeId) {
      setFieldError('Choose who should work on this ticket.')
      return
    }
    setFieldError(null)
    setBusy(true)
    try {
      const updated = await ticketsApi.assign(ticket.id, Number(assigneeId), note.trim() || undefined)
      toast.success(`Assigned to ${updated.assignee?.display_name ?? 'the selected user'}.`)
      setNote('')
      onChanged()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel" aria-label="Assignment">
      <h2 className="panel-title">Assign</h2>
      {!canAssign ? (
        <p className="muted">A ticket in status {STATUS_LABEL[ticket.status]} cannot be assigned.</p>
      ) : users.loading ? (
        <p className="muted" role="status">Loading people...</p>
      ) : users.error ? (
        <p className="form-error" role="alert">{users.error}</p>
      ) : (
        <form onSubmit={submit} noValidate>
          <FormField label="Assign to" error={fieldError}>
            {(c) => (
              <select {...c} value={assigneeId} onChange={(e) => setAssigneeId(e.target.value)}>
                <option value="">Choose a person</option>
                {users.data?.items.map((u) => (
                  <option key={u.id} value={u.id}>{u.display_name} ({ROLE_LABEL[u.role]})</option>
                ))}
              </select>
            )}
          </FormField>
          <FormField label="Note (optional)">
            {(c) => <input {...c} value={note} maxLength={1000} onChange={(e) => setNote(e.target.value)} />}
          </FormField>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Assigning...' : 'Assign ticket'}
          </button>
        </form>
      )}
    </section>
  )
}

function EditPanel({ ticket, onChanged }: { ticket: Ticket; onChanged: () => void }) {
  const toast = useToast()
  const [title, setTitle] = useState(ticket.title)
  const [description, setDescription] = useState(ticket.description)
  const [category, setCategory] = useState<Category>(ticket.category)
  const [priority, setPriority] = useState<Priority>(ticket.priority)
  const [errors, setErrors] = useState<{ title?: string; description?: string }>({})
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const found = validateTicket(title, description)
    setErrors(found)
    if (Object.keys(found).length > 0) return
    setBusy(true)
    try {
      await ticketsApi.update(ticket.id, {
        title: title.trim(), description: description.trim(), category, priority,
      })
      toast.success('Ticket details saved.')
      onChanged()
    } catch (err) {
      if (err instanceof ApiError) setErrors({ title: err.fieldErrors.title, description: err.fieldErrors.description })
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="panel" aria-label="Edit details">
      <h2 className="panel-title">Edit details</h2>
      <form onSubmit={submit} noValidate>
        <FormField label="Title" error={errors.title}>
          {(c) => <input {...c} value={title} onChange={(e) => setTitle(e.target.value)} />}
        </FormField>
        <FormField label="Description" error={errors.description}>
          {(c) => <textarea {...c} rows={5} value={description} onChange={(e) => setDescription(e.target.value)} />}
        </FormField>
        <FormField label="Category">
          {(c) => (
            <select {...c} value={category} onChange={(e) => setCategory(e.target.value as Category)}>
              {CATEGORIES.map((v) => <option key={v} value={v}>{CATEGORY_LABEL[v]}</option>)}
            </select>
          )}
        </FormField>
        <FormField label="Priority">
          {(c) => (
            <select {...c} value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
              {PRIORITIES.map((v) => <option key={v} value={v}>{PRIORITY_LABEL[v]}</option>)}
            </select>
          )}
        </FormField>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? 'Saving...' : 'Save changes'}
        </button>
      </form>
    </section>
  )
}
