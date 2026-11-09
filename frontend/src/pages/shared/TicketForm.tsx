import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError } from '../../api/client'
import { assetsApi, ticketsApi } from '../../api/endpoints'
import { CATEGORIES, PRIORITIES, type Category, type Priority } from '../../api/types'
import { FormField } from '../../components/FormField'
import { PageHeader } from '../../components/PageHeader'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../hooks/useAsync'
import { CATEGORY_LABEL, PRIORITY_LABEL } from '../../utils/labels'
import { validateTicket, type TicketErrors } from '../../utils/validation'

type Errors = TicketErrors

export function TicketForm({ admin }: { admin: boolean }) {
  const base = admin ? '/admin' : '/worker'
  const navigate = useNavigate()
  const toast = useToast()
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState<Category>('OTHER')
  const [priority, setPriority] = useState<Priority>('MEDIUM')
  const [assetId, setAssetId] = useState('')
  const [errors, setErrors] = useState<Errors>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const assets = useAsync(() => assetsApi.list({ include_retired: false, page_size: 100 }), [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setServerError(null)
    const found = validateTicket(title, description)
    setErrors(found)
    if (Object.keys(found).length > 0) return
    setBusy(true)
    try {
      const ticket = await ticketsApi.create({
        title: title.trim(),
        description: description.trim(),
        category,
        priority,
        related_asset_id: assetId ? Number(assetId) : null,
      })
      toast.success(`Ticket ${ticket.ticket_number} created.`)
      navigate(`${base}/tickets/${ticket.id}`)
    } catch (err) {
      if (err instanceof ApiError) {
        const fields = err.fieldErrors
        setErrors({ title: fields.title, description: fields.description })
        setServerError(err.message)
      } else {
        setServerError('The ticket could not be created.')
      }
      setBusy(false)
    }
  }

  return (
    <>
      <PageHeader title="Create ticket" subtitle="Describe the problem so the right person can pick it up." />
      <form className="panel form-narrow" onSubmit={onSubmit} noValidate>
        <FormField label="Title" required error={errors.title}>
          {(c) => <input {...c} value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />}
        </FormField>
        <FormField label="Description" required error={errors.description} hint="What happened, where, and since when.">
          {(c) => <textarea {...c} rows={6} value={description} onChange={(e) => setDescription(e.target.value)} />}
        </FormField>
        <div className="form-row">
          <FormField label="Category">
            {(c) => (
              <select {...c} value={category} onChange={(e) => setCategory(e.target.value as Category)}>
                {CATEGORIES.map((v) => <option key={v} value={v}>{CATEGORY_LABEL[v]}</option>)}
              </select>
            )}
          </FormField>
          <FormField label="Priority">
            {(c) => (
              <select {...c} value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
                {PRIORITIES.map((v) => <option key={v} value={v}>{PRIORITY_LABEL[v]}</option>)}
              </select>
            )}
          </FormField>
        </div>
        <FormField
          label="Related asset (optional)"
          hint={assets.error ? 'Assets could not be loaded. You can still submit without one.' : undefined}
        >
          {(c) => (
            <select {...c} value={assetId} onChange={(e) => setAssetId(e.target.value)} disabled={assets.loading}>
              <option value="">{assets.loading ? 'Loading assets...' : 'No related asset'}</option>
              {assets.data?.items.map((a) => (
                <option key={a.id} value={a.id}>{a.asset_tag} - {a.name}</option>
              ))}
            </select>
          )}
        </FormField>
        {serverError && <p className="form-error" role="alert">{serverError}</p>}
        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Creating...' : 'Create ticket'}
          </button>
          <button type="button" className="btn" onClick={() => navigate(`${base}/tickets`)} disabled={busy}>
            Cancel
          </button>
        </div>
      </form>
    </>
  )
}
