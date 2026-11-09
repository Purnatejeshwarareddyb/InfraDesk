import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, buildQuery, request, setUnauthorizedHandler } from '../api/client'
import { errorResponse, jsonResponse } from './helpers'

afterEach(() => setUnauthorizedHandler(null))

describe('api client', () => {
  it('parses the backend error shape into an ApiError', async () => {
    vi.stubGlobal('fetch', vi.fn(async () =>
      errorResponse(422, 'validation_error', 'The request contains invalid data.', [
        { field: 'title', message: 'Too short' },
      ])))
    const err = await request('/api/v1/tickets', { method: 'POST', body: {} }).catch((e: unknown) => e)
    expect(err).toBeInstanceOf(ApiError)
    const apiErr = err as ApiError
    expect(apiErr.status).toBe(422)
    expect(apiErr.code).toBe('validation_error')
    expect(apiErr.message).toBe('The request contains invalid data.')
    expect(apiErr.fieldErrors).toEqual({ title: 'Too short' })
  })

  it('survives non-JSON error bodies', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('<html>Bad gateway</html>', { status: 502 })))
    const err = (await request('/x').catch((e: unknown) => e)) as ApiError
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(502)
    expect(err.message).toMatch(/server/i)
  })

  it('reports network failures as an ApiError with status 0', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('Failed to fetch') }))
    const err = (await request('/x').catch((e: unknown) => e)) as ApiError
    expect(err.status).toBe(0)
    expect(err.code).toBe('network_error')
  })

  it('calls the unauthorized handler on 401', async () => {
    const handler = vi.fn()
    setUnauthorizedHandler(handler)
    vi.stubGlobal('fetch', vi.fn(async () => errorResponse(401, 'session_expired', 'Your session has expired.')))
    await expect(request('/api/v1/tickets')).rejects.toMatchObject({ status: 401 })
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('does not call the handler on 401 when skipUnauthorizedHandler is set (login)', async () => {
    const handler = vi.fn()
    setUnauthorizedHandler(handler)
    vi.stubGlobal('fetch', vi.fn(async () => errorResponse(401, 'invalid_credentials', 'Incorrect username or password.')))
    await expect(request('/api/v1/auth/login', { method: 'POST', skipUnauthorizedHandler: true })).rejects.toThrow(
      'Incorrect username or password.',
    )
    expect(handler).not.toHaveBeenCalled()
  })

  it('sends same-origin credentials and JSON bodies', async () => {
    const fetchMock = vi.fn(async () => jsonResponse({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    await request('/api/v1/tickets', { method: 'POST', body: { a: 1 } })
    const call = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(call[1].credentials).toBe('same-origin')
    expect(call[1].body).toBe('{"a":1}')
  })

  it('builds query strings without empty values', () => {
    expect(buildQuery({ q: 'a b', status: '', page: 2, mine: false, x: undefined })).toBe('?q=a+b&page=2')
    expect(buildQuery({})).toBe('')
  })
})
