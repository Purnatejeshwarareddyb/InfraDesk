import { useEffect, useState, type FormEvent } from 'react'
import { ApiError, errorMessage } from '../../api/client'
import { assetsApi, type AssetInput } from '../../api/endpoints'
import { ASSET_STATUSES, ASSET_TYPES, type Asset, type AssetStatus, type AssetType } from '../../api/types'
import { Chip } from '../../components/Badges'
import { ConfirmDialog } from '../../components/ConfirmDialog'
import { DataTable, type Column } from '../../components/DataTable'
import { FormField } from '../../components/FormField'
import { Modal } from '../../components/Modal'
import { PageHeader } from '../../components/PageHeader'
import { Pagination } from '../../components/Pagination'
import { DataState } from '../../components/StateViews'
import { useToast } from '../../components/Toast'
import { useAsync } from '../../hooks/useAsync'
import { useDebounced } from '../../hooks/useDebounced'
import { ASSET_STATUS_LABEL, ASSET_TYPE_LABEL } from '../../utils/labels'

type Dialog = { kind: 'form'; asset: Asset | null } | { kind: 'retire'; asset: Asset } | null

const TONE: Record<AssetStatus, 'good' | 'warn' | 'muted'> = { ACTIVE: 'good', IN_REPAIR: 'warn', RETIRED: 'muted' }

export function Assets() {
  const toast = useToast()
  const [search, setSearch] = useState('')
  const q = useDebounced(search)
  const [status, setStatus] = useState<AssetStatus | ''>('')
  const [type, setType] = useState<AssetType | ''>('')
  const [hideRetired, setHideRetired] = useState(false)
  const [page, setPage] = useState(1)
  const [dialog, setDialog] = useState<Dialog>(null)
  const list = useAsync(
    () => assetsApi.list({ q, status, asset_type: type, include_retired: !hideRetired, page, page_size: 20 }),
    [q, status, type, hideRetired, page],
  )
  useEffect(() => setPage(1), [q, status, type, hideRetired])

  const columns: Column<Asset>[] = [
    { key: 'tag', header: 'Tag', render: (a) => <span className="mono">{a.asset_tag}</span> },
    { key: 'name', header: 'Name', render: (a) => <strong>{a.name}</strong> },
    { key: 'type', header: 'Type', render: (a) => ASSET_TYPE_LABEL[a.asset_type] },
    { key: 'location', header: 'Location', render: (a) => a.location || '-' },
    { key: 'serial', header: 'Serial number', render: (a) => a.serial_number ?? '-' },
    { key: 'status', header: 'Status', render: (a) => <Chip tone={TONE[a.status]}>{ASSET_STATUS_LABEL[a.status]}</Chip> },
    {
      key: 'actions',
      header: 'Actions',
      render: (a) => (
        <div className="button-row">
          <button type="button" className="btn btn-small" onClick={() => setDialog({ kind: 'form', asset: a })}>Edit</button>
          {a.status !== 'RETIRED' && (
            <button type="button" className="btn btn-small btn-danger-outline" onClick={() => setDialog({ kind: 'retire', asset: a })}>Retire</button>
          )}
        </div>
      ),
    },
  ]

  function done(message: string) {
    toast.success(message)
    setDialog(null)
    list.reload()
  }

  return (
    <>
      <PageHeader
        title="Assets"
        subtitle="Equipment that tickets can refer to."
        actions={<button type="button" className="btn btn-primary" onClick={() => setDialog({ kind: 'form', asset: null })}>Create asset</button>}
      />
      <form className="filters" role="search" aria-label="Filter assets" onSubmit={(e) => e.preventDefault()}>
        <div className="field field-grow">
          <label htmlFor="a-search">Search</label>
          <input id="a-search" type="search" placeholder="Tag, name, location or serial" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="a-type">Type</label>
          <select id="a-type" value={type} onChange={(e) => setType(e.target.value as AssetType | '')}>
            <option value="">All types</option>
            {ASSET_TYPES.map((t) => <option key={t} value={t}>{ASSET_TYPE_LABEL[t]}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="a-status">Status</label>
          <select id="a-status" value={status} onChange={(e) => setStatus(e.target.value as AssetStatus | '')}>
            <option value="">All statuses</option>
            {ASSET_STATUSES.map((s) => <option key={s} value={s}>{ASSET_STATUS_LABEL[s]}</option>)}
          </select>
        </div>
        <label className="check">
          <input type="checkbox" checked={hideRetired} onChange={(e) => setHideRetired(e.target.checked)} />
          Hide retired
        </label>
      </form>
      <DataState
        loading={list.loading} error={list.error} onRetry={list.reload} hasData={list.data !== null}
        empty={list.data !== null && list.data.total === 0} emptyTitle="No assets match" emptyHint="Change the filters or create an asset."
      >
        {list.data && (
          <>
            <DataTable caption="Assets" columns={columns} rows={list.data.items} rowKey={(a) => a.id} />
            <Pagination page={list.data.page} pages={list.data.pages} total={list.data.total} pageSize={list.data.page_size} onPage={setPage} />
          </>
        )}
      </DataState>
      {dialog?.kind === 'form' && <AssetForm asset={dialog.asset} onClose={() => setDialog(null)} onDone={done} />}
      {dialog?.kind === 'retire' && <RetireAsset asset={dialog.asset} onClose={() => setDialog(null)} onDone={done} />}
    </>
  )
}

interface DialogProps {
  onClose: () => void
  onDone: (message: string) => void
}

function AssetForm({ asset, onClose, onDone }: DialogProps & { asset: Asset | null }) {
  const [tag, setTag] = useState(asset?.asset_tag ?? '')
  const [name, setName] = useState(asset?.name ?? '')
  const [type, setType] = useState<AssetType>(asset?.asset_type ?? 'OTHER')
  const [location, setLocation] = useState(asset?.location ?? '')
  const [serial, setSerial] = useState(asset?.serial_number ?? '')
  const [status, setStatus] = useState<AssetStatus>(asset?.status ?? 'ACTIVE')
  const [notes, setNotes] = useState(asset?.notes ?? '')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const statuses = asset?.status === 'RETIRED' ? ASSET_STATUSES : ASSET_STATUSES.filter((s) => s !== 'RETIRED')

  async function submit(e: FormEvent) {
    e.preventDefault()
    setServerError(null)
    const found: Record<string, string> = {}
    if (tag.trim().length < 2) found.asset_tag = 'Enter a tag of at least 2 characters.'
    if (name.trim().length < 2) found.name = 'Enter a name of at least 2 characters.'
    setErrors(found)
    if (Object.keys(found).length > 0) return
    const input: AssetInput = {
      asset_tag: tag.trim(), name: name.trim(), asset_type: type, location: location.trim(),
      serial_number: serial.trim() || null, status, notes: notes.trim(),
    }
    setBusy(true)
    try {
      if (asset) {
        await assetsApi.update(asset.id, { ...input, serial_number: serial.trim() })
        onDone(`Asset ${input.asset_tag.toUpperCase()} updated.`)
      } else {
        await assetsApi.create(input)
        onDone(`Asset ${input.asset_tag.toUpperCase()} created.`)
      }
    } catch (err) {
      if (err instanceof ApiError) setErrors(err.fieldErrors)
      setServerError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <Modal title={asset ? `Edit ${asset.asset_tag}` : 'Create asset'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <div className="form-row">
          <FormField label="Asset tag" required error={errors.asset_tag}>
            {(c) => <input {...c} value={tag} onChange={(e) => setTag(e.target.value)} />}
          </FormField>
          <FormField label="Name" required error={errors.name}>
            {(c) => <input {...c} value={name} onChange={(e) => setName(e.target.value)} />}
          </FormField>
        </div>
        <div className="form-row">
          <FormField label="Type">
            {(c) => (
              <select {...c} value={type} onChange={(e) => setType(e.target.value as AssetType)}>
                {ASSET_TYPES.map((t) => <option key={t} value={t}>{ASSET_TYPE_LABEL[t]}</option>)}
              </select>
            )}
          </FormField>
          <FormField label="Status">
            {(c) => (
              <select {...c} value={status} onChange={(e) => setStatus(e.target.value as AssetStatus)}>
                {statuses.map((s) => <option key={s} value={s}>{ASSET_STATUS_LABEL[s]}</option>)}
              </select>
            )}
          </FormField>
        </div>
        <div className="form-row">
          <FormField label="Location" error={errors.location}>
            {(c) => <input {...c} value={location} onChange={(e) => setLocation(e.target.value)} />}
          </FormField>
          <FormField label="Serial number" error={errors.serial_number}>
            {(c) => <input {...c} value={serial} onChange={(e) => setSerial(e.target.value)} />}
          </FormField>
        </div>
        <FormField label="Notes" error={errors.notes}>
          {(c) => <textarea {...c} rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />}
        </FormField>
        {serverError && <p className="form-error" role="alert">{serverError}</p>}
        <div className="dialog-actions">
          <button type="button" className="btn" onClick={onClose} disabled={busy}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Saving...' : asset ? 'Save changes' : 'Create asset'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function RetireAsset({ asset, onClose, onDone }: DialogProps & { asset: Asset }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function run() {
    setBusy(true)
    setError(null)
    try {
      await assetsApi.retire(asset.id)
      onDone(`Asset ${asset.asset_tag} retired.`)
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }
  return (
    <ConfirmDialog
      open
      title={`Retire ${asset.asset_tag}?`}
      message="A retired asset can no longer be linked to new tickets."
      confirmLabel="Retire asset"
      danger
      busy={busy}
      error={error}
      onConfirm={run}
      onCancel={onClose}
    />
  )
}
