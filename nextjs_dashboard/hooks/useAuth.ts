/**
 * 🪝 Hook de Autenticação com Refresh Tokens
 * ==========================================
 * 
 * Hook customizado que integra AuthService com React:
 * - Estado de autenticação reativo
 * - Métodos para login/logout
 * - Sincronização entre componentes
 * - Loading states para UX
 */

import { useState, useEffect, useCallback } from 'react';
import { authService, LoginCredentials, User, TokenPair } from '../lib/auth-service';

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<TokenPair>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

export type UseAuthReturn = AuthState & AuthActions;

/**
 * 🪝 Hook principal de autenticação
 */
export function useAuth(): UseAuthReturn {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    isLoading: true,
    error: null,
  });
  
  /**
   * 🔄 Atualizar estado de autenticação
   */
  const updateAuthState = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const isAuthenticated = authService.isAuthenticated();
      
      if (isAuthenticated) {
        const user = await authService.getCurrentUser();
        setState({
          isAuthenticated: true,
          user,
          isLoading: false,
          error: null,
        });
      } else {
        setState({
          isAuthenticated: false,
          user: null,
          isLoading: false,
          error: null,
        });
      }
    } catch (error) {
      console.error('❌ Erro ao verificar autenticação:', error);
      setState({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Erro desconhecido',
      });
    }
  }, []);
  
  /**
   * 🔑 Função de login
   */
  const login = useCallback(async (credentials: LoginCredentials): Promise<TokenPair> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const tokenPair = await authService.login(credentials);
      
      // Atualizar estado após login bem-sucedido
      await updateAuthState();
      
      return tokenPair;
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erro no login';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, [updateAuthState]);
  
  /**
   * 🚪 Função de logout
   */
  const logout = useCallback(async (): Promise<void> => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      
      await authService.logout();
      
      setState({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        error: null,
      });
      
    } catch (error) {
      console.error('❌ Erro no logout:', error);
      // Mesmo com erro, limpar estado local
      setState({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        error: null,
      });
    }
  }, []);
  
  /**
   * 🔄 Atualizar informações do usuário
   */
  const refreshUser = useCallback(async (): Promise<void> => {
    await updateAuthState();
  }, [updateAuthState]);
  
  /**
   * 🧹 Limpar erro
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);
  
  /**
   * 🎬 Effect para verificar autenticação inicial
   */
  useEffect(() => {
    updateAuthState();
  }, [updateAuthState]);
  
  /**
   * 🎧 Effect para escutar eventos de storage (sincronização entre abas)
   */
  useEffect(() => {
    const handleStorageChange = (event: StorageEvent) => {
      // Se tokens foram removidos/alterados em outra aba, atualizar estado
      if (event.key?.includes('token')) {
        updateAuthState();
      }
    };
    
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', handleStorageChange);
      
      return () => {
        window.removeEventListener('storage', handleStorageChange);
      };
    }
  }, [updateAuthState]);
  
  return {
    // Estado
    isAuthenticated: state.isAuthenticated,
    user: state.user,
    isLoading: state.isLoading,
    error: state.error,
    
    // Ações
    login,
    logout,
    refreshUser,
    clearError,
  };
}

/**
 * 🛡️ Hook para verificar se usuário tem permissão específica
 */
export function usePermission(permission: string): boolean {
  const { user } = useAuth();
  
  // Por enquanto, usuários admin têm todas as permissões
  // Pode ser expandido futuramente com sistema de roles
  return user?.is_active === true;
}

/**
 * 🔐 Hook para verificar se usuário é super admin
 */
export function useSuperAdmin(): boolean {
  const { user } = useAuth();
  
  // Assumindo que existe campo is_super_admin no modelo User
  return (user as any)?.is_super_admin === true;
}
