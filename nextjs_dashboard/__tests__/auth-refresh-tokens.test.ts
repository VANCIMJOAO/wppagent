/**
 * 🧪 Testes Frontend - Sistema de Refresh Tokens
 * ===============================================
 * 
 * Testa funcionalidades do AuthService e hooks de autenticação:
 * - Login e armazenamento de tokens
 * - Renovação automática de tokens
 * - Logout e limpeza de tokens
 * - Sincronização entre componentes
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { authService } from '../lib/auth-service';
import { useAuth } from '../hooks/useAuth';

// Mock do fetch global
global.fetch = jest.fn();

// Mock do localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock do window.location
Object.defineProperty(window, 'location', {
  value: { href: '' },
  writable: true,
});

describe('🔐 AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  describe('🔑 Login', () => {
    test('should login successfully and store tokens', async () => {
      const mockTokenPair = {
        access_token: 'mock_access_token',
        refresh_token: 'mock_refresh_token',
        token_type: 'bearer',
        expires_in: 900,
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockTokenPair),
      });

      const result = await authService.login({
        username: 'test_user',
        password: 'test_password',
      });

      expect(result).toEqual(mockTokenPair);
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'mock_access_token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('refresh_token', 'mock_refresh_token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('token_expires_at', expect.any(String));
    });

    test('should throw error on failed login', async () => {
      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid credentials' }),
      });

      await expect(authService.login({
        username: 'wrong_user',
        password: 'wrong_password',
      })).rejects.toThrow('Invalid credentials');
    });
  });

  describe('🔄 Token Refresh', () => {
    test('should refresh token successfully', async () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'refresh_token') return 'mock_refresh_token';
        return null;
      });

      const mockRefreshResponse = {
        access_token: 'new_access_token',
        token_type: 'bearer',
        expires_in: 900,
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockRefreshResponse),
      });

      const result = await authService.refreshToken();

      expect(result).toBe('new_access_token');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('access_token', 'new_access_token');
    });

    test('should logout on failed refresh', async () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'refresh_token') return 'expired_refresh_token';
        return null;
      });

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Refresh token expired' }),
      });

      const logoutSpy = jest.spyOn(authService, 'logout').mockImplementation(async () => {});

      await expect(authService.refreshToken()).rejects.toThrow();
      expect(logoutSpy).toHaveBeenCalled();
    });

    test('should deduplicate concurrent refresh calls', async () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'refresh_token') return 'mock_refresh_token';
        return null;
      });

      const mockRefreshResponse = {
        access_token: 'new_access_token',
        token_type: 'bearer',
        expires_in: 900,
      };

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockRefreshResponse),
      });

      // Fazer múltiplas chamadas simultaneas
      const promise1 = authService.refreshToken();
      const promise2 = authService.refreshToken();
      const promise3 = authService.refreshToken();

      const results = await Promise.all([promise1, promise2, promise3]);

      // Todas devem retornar o mesmo token
      expect(results).toEqual(['new_access_token', 'new_access_token', 'new_access_token']);
      
      // Fetch deve ter sido chamado apenas uma vez
      expect(fetch).toHaveBeenCalledTimes(1);
    });
  });

  describe('🚪 Logout', () => {
    test('should logout and clear tokens', async () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'access_token') return 'mock_access_token';
        return null;
      });

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      await authService.logout();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('token_expires_at');
      expect(window.location.href).toBe('/login');
    });

    test('should clear tokens even if server request fails', async () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'access_token') return 'mock_access_token';
        return null;
      });

      (fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await authService.logout();

      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refresh_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('token_expires_at');
    });
  });

  describe('🪙 Token Validation', () => {
    test('should return valid token if not expired', () => {
      const futureTime = Date.now() + 600000; // 10 minutos no futuro
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'access_token') return 'valid_token';
        if (key === 'token_expires_at') return futureTime.toString();
        return null;
      });

      const token = authService.getAccessToken();
      expect(token).toBe('valid_token');
    });

    test('should return null if token expired', () => {
      const pastTime = Date.now() - 600000; // 10 minutos no passado
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'access_token') return 'expired_token';
        if (key === 'token_expires_at') return pastTime.toString();
        return null;
      });

      const token = authService.getAccessToken();
      expect(token).toBe(null);
    });

    test('should return valid token after refresh', async () => {
      // Mock token expirado
      const pastTime = Date.now() - 600000;
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'access_token') return 'expired_token';
        if (key === 'refresh_token') return 'valid_refresh_token';
        if (key === 'token_expires_at') return pastTime.toString();
        return null;
      });

      (fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          access_token: 'new_token',
          token_type: 'bearer',
          expires_in: 900,
        }),
      });

      const token = await authService.getValidToken();
      expect(token).toBe('new_token');
    });
  });
});

describe('🪝 useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should initialize with loading state', () => {
    const { result } = renderHook(() => useAuth());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
  });

  test('should login successfully and update state', async () => {
    const mockTokenPair = {
      access_token: 'mock_access_token',
      refresh_token: 'mock_refresh_token',
      token_type: 'bearer',
      expires_in: 900,
    };

    const mockUser = {
      id: 1,
      username: 'test_user',
      email: 'test@example.com',
      is_active: true,
    };

    // Mock do authService
    jest.spyOn(authService, 'login').mockResolvedValueOnce(mockTokenPair);
    jest.spyOn(authService, 'isAuthenticated').mockReturnValue(true);
    jest.spyOn(authService, 'getCurrentUser').mockResolvedValueOnce(mockUser);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.login({
        username: 'test_user',
        password: 'test_password',
      });
    });

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isLoading).toBe(false);
    });
  });

  test('should logout successfully and clear state', async () => {
    jest.spyOn(authService, 'logout').mockResolvedValueOnce(undefined);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    expect(result.current.isLoading).toBe(false);
  });

  test('should handle login error', async () => {
    jest.spyOn(authService, 'login').mockRejectedValueOnce(new Error('Login failed'));

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      try {
        await result.current.login({
          username: 'wrong_user',
          password: 'wrong_password',
        });
      } catch (error) {
        // Expected error
      }
    });

    expect(result.current.error).toBe('Login failed');
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(false);
  });

  test('should clear error when clearError is called', async () => {
    jest.spyOn(authService, 'login').mockRejectedValueOnce(new Error('Login failed'));

    const { result } = renderHook(() => useAuth());

    // Cause error
    await act(async () => {
      try {
        await result.current.login({
          username: 'wrong_user',
          password: 'wrong_password',
        });
      } catch (error) {
        // Expected error
      }
    });

    expect(result.current.error).toBe('Login failed');

    // Clear error
    act(() => {
      result.current.clearError();
    });

    expect(result.current.error).toBe(null);
  });
});

describe('🔄 Multi-tab Synchronization', () => {
  test('should sync auth state when localStorage changes', async () => {
    const { result } = renderHook(() => useAuth());

    // Simular mudança no localStorage (outra aba fez logout)
    act(() => {
      const storageEvent = new StorageEvent('storage', {
        key: 'access_token',
        newValue: null,
        oldValue: 'some_token',
      });
      
      window.dispatchEvent(storageEvent);
    });

    // Estado deve ser atualizado
    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(false);
    });
  });
});
