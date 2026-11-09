import { useCallback, useEffect, useRef, useState } from 'react'
import { isAbort, errorMessage } from '../api/client'

export interface AsyncState<T> {
  data: T | null
  error: string | null
  loading: boolean
  reload: () => void
  setData: (value: T | null) => void
}

/** Runs `fn` when `deps` change; stale responses are ignored. */
export function useAsync<T>(fn: (signal: AbortSignal) => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [tick, setTick] = useState(0)
  const fnRef = useRef(fn)
  fnRef.current = fn

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    fnRef.current(controller.signal).then(
      (value) => {
        if (controller.signal.aborted) return
        setData(value)
        setLoading(false)
      },
      (err: unknown) => {
        if (controller.signal.aborted || isAbort(err)) return
        setError(errorMessage(err))
        setLoading(false)
      },
    )
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  const reload = useCallback(() => setTick((n) => n + 1), [])
  return { data, error, loading, reload, setData }
}
