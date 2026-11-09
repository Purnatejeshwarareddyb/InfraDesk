import type { AuditEvent } from '../api/types'
import { prettyValue } from './labels'

export function describeEvent(e: AuditEvent): string {
  const parts: string[] = []
  if (e.old_value && e.new_value) parts.push(`${prettyValue(e.old_value)} to ${prettyValue(e.new_value)}`)
  else if (e.new_value) parts.push(prettyValue(e.new_value))
  if (e.detail) parts.push(e.detail)
  return parts.join('. ')
}
