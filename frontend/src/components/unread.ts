import { createContext, useContext } from 'react'

export interface UnreadValue {
  unread: number
  refresh: () => void
}

export const UnreadContext = createContext<UnreadValue>({ unread: 0, refresh: () => undefined })

export function useUnread(): UnreadValue {
  return useContext(UnreadContext)
}
