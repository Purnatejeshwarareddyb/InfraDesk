export interface FieldError {
  field: string
  message: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: FieldError[]

  constructor(status: number, code: string, message: string, details: FieldError[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }

  /** Map of field name to message, for showing errors beside form inputs. */
  get fieldErrors(): Record<string, string> {
    const out: Record<string, string> = {}
    for (const d of this.details) {
      const key = d.field.split('.').pop() ?? d.field
      if (!(key in out)) out[key] = d.message
    }
    return out
  }
}

export const API_BASE: string = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''

type Query = Record<string, string | number | boolean | null | undefined>

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH'
  query?: Query
  body?: unknown
  /** Login and the start-up session probe must not trigger the "session expired" redirect. */
  skipUnauthorizedHandler?: boolean
  signal?: AbortSignal
}

let unauthorizedHandler: (() => void) | null = null

/** The auth provider registers what happens on a 401 (clear state, go to /login). */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

export function buildQuery(query?: Query): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === '' || value === false) continue
    params.set(key, String(value))
  }
  const text = params.toString()
  return text ? `?${text}` : ''
}

export function apiUrl(path: string, query?: Query): string {
  return `${API_BASE}${path}${buildQuery(query)}`
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function parseDetails(value: unknown): FieldError[] {
  if (!Array.isArray(value)) return []
  const out: FieldError[] = []
  for (const item of value) {
    if (isRecord(item) && typeof item.message === 'string') {
      out.push({ field: typeof item.field === 'string' ? item.field : 'request', message: item.message })
    }
  }
  return out
}

/** Turn any failed response into an ApiError without ever throwing a parsing error. */
export async function parseError(response: Response): Promise<ApiError> {
  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }
  if (isRecord(payload) && isRecord(payload.error)) {
    const err = payload.error
    const code = typeof err.code === 'string' ? err.code : 'http_error'
    const message = typeof err.message === 'string' ? err.message : fallbackMessage(response.status)
    return new ApiError(response.status, code, message, parseDetails(err.details))
  }
  return new ApiError(response.status, 'http_error', fallbackMessage(response.status))
}

function fallbackMessage(status: number): string {
  if (status === 401) return 'Your session has expired. Please sign in again.'
  if (status === 403) return 'You do not have permission to do that.'
  if (status === 404) return 'That item could not be found.'
  if (status >= 500) return 'The server had a problem. Please try again.'
  return 'The request failed. Please try again.'
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', query, body, skipUnauthorizedHandler = false, signal } = options
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let response: Response
  try {
    response = await fetch(apiUrl(path, query), {
      method,
      headers,
      credentials: 'same-origin',
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    })
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause
    throw new ApiError(0, 'network_error', 'Cannot reach the InfraDesk server. Check the connection and try again.')
  }

  if (!response.ok) {
    const error = await parseError(response)
    if (response.status === 401 && !skipUnauthorizedHandler) unauthorizedHandler?.()
    throw error
  }
  if (response.status === 204) return undefined as T
  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError(response.status, 'invalid_response', 'The server sent an unreadable response.')
  }
}

export function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Something went wrong.'
}
