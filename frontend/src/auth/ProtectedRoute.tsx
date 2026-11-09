import type { ReactNode } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import type { Role } from '../api/types'
import { Loading } from '../components/StateViews'
import { homePath, useAuth } from './authContext'

interface Props {
  role?: Role
  children: ReactNode
}

/** Front-end gate only: the backend remains the authority on every request. */
export function ProtectedRoute({ role, children }: Props) {
  const { user, initializing } = useAuth()
  const location = useLocation()

  if (initializing) return <Loading label="Checking your session" />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  if (role && user.role !== role) {
    return (
      <main className="centered-page" id="main">
        <h1>You do not have access to this area</h1>
        <p>This section is for {role === 'ADMIN' ? 'administrators' : 'workers'} only.</p>
        <Link className="btn btn-primary" to={homePath(user.role)}>
          Go to your dashboard
        </Link>
      </main>
    )
  }
  return <>{children}</>
}
