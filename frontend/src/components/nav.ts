import type { Role } from '../api/types'

export interface NavItem {
  to: string
  label: string
  end?: boolean
}

export function navItems(role: Role): NavItem[] {
  if (role === 'ADMIN') {
    return [
      { to: '/admin', label: 'Dashboard', end: true },
      { to: '/admin/tickets', label: 'Tickets' },
      { to: '/admin/users', label: 'Users' },
      { to: '/admin/assets', label: 'Assets' },
      { to: '/admin/reports', label: 'Reports' },
      { to: '/admin/activity', label: 'Activity' },
      { to: '/admin/notifications', label: 'Notifications' },
      { to: '/admin/settings', label: 'Settings and help' },
    ]
  }
  return [
    { to: '/worker', label: 'Dashboard', end: true },
    { to: '/worker/tickets', label: 'My tickets' },
    { to: '/worker/tickets/new', label: 'Create ticket' },
    { to: '/worker/notifications', label: 'Notifications' },
    { to: '/worker/account', label: 'My account' },
  ]
}
