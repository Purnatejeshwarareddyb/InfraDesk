import { useAuth } from '../../auth/authContext'
import { PageHeader } from '../../components/PageHeader'
import { ROLE_LABEL } from '../../utils/labels'
import { ChangePasswordForm } from '../shared/ChangePasswordForm'

export function Account() {
  const { user } = useAuth()
  return (
    <>
      <PageHeader title="My account" />
      <section className="panel" aria-label="Profile">
        <dl className="facts">
          <div><dt>Name</dt><dd>{user?.display_name}</dd></div>
          <div><dt>Username</dt><dd className="mono">{user?.username}</dd></div>
          <div><dt>Role</dt><dd>{user ? ROLE_LABEL[user.role] : ''}</dd></div>
        </dl>
      </section>
      <section className="panel" aria-label="Change password">
        <h2 className="panel-title">Change your password</h2>
        <ChangePasswordForm />
      </section>
    </>
  )
}
