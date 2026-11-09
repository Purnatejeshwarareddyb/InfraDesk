import { healthApi } from '../../api/endpoints'
import { PageHeader } from '../../components/PageHeader'
import { DataState } from '../../components/StateViews'
import { useAsync } from '../../hooks/useAsync'
import { ChangePasswordForm } from '../shared/ChangePasswordForm'

export function Settings() {
  const health = useAsync(() => healthApi.health(), [])
  const origin = window.location.origin
  return (
    <>
      <PageHeader title="Settings and help" subtitle="About this installation and your own account." />
      <div className="grid-2">
        <section className="panel" aria-label="About InfraDesk">
          <h2 className="panel-title">About this installation</h2>
          <DataState loading={health.loading} error={health.error} onRetry={health.reload} hasData={health.data !== null}>
            {health.data && (
              <dl className="facts">
                <div><dt>Application</dt><dd>{health.data.app}</dd></div>
                <div><dt>Version</dt><dd>{health.data.version}</dd></div>
                <div><dt>Service status</dt><dd>{health.data.status}</dd></div>
              </dl>
            )}
          </DataState>
          <h3>Local addresses</h3>
          <ul className="plain-list">
            <li>Web app: <span className="mono">{origin}</span></li>
            <li><a href="/docs">API documentation</a> (<span className="mono">{origin}/docs</span>)</li>
            <li><a href="/health">Health check</a> (<span className="mono">{origin}/health</span>)</li>
            <li><a href="/ready">Readiness check</a> (<span className="mono">{origin}/ready</span>)</li>
          </ul>
        </section>
        <section className="panel" aria-label="Usage notes">
          <h2 className="panel-title">Usage notes</h2>
          <ul className="plain-list">
            <li>New tickets start as Open. Assign one to a person from its detail page; it then becomes Assigned.</li>
            <li>The assignee moves a ticket through In progress, Waiting and Resolved. A resolution note is required to resolve.</li>
            <li>Only administrators close a ticket or reopen a closed one.</li>
            <li>Deactivating a user signs them out at once. Their past tickets stay in the history.</li>
            <li>Reports and the CSV download use ticket creation dates.</li>
            <li>Retired assets stay in the list but cannot be linked to new tickets.</li>
          </ul>
        </section>
      </div>
      <section className="panel" aria-label="Change password">
        <h2 className="panel-title">Change your password</h2>
        <ChangePasswordForm />
      </section>
    </>
  )
}
