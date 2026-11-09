export type TicketErrors = Partial<Record<'title' | 'description', string>>

export function validateTicket(title: string, description: string): TicketErrors {
  const errors: TicketErrors = {}
  const t = title.trim()
  const d = description.trim()
  if (t.length < 5) errors.title = 'Enter a title of at least 5 characters.'
  else if (t.length > 160) errors.title = 'The title must be 160 characters or fewer.'
  if (d.length < 10) errors.description = 'Describe the problem in at least 10 characters.'
  else if (d.length > 5000) errors.description = 'The description must be 5000 characters or fewer.'
  return errors
}

/** Mirrors the backend password rule so people get feedback before sending. */
export function passwordProblem(value: string): string | null {
  if (value.length < 10) return 'Use at least 10 characters.'
  if (value.length > 128) return 'Use 128 characters or fewer.'
  if (value.toLowerCase() === value || value.toUpperCase() === value || !/\d/.test(value)) {
    return 'Include upper-case and lower-case letters and a digit.'
  }
  return null
}
