import { useId, type ReactNode } from 'react'

export interface ControlProps {
  id: string
  'aria-invalid': boolean | undefined
  'aria-describedby': string | undefined
  'aria-required': boolean | undefined
}

interface Props {
  label: string
  error?: string | null
  hint?: string
  required?: boolean
  children: (control: ControlProps) => ReactNode
}

export function FormField({ label, error, hint, required, children }: Props) {
  const uid = useId()
  const id = `f${uid.replace(/:/g, '')}`
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ') || undefined
  return (
    <div className={error ? 'field field-invalid' : 'field'}>
      <label htmlFor={id}>
        {label}
        {required && <span className="required"> (required)</span>}
      </label>
      {children({
        id,
        'aria-invalid': error ? true : undefined,
        'aria-describedby': describedBy,
        'aria-required': required ? true : undefined,
      })}
      {hint && (
        <p className="field-hint" id={hintId}>
          {hint}
        </p>
      )}
      {error && (
        <p className="field-error" id={errorId}>
          {error}
        </p>
      )}
    </div>
  )
}
