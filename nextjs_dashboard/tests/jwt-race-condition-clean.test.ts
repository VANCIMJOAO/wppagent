/**
 * 🧪 JWT Token Race Condition Resolution Test
 * ==========================================
 * 
 * Jest tests para validar que o TokenManager resolve
 * completamente os problemas de race condition.
 * 
 * Status: Validação da solução JWT Race Condition
 */

// Mock localStorage for testing
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

// Mock fetch for token refresh
global.fetch = jest.fn();

// Setup mocks before importing tokenManager
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Dynamic import to ensure mocks are set up first
let tokenManager: any;

beforeAll(async () => {
  const { tokenManager: tm } = await import('../lib/token-manager');
  tokenManager = tm;
});

describe('JWT Token Race Condition Resolution', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  /**
   * Test 1: Multiple simultaneous token refresh requests
   */
  it('should handle multiple simultaneous refresh requests without race conditions', async () => {
    // Setup expired token
    const expiredToken = createMockExpiredToken();
    localStorageMock.setItem('access_token', expiredToken);
    localStorageMock.setItem('refresh_token', 'mock_refresh_token');

    // Mock successful refresh response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'new_access_token',
        refresh_token: 'new_refresh_token',
      }),
    });

    // Create 10 simultaneous refresh requests
    const refreshPromises = Array.from({ length: 10 }, () => 
      tokenManager.getValidToken()
    );

    const results = await Promise.all(refreshPromises);

    // All results should be the same (no race condition)
    expect(results.every((token: string) => token === 'new_access_token')).toBe(true);
    
    // Fetch should only be called once due to mutex
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  /**
   * Test 2: Token validation works correctly
   */
  it('should correctly validate token expiry', () => {
    const validToken = createMockValidToken();
    const expiredToken = createMockExpiredToken();

    expect(tokenManager.isTokenExpired(validToken)).toBe(false);
    expect(tokenManager.isTokenExpired(expiredToken)).toBe(true);
  });

  /**
   * Test 3: Auth state management
   */
  it('should manage authentication state correctly', () => {
    // Clear tokens first
    tokenManager.clearTokens();
    
    // No token = not authenticated
    expect(tokenManager.isAuthenticated()).toBe(false);

    // Valid token = authenticated
    const validToken = createMockValidToken();
    localStorageMock.setItem('access_token', validToken);
    expect(tokenManager.isAuthenticated()).toBe(true);

    // Expired token = not authenticated
    const expiredToken = createMockExpiredToken();
    localStorageMock.setItem('access_token', expiredToken);
    expect(tokenManager.isAuthenticated()).toBe(false);
  });

  /**
   * Test 4: Token cleanup
   */
  it('should clear tokens correctly', () => {
    localStorageMock.setItem('access_token', 'test_access_token');
    localStorageMock.setItem('refresh_token', 'test_refresh_token');

    tokenManager.clearTokens();

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token');
  });

  /**
   * Test 5: Token info extraction
   */
  it('should extract token info correctly', () => {
    const validToken = createMockValidToken();
    localStorageMock.setItem('access_token', validToken);

    const tokenInfo = tokenManager.getTokenInfo();

    expect(tokenInfo).not.toBeNull();
    expect(tokenInfo?.user_id).toBe('test-user');
    expect(tokenInfo?.email).toBe('test@example.com');
  });

  /**
   * Test 6: Concurrent access during token refresh
   */
  it('should handle concurrent access during token refresh', async () => {
    const nearExpiredToken = createMockNearExpiredToken();
    localStorageMock.setItem('access_token', nearExpiredToken);
    localStorageMock.setItem('refresh_token', 'mock_refresh_token');

    // Mock refresh response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access_token: 'refreshed_access_token',
        refresh_token: 'refreshed_refresh_token',
      }),
    });

    // Create multiple concurrent requests
    const concurrentRequests = [
      tokenManager.getValidToken(),
      tokenManager.isAuthenticated(),
      tokenManager.getTokenInfo(),
      tokenManager.getValidToken(),
      tokenManager.getValidToken()
    ];

    const results = await Promise.all(concurrentRequests);

    // First and last should be tokens, middle ones should work
    expect(results[0]).toBe('refreshed_access_token');
    expect(results[1]).toBe(true);
    expect(results[2]).toBeTruthy();
    expect(results[3]).toBe('refreshed_access_token');
    expect(results[4]).toBe('refreshed_access_token');
  });
});

/**
 * Helper: Create mock expired token
 */
function createMockExpiredToken(): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    exp: Math.floor(Date.now() / 1000) - 3600, // Expired 1 hour ago
    iat: Math.floor(Date.now() / 1000) - 7200,
    user_id: 'test-user',
    email: 'test@example.com'
  }));
  const signature = 'mock-signature';
  return `${header}.${payload}.${signature}`;
}

/**
 * Helper: Create mock valid token
 */
function createMockValidToken(): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    exp: Math.floor(Date.now() / 1000) + 3600, // Expires in 1 hour
    iat: Math.floor(Date.now() / 1000),
    user_id: 'test-user',
    email: 'test@example.com'
  }));
  const signature = 'mock-signature';
  return `${header}.${payload}.${signature}`;
}

/**
 * Helper: Create mock near-expired token
 */
function createMockNearExpiredToken(): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({
    exp: Math.floor(Date.now() / 1000) + 30, // Expires in 30 seconds
    iat: Math.floor(Date.now() / 1000) - 3600,
    user_id: 'test-user',
    email: 'test@example.com'
  }));
  const signature = 'mock-signature';
  return `${header}.${payload}.${signature}`;
}
