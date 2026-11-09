import { useEffect, useRef, type ReactNode } from 'react'

interface Props {
  title: string
  onClose: () => void
  children: ReactNode
  wide?: boolean
}

/** A modal dialog that traps focus, closes on Escape and returns focus when it closes. */
export function Modal({ title, onClose, children, wide }: Props) {
  const panelRef = useRef<HTMLDivElement>(null)
  const closeRef = useRef(onClose)
  closeRef.current = onClose

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    const panel = panelRef.current
    const first = panel?.querySelector<HTMLElement>('input, select, textarea, button')
    first?.focus()
    return () => previous?.focus?.()
  }, [])

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      e.stopPropagation()
      closeRef.current()
      return
    }
    if (e.key !== 'Tab') return
    const nodes = panelRef.current?.querySelectorAll<HTMLElement>(
      'input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), a[href]',
    )
    if (!nodes || nodes.length === 0) return
    const firstEl = nodes[0]
    const lastEl = nodes[nodes.length - 1]
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
        className={wide ? 'dialog dialog-wide' : 'dialog'}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={panelRef}
      >
        <h2>{title}</h2>
        {children}
      </div>
    </div>
  )
}
