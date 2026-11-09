import { useEffect, useState, type FormEvent } from 'react'
import { ApiError, errorMessage } from '../../api/client'
import { usersApi } from '../../api/endpoints'
import { ROLES, type Role, type User } from '../../api/types'
import { useAuth } from '../../auth/authContext'
import { Chip } from '../../components/Badges'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { DataTable, type Column } from '../../components/DataTable'
import { FormField } from '../../components/FormField'
import { Modal } from '../../components/Modal'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { DataState } from '../../components/StateViews'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../hooks/useAsync'
import { useDebounced } from '../../hooks/useDebounced'
import { formatDate } from '../../utils/date'
import { ROLE_LABEL } from '../../utils/labels'
import { passwordProblem } from '../../utils/validation'

type Dialog =
  | { kind: 'create' }
  | { kind: 'edit'; user: User }
  | { kind: 'password'; user: User }
  | { kind: 'toggle'; user: User }
  | null

export function Users() {
  const { user: me } = useAuth()
  const toast = useToast()
  const [search, setSearch] = useState('')
  const q = useDebounced(search)
  const [role, setRole] = useState<Role | ''>('')
  const [active, setActive] = useState<'' | 'true' | 'false'>('')
  const [page, setPage] = useState(1)
  const [dialog, setDialog] = useState<Dialog>(null)
  const list = useAsync(
    () => usersApi.list({ q, role, active: active === '' ? '' : active === 'true', page, page_size: 20 }),
    [q, role, active, page],
  )
  useEffect(() => setPage(1), [q, role, active])

  const columns: Column<User>[] = [
    { key: 'name', header: 'Name', render: (u) => <strong>{u.display_name}</strong> },
    { key: 'username', header: 'Username', render: (u) => <span className="mono">{u.username}</span> },
    { key: 'role', header: 'Role', render: (u) => ROLE_LABEL[u.role] },
    { key: 'active', header: 'Status', render: (u) => <Chip tone={u.is_active ? 'good' : 'muted'}>{u.is_active ? 'Active' : 'Deactivated'}</Chip> },
    { key: 'created', header: 'Created', render: (u) => formatDate(u.created_at) },
    {
      key: 'actions',
      header: 'Actions',
      render: (u) => (
        <div className="button-row">
          <button type="button" className="btn btn-small" onClick={() => setDialog({ kind: 'edit', user: u })}>Edit</button>
          <button type="button" className="btn btn-small" onClick={() => setDialog({ kind: 'password', user: u })}>Reset password</button>
          <button
            type="button"
            className={u.is_active ? 'btn btn-small btn-danger-outline' : 'btn btn-small'}
            disabled={u.id === me?.id}
            onClick={() => setDialog({ kind: 'toggle', user: u })}
          >
            {u.is_active ? 'Deactivate' : 'Activate'}
          </button>
        </div>
      ),
    },
  ]

  function done(message: string) {
    toast.success(message)
    setDialog(null)
    list.reload()
  }

  return (
    <>
      <PageHeader
        title="Users"
        subtitle="Accounts for administrators and workers."
        actions={<button type="button" className="btn btn-primary" onClick={() => setDialog({ kind: 'create' })}>Create user</button>}
      />
      <form className="filters" role="search" aria-label="Filter users" onSubmit={(e) => e.preventDefault()}>
        <div className="field field-grow">
          <label htmlFor="u-search">Search</label>
          <input id="u-search" type="search" placeholder="Name or username" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="u-role">Role</label>
          <select id="u-role" value={role} onChange={(e) => setRole(e.target.value as Role | '')}>
            <option value="">All roles</option>
            {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="u-active">Account</label>
          <select id="u-active" value={active} onChange={(e) => setActive(e.target.value as '' | 'true' | 'false')}>
            <option value="">All accounts</option>
            <option value="true">Active</option>
            <option value="false">Deactivated</option>
          </select>
        </div>
      </form>
      <DataState
        loading={list.loading} error={list.error} onRetry={list.reload} hasData={list.data !== null}
        empty={list.data !== null && list.data.total === 0} emptyTitle="No users match" emptyHint="Change the filters or create a user."
      >
        {list.data && (
          <>
            <DataTable caption="Users" columns={columns} rows={list.data.items} rowKey={(u) => u.id} />
            <Pagination page={list.data.page} pages={list.data.pages} total={list.data.total} pageSize={list.data.page_size} onPage={setPage} />
          </>
        )}
      </DataState>

      {dialog?.kind === 'create' && <CreateUser onClose={() => setDialog(null)} onDone={done} />}
      {dialog?.kind === 'edit' && <EditUser user={dialog.user} onClose={() => setDialog(null)} onDone={done} />}
      {dialog?.kind === 'password' && <ResetPassword user={dialog.user} onClose={() => setDialog(null)} onDone={done} />}
      {dialog?.kind === 'toggle' && <ToggleUser user={dialog.user} onClose={() => setDialog(null)} onDone={done} />}
    </>
  )
}

interface DialogProps {
  onClose: () => void
  onDone: (message: string) => void
}

function CreateUser({ onClose, onDone }: DialogProps) {
  const [username, setUsername] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<Role>('WORKER')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setServerError(null)
    const found: Record<string, string> = {}
    if (!/^[a-z0-9_.-]{3,32}$/i.test(username.trim())) found.username = 'Use 3-32 letters, digits, dots, dashes or underscores.'
    if (displayName.trim().length < 2) found.display_name = 'Enter a name of at least 2 characters.'
    const problem = passwordProblem(password)
    if (problem) found.password = problem
    setErrors(found)
    if (Object.keys(found).length > 0) return
    setBusy(true)
    try {
      const u = await usersApi.create({ username: username.trim(), display_name: displayName.trim(), password, role })
      onDone(`User ${u.username} created.`)
    } catch (err) {
      if (err instanceof ApiError) setErrors(err.fieldErrors)
      setServerError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <Modal title="Create user" onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <FormField label="Username" required error={errors.username}>
          {(c) => <input {...c} autoComplete="off" autoCapitalize="none" value={username} onChange={(e) => setUsername(e.target.value)} />}
        </FormField>
        <FormField label="Display name" required error={errors.display_name}>
          {(c) => <input {...c} value={displayName} onChange={(e) => setDisplayName(e.target.value)} />}
        </FormField>
        <FormField label="Initial password" required error={errors.password} hint="At least 10 characters with upper-case, lower-case and a digit.">
          {(c) => <input {...c} type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />}
        </FormField>
        <FormField label="Role">
          {(c) => (
            <select {...c} value={role} onChange={(e) => setRole(e.target.value as Role)}>
              {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
            </select>
          )}
        </FormField>
        {serverError && <p className="form-error" role="alert">{serverError}</p>}
        <div className="dialog-actions">
          <button type="button" className="btn" onClick={onClose} disabled={busy}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Creating...' : 'Create user'}</button>
        </div>
      </form>
    </Modal>
  )
}

function EditUser({ user, onClose, onDone }: DialogProps & { user: User }) {
  const [displayName, setDisplayName] = useState(user.display_name)
  const [role, setRole] = useState<Role>(user.role)
  const [nameError, setNameError] = useState<string | null>(null)
  const [serverError, setServerError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setServerError(null)
    if (displayName.trim().length < 2) {
      setNameError('Enter a name of at least 2 characters.')
      return
    }
    setNameError(null)
    setBusy(true)
    try {
      await usersApi.update(user.id, { display_name: displayName.trim(), role })
      onDone(`User ${user.username} updated.`)
    } catch (err) {
      setServerError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <Modal title={`Edit ${user.username}`} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <FormField label="Display name" required error={nameError}>
          {(c) => <input {...c} value={displayName} onChange={(e) => setDisplayName(e.target.value)} />}
        </FormField>
        <FormField label="Role">
          {(c) => (
            <select {...c} value={role} onChange={(e) => setRole(e.target.value as Role)}>
              {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
            </select>
          )}
        </FormField>
        {serverError && <p className="form-error" role="alert">{serverError}</p>}
        <div className="dialog-actions">
          <button type="button" className="btn" onClick={onClose} disabled={busy}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Saving...' : 'Save changes'}</button>
        </div>
      </form>
    </Modal>
  )
}

function ResetPassword({ user, onClose, onDone }: DialogProps & { user: User }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [serverError, setServerError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setServerError(null)
    const problem = passwordProblem(password)
    setError(problem)
    if (problem) return
    setBusy(true)
    try {
      await usersApi.update(user.id, { password })
      onDone(`Password reset for ${user.username}.`)
    } catch (err) {
      setServerError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <Modal title={`Reset password for ${user.username}`} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <FormField label="New password" required error={error} hint="Share it with the person through a safe channel.">
          {(c) => <input {...c} type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} />}
        </FormField>
        {serverError && <p className="form-error" role="alert">{serverError}</p>}
        <div className="dialog-actions">
          <button type="button" className="btn" onClick={onClose} disabled={busy}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>{busy ? 'Resetting...' : 'Reset password'}</button>
        </div>
      </form>
    </Modal>
  )
}

function ToggleUser({ user, onClose, onDone }: DialogProps & { user: User }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const deactivating = user.is_active

  async function run() {
    setBusy(true)
    setError(null)
    try {
      if (deactivating) await usersApi.deactivate(user.id)
      else await usersApi.activate(user.id)
      onDone(`User ${user.username} ${deactivating ? 'deactivated' : 'activated'}.`)
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <ConfirmDialog
      open
      title={deactivating ? `Deactivate ${user.username}?` : `Activate ${user.username}?`}
      message={deactivating ? 'They will be signed out and cannot sign in until you activate the account again.' : 'They will be able to sign in again.'}
      confirmLabel={deactivating ? 'Deactivate user' : 'Activate user'}
      danger={deactivating}
      busy={busy}
      error={error}
      onConfirm={run}
      onCancel={onClose}
    />
  )
}
