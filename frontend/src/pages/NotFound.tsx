import { Link } from 'react-router-dom'
import { homePath, useAuth } from '../auth/authContext'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

export function NotFound() {
  const { user } = useAuth()
  const Wrapper = user ? 'div' : 'main'
  useDocumentTitle('Page not found')
  return (
    <Wrapper className="centered-page">
      <h1>Page not found</h1>
      <p>The address you opened does not exist in InfraDesk.</p>
      <Link className="btn btn-primary" to={user ? homePath(user.role) : '/login'}>
        {user ? 'Go to your dashboard' : 'Go to sign in'}
      </Link>
    </Wrapper>
  )
}
