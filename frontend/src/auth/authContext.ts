import { createContext, useContext } from 'react'
import type { Role, User } from '../api/types'

export interface AuthContextValue {
  user: User | null
  /** True until the first /auth/me probe has finished. */
  initializing: boolean
  /** True when the last session ended because the server answered 401. */
  sessionExpired: boolean
  login: (username: string, password: string) => Promise<User>
  logout: () => Promise<void>
  /** Mark that the session ended (used by the 401 handler). */
  expireSession: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}

export function homePath(role: Role): string {
  return role === 'ADMIN' ? '/admin' : '/worker'
}
