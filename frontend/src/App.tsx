import { Navigate, Route, Routes } from 'react-router-dom'
import { homePath, useAuth } from './auth/authContext'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppShell } from './components/AppShell'
import { Loading } from './components/StateViews'
import { Activity } from './pages/admin/Activity'
import { Assets } from './pages/admin/Assets'
import { Reports } from './pages/admin/Reports'
import { Settings } from './pages/admin/Settings'
import { Users } from './pages/admin/Users'
import { Login } from './pages/Login'
import { NotFound } from './pages/NotFound'
import { Dashboard } from './pages/shared/Dashboard'
import { Notifications } from './pages/shared/Notifications'
import { TicketDetail } from './pages/shared/TicketDetail'
import { TicketForm } from './pages/shared/TicketForm'
import { TicketList } from './pages/shared/TicketList'
import { Account } from './pages/worker/Account'

function RootRedirect() {
  const { user, initializing } = useAuth()
  if (initializing) return <Loading label="Checking your session" />
  return <Navigate to={user ? homePath(user.role) : '/login'} replace />
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<RootRedirect />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/admin"
        element={
          <ProtectedRoute role="ADMIN">
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard admin />} />
        <Route path="tickets" element={<TicketList admin />} />
        <Route path="tickets/new" element={<TicketForm admin />} />
        <Route path="tickets/:id" element={<TicketDetail admin />} />
        <Route path="users" element={<Users />} />
        <Route path="assets" element={<Assets />} />
        <Route path="reports" element={<Reports />} />
        <Route path="activity" element={<Activity />} />
        <Route path="notifications" element={<Notifications admin />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route
        path="/worker"
        element={
          <ProtectedRoute role="WORKER">
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard admin={false} />} />
        <Route path="tickets" element={<TicketList admin={false} />} />
        <Route path="tickets/new" element={<TicketForm admin={false} />} />
        <Route path="tickets/:id" element={<TicketDetail admin={false} />} />
        <Route path="notifications" element={<Notifications admin={false} />} />
        <Route path="account" element={<Account />} />
        <Route path="*" element={<NotFound />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
