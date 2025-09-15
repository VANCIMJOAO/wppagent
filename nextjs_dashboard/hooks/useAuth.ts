/**
 * 🪝 Hook de Autenticação com Cookies Seguros
 * ==========================================
 *
 * Hook customizado que integra SecureAuthManager com React:
 * - Estado de autenticação reativo
 * - Métodos para login/logout seguros
 * - Sincronização entre componentes
 * - Loading states para UX
 * - HttpOnly cookies para segurança
 */

import { secureAuth, SecureAuthState, AuthResponse, User } from '../lib/secure-auth-manager';
import { useState, useEffect, useCallback, useContext, createContext, ReactNode } from 'react';

// Tipos para o hook
interface LoginCredentials {
  username: string;
  password: string;
  totp?: string; // Código 2FA opcional
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

export type UseAuthReturn = AuthState & AuthActions;

/**
 * Context para compartilhar estado de auth entre componentes
 */
const AuthContext = createContext<UseAuthReturn | null>(null);

/**
 * 🪝 Hook de Autenticação Segura
 * =============================
 *
 * Fornece estado e métodos de autenticação usando cookies HttpOnly
 *
 * @returns {UseAuthReturn} Estado e ações de autenticação
 *
 * @example
 * ```typescript
 * const { login, logout, isAuthenticated, user, isLoading } = useAuth();
 *
 * // Fazer login
 * const handleLogin = async (credentials) => {
 *   const result = await login(credentials);
 *   if (result.success) {
 *     console.log('Login realizado!');
 *   }
 * };
 * ```
 */
export function useAuth(): UseAuthReturn {
  // Estado local do hook
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    isLoading: true, // Começar como loading para verificar auth inicial
    error: null,
  });

  // Sincronizar com SecureAuthManager no mount
  useEffect(() => {
    const checkInitialAuth = async () => {
      try {
        const isAuth = await secureAuth.isAuthenticated();
        const currentUser = isAuth ? await secureAuth.getCurrentUser() : null;

        setAuthState({
          isAuthenticated: isAuth,
          user: currentUser,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        console.error('🔴 Erro ao verificar auth inicial:', error);
        setAuthState(prev => ({
          ...prev,
          isAuthenticated: false,
          user: null,
          isLoading: false,
          error: 'Erro ao verificar autenticação',
        }));
      }
    };

    checkInitialAuth();
  }, []);

  /**
   * 🔐 Função de Login
   */
  const login = useCallback(async (credentials: LoginCredentials): Promise<AuthResponse> => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await secureAuth.login(credentials);

      if (response.success && response.user) {
        // Sucesso - atualizar estado
        setAuthState({
          isAuthenticated: true,
          user: response.user,
          isLoading: false,
          error: null,
        });
      } else {
        // Erro - manter deslogado
        setAuthState({
          isAuthenticated: false,
          user: null,
          isLoading: false,
          error: response.error || 'Credenciais inválidas',
        });
      }

      return response;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro no login';
      setAuthState({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        error: errorMessage,
      });

      return {
        success: false,
        error: errorMessage,
      };
    }
  }, []);

  /**
   * 🚪 Função de Logout
   */
  const logout = useCallback(async (): Promise<void> => {
    setAuthState(prev => ({ ...prev, isLoading: true }));

    try {
      await secureAuth.logout();

      // Sempre limpar estado após logout
      setAuthState({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        error: null,
      });

    } catch (error) {
      console.error('🔴 Erro no logout:', error);
      // Mesmo com erro, limpar estado local
      setAuthState({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        error: null,
      });
    }
  }, []);

  /**
   * 🔄 Atualizar dados do usuário
   */
  const refreshUser = useCallback(async (): Promise<void> => {
    try {
      const isAuth = await secureAuth.isAuthenticated();

      if (isAuth) {
        const currentUser = await secureAuth.getCurrentUser();
        setAuthState(prev => ({
          ...prev,
          isAuthenticated: true,
          user: currentUser,
          error: null,
        }));
      } else {
        setAuthState(prev => ({
          ...prev,
          isAuthenticated: false,
          user: null,
        }));
      }

    } catch (error) {
      console.error('🔴 Erro ao atualizar usuário:', error);
      setAuthState(prev => ({
        ...prev,
        error: 'Erro ao atualizar dados do usuário',
      }));
    }
  }, []);

  /**
   * 🧹 Limpar erro
   */
  const clearError = useCallback((): void => {
    setAuthState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...authState,
    login,
    logout,
    refreshUser,
    clearError,
  };
}

/**
 * 🪝 Hook para usar Auth Context
 * =============================
 *
 * Use este hook quando quiser compartilhar estado entre componentes.
 */
export function useAuthContext(): UseAuthReturn {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuthContext deve ser usado dentro de AuthProvider');
  }

  return context;
}

export default useAuth;
