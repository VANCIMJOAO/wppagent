import { renderHook, act } from '@testing-library/react'
import { useApi, useApiGet, useApiPost } from '@/hooks/useApi'

// Mock fetch
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

describe('useApi', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  it('should handle successful API request', async () => {
    const mockData = { id: 1, name: 'Test User' }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response)

    const { result } = renderHook(() => useApi<typeof mockData>())

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()

    await act(async () => {
      await result.current.request('/test-endpoint')
    })

    expect(result.current.data).toEqual(mockData)
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(mockFetch).toHaveBeenCalledWith(
      'https://wppagent-production.up.railway.app/test-endpoint',
      expect.objectContaining({
        headers: {
          'Content-Type': 'application/json',
        },
      })
    )
  })

  it('should handle API request errors', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useApi())

    await act(async () => {
      await result.current.request('/test-endpoint')
    })

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBe('Network error')
  })

  it('should handle HTTP error responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    } as Response)

    const { result } = renderHook(() => useApi())

    await act(async () => {
      await result.current.request('/test-endpoint')
    })

    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBe('HTTP 404: Not Found')
  })

  it('should retry failed requests', async () => {
    // Fail first 2 attempts, succeed on third
    mockFetch
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      } as Response)

    const { result } = renderHook(() => useApi({ retries: 3, retryDelay: 10 }))

    await act(async () => {
      await result.current.request('/test-endpoint')
    })

    expect(result.current.data).toEqual({ success: true })
    expect(result.current.error).toBeNull()
    expect(mockFetch).toHaveBeenCalledTimes(3)
  })

  it('should cancel requests when reset is called', async () => {
    // Mock a slow request
    const mockAbortController = {
      signal: { aborted: false },
      abort: jest.fn(),
    }
    jest.spyOn(global, 'AbortController').mockImplementation(() => mockAbortController as any)

    const { result } = renderHook(() => useApi())

    // Start a request
    act(() => {
      result.current.request('/test-endpoint')
    })

    expect(result.current.loading).toBe(true)

    // Reset should cancel the request
    act(() => {
      result.current.reset()
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.data).toBeNull()
    expect(result.current.error).toBeNull()
    expect(mockAbortController.abort).toHaveBeenCalled()
  })

  it('should use custom base URL', async () => {
    const customBaseUrl = 'https://custom-api.com'
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    } as Response)

    const { result } = renderHook(() => useApi({ baseUrl: customBaseUrl }))

    await act(async () => {
      await result.current.request('/test-endpoint')
    })

    expect(mockFetch).toHaveBeenCalledWith(
      `${customBaseUrl}/test-endpoint`,
      expect.any(Object)
    )
  })
})

describe('useApiGet', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  it('should make GET request', async () => {
    const mockData = { message: 'Success' }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response)

    const { result } = renderHook(() => useApiGet<typeof mockData>('/users'))

    await act(async () => {
      await result.current.get()
    })

    expect(result.current.data).toEqual(mockData)
    expect(mockFetch).toHaveBeenCalledWith(
      'https://wppagent-production.up.railway.app/users',
      expect.objectContaining({
        method: 'GET',
      })
    )
  })
})

describe('useApiPost', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  it('should make POST request with body', async () => {
    const mockData = { id: 1, created: true }
    const postData = { name: 'New User', email: 'user@test.com' }
    
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response)

    const { result } = renderHook(() => useApiPost<typeof mockData>())

    await act(async () => {
      await result.current.post('/users', postData)
    })

    expect(result.current.data).toEqual(mockData)
    expect(mockFetch).toHaveBeenCalledWith(
      'https://wppagent-production.up.railway.app/users',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(postData),
        headers: {
          'Content-Type': 'application/json',
        },
      })
    )
  })
})
