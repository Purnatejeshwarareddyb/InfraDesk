import type { ReactNode } from 'react'

export function Loading({ label = 'Loading' }: { label?: string }) {
  return (
    <div className="state state-loading" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      <span>{label}...</span>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state state-error" role="alert">
      <p className="state-title">Could not load this data</p>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="btn" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, hint, action }: { title: string; hint?: string; action?: ReactNode }) {
  return (
    <div className="state state-empty">
      <p className="state-title">{title}</p>
      {hint && <p>{hint}</p>}
      {action}
    </div>
  )
}

interface DataStateProps {
  loading: boolean
  error: string | null
  onRetry?: () => void
  empty?: boolean
  emptyTitle?: string
  emptyHint?: string
  emptyAction?: ReactNode
  hasData: boolean
  children: ReactNode
}

/** One place that decides between loading, error, empty and content. */
export function DataState({
  loading, error, onRetry, empty, emptyTitle = 'Nothing here yet', emptyHint, emptyAction, hasData, children,
}: DataStateProps) {
  if (loading && !hasData) return <Loading />
  if (error && !hasData) return <ErrorState message={error} onRetry={onRetry} />
  if (empty) return <EmptyState title={emptyTitle} hint={emptyHint} action={emptyAction} />
  return (
    <div className={loading ? 'is-refreshing' : undefined} aria-busy={loading}>
      {error && <ErrorState message={error} onRetry={onRetry} />}
      {children}
    </div>
  )
}
