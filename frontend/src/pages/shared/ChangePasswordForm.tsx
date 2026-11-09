import { useState, type FormEvent } from 'react'
import { errorMessage } from '../../api/client'
import { authApi } from '../../api/endpoints'
import { FormField } from '../../components/FormField'
import { passwordProblem } from '../../utils/validation'

export function ChangePasswordForm() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [errors, setErrors] = useState<{ current?: string; next?: string; confirm?: string }>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setServerError(null)
    setSuccess(null)
    const found: typeof errors = {}
    if (!current) found.current = 'Enter your current password.'
    const problem = passwordProblem(next)
    if (problem) found.next = problem
    if (confirm !== next) found.confirm = 'The two new passwords do not match.'
    setErrors(found)
    if (Object.keys(found).length > 0) return
    setBusy(true)
    try {
      await authApi.changePassword(current, next)
      setSuccess('Your password was changed.')
      setCurrent('')
      setNext('')
      setConfirm('')
    } catch (err) {
      setServerError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="form-narrow" onSubmit={submit} noValidate>
      <FormField label="Current password" error={errors.current}>
        {(c) => <input {...c} type="password" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} />}
      </FormField>
      <FormField label="New password" error={errors.next} hint="At least 10 characters with upper-case, lower-case and a digit.">
        {(c) => <input {...c} type="password" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} />}
      </FormField>
      <FormField label="Repeat new password" error={errors.confirm}>
        {(c) => <input {...c} type="password" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />}
      </FormField>
      {serverError && <p className="form-error" role="alert">{serverError}</p>}
      {success && <p className="notice notice-good" role="status">{success}</p>}
      <button type="submit" className="btn btn-primary" disabled={busy}>
        {busy ? 'Changing...' : 'Change password'}
      </button>
    </form>
  )
}
