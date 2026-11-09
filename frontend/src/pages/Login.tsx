import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { homePath, useAuth } from '../auth/authContext'
import { FormField } from '../components/FormField'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

interface LocationState {
  from?: string
  expired?: boolean
}

export function Login() {
  useDocumentTitle('Sign in')
  const { user, login, sessionExpired } = useAuth()
  const navigate = useNavigate()
  const state = (useLocation().state ?? {}) as LocationState
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to={homePath(user.role)} replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const next: typeof errors = {}
    if (!username.trim()) next.username = 'Enter your username.'
    if (!password) next.password = 'Enter your password.'
    setErrors(next)
    setServerError(null)
    if (next.username || next.password) return

    setBusy(true)
    try {
      const me = await login(username.trim(), password)
      const home = homePath(me.role)
      const target = state.from && (state.from === home || state.from.startsWith(`${home}/`)) ? state.from : home
      navigate(target, { replace: true })
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : 'Sign in failed. Please try again.')
      setBusy(false)
    }
  }

  return (
    <main className="login-page" id="main">
      <div className="login-card">
        <div className="brand brand-light">
          <span className="brand-name">InfraDesk</span>
        </div>
        <h1>Sign in</h1>
        <p className="muted">Use the account your administrator created for you.</p>
        {(state.expired || sessionExpired) && (
          <p className="notice notice-warn" role="status">
            Your session has expired. Please sign in again.
          </p>
        )}
        <form onSubmit={onSubmit} noValidate>
          <FormField label="Username" error={errors.username}>
            {(c) => (
              <input
                {...c}
                name="username"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            )}
          </FormField>
          <FormField label="Password" error={errors.password}>
            {(c) => (
              <input
                {...c}
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            )}
          </FormField>
          {serverError && (
            <p className="form-error" role="alert">
              {serverError}
            </p>
          )}
          <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
            {busy ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <p className="muted small">There is no self-registration. Ask an administrator for an account.</p>
      </div>
    </main>
  )
}
