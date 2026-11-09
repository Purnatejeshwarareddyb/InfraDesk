import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { notificationsApi } from '../api/endpoints'
import { UnreadContext } from './unread'

export const POLL_MS = 30_000

/** Keeps the unread count fresh: polls every 30 seconds, but only while the tab is visible. */
export function UnreadProvider({ children }: { children: ReactNode }) {
  const [unread, setUnread] = useState(0)

  const refresh = useCallback(() => {
    notificationsApi.list({ page_size: 1 }).then(
      (res) => setUnread(res.unread_count),
      () => undefined, // keep the last known count; a 401 is handled centrally
    )
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') refresh()
    }, POLL_MS)
    const onVisible = () => {
      if (document.visibilityState === 'visible') refresh()
    }
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      clearInterval(id)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [refresh])

  const value = useMemo(() => ({ unread, refresh }), [unread, refresh])
  return <UnreadContext.Provider value={value}>{children}</UnreadContext.Provider>
}
