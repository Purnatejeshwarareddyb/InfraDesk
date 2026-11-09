import { useEffect, useRef, type ReactNode } from 'react'

interface Props {
  open: boolean
  title: string
  message: ReactNode
  confirmLabel: string
  danger?: boolean
  busy?: boolean
  error?: string | null
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({ open, title, message, confirmLabel, danger, busy, error, onConfirm, onCancel }: Props) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const previous = document.activeElement as HTMLElement | null
    cancelRef.current?.focus()
    return () => previous?.focus?.()
  }, [open])

  if (!open) return null

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape' && !busy) {
      e.stopPropagation()
      onCancel()
      return
    }
    if (e.key !== 'Tab') return
    const focusable = panelRef.current?.querySelectorAll<HTMLElement>('button:not([disabled])')
    if (!focusable || focusable.length === 0) return
    const firstEl = focusable[0]
    const lastEl = focusable[focusable.length - 1]
    if (e.shiftKey && document.activeElement === firstEl) {
      e.preventDefault()
      lastEl?.focus()
    } else if (!e.shiftKey && document.activeElement === lastEl) {
      e.preventDefault()
      firstEl?.focus()
    }
  }

  return (
    <div className="dialog-backdrop" onKeyDown={onKeyDown}>
      <div
        className="dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-message"
        ref={panelRef}
      >
        <h2 id="confirm-title">{title}</h2>
        <div id="confirm-message" className="dialog-body">
          {message}
        </div>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="dialog-actions">
          <button type="button" className="btn" ref={cancelRef} onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button
            type="button"
            className={danger ? 'btn btn-danger' : 'btn btn-primary'}
            onClick={onConfirm}
            disabled={busy}
          >
            {busy ? 'Working...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
