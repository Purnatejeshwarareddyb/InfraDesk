import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { setUnauthorizedHandler } from '../api/client'
import { authApi } from '../api/endpoints'
import type { User } from '../api/types'
import { AuthContext, type AuthContextValue } from './authContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [initializing, setInitializing] = useState(true)
  const [sessionExpired, setSessionExpired] = useState(false)
  const navigate = useNavigate()
  const userRef = useRef<User | null>(null)
  userRef.current = user

  useEffect(() => {
    let cancelled = false
    authApi.me().then(
      (me) => {
        if (cancelled) return
        setUser(me)
        setInitializing(false)
      },
      () => {
        if (cancelled) return
        setUser(null)
        setInitializing(false)
      },
    )
    return () => {
      cancelled = true
    }
  }, [])

  const expireSession = useCallback(() => {
    if (!userRef.current) return
    setSessionExpired(true)
    setUser(null) // protected routes then redirect to /login
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(expireSession)
    return () => setUnauthorizedHandler(null)
  }, [expireSession])

  const login = useCallback(async (username: string, password: string) => {
    const res = await authApi.login(username, password)
    setSessionExpired(false)
    setUser(res.user)
    return res.user
  }, [])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      setSessionExpired(false)
      setUser(null)
      navigate('/login', { replace: true })
    }
  }, [navigate])

  const value = useMemo<AuthContextValue>(
    () => ({ user, initializing, sessionExpired, login, logout, expireSession }),
    [user, initializing, sessionExpired, login, logout, expireSession],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
