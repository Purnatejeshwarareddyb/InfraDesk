/**
 * The backend sends ISO timestamps in UTC. SQLite can drop the zone suffix, so a value
 * without one is treated as UTC. Everything is shown in the browser's local time zone.
 */
export function parseApiDate(value: string): Date {
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/i.test(value)
  return new Date(hasZone ? value : `${value}Z`)
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '-'
  const date = parseApiDate(value)
  if (Number.isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '-'
  const date = parseApiDate(value)
  if (Number.isNaN(date.getTime())) return '-'
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(date)
}
