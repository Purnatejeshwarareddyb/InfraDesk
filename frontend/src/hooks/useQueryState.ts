import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

/** Keeps list filters in the URL so a filtered view can be reloaded or shared. */
export function useQueryState(defaults: Record<string, string>) {
  const [params, setParams] = useSearchParams()
  const values: Record<string, string> = {}
  for (const key of Object.keys(defaults)) values[key] = params.get(key) ?? defaults[key] ?? ''

  const update = useCallback(
    (patch: Record<string, string>, resetPage = true) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          for (const [k, v] of Object.entries(patch)) {
            if (v === '' || v === defaults[k]) next.delete(k)
            else next.set(k, v)
          }
          if (resetPage && !('page' in patch)) next.delete('page')
          return next
        },
        { replace: true },
      )
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [setParams],
  )
  return [values, update] as const
}
