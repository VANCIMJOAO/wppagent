"use client";

/**
 * 🔐 Auth Context Provider
 * ========================
 * 
 * ✅ CORREÇÃO #7: Todos os logs são condicionais via debugLog
 * - debugLog.* apenas executa em NODE_ENV=development
 * - Nenhum log é emitido em produção
 * - Informações sensíveis (email, tokens) não são logadas
 * - Erros críticos devem usar sistema de monitoring (Sentry, DataDog, etc)
 */

import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { debugLog } from '@/lib/debug';
import { useTokenRefresh } from '@/hooks/use-token-refresh';
import { onAuthEvent, AuthEventType } from '@/lib/auth-events';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);
  const router = useRouter();
  const pathname = usePathname(); // ✅ CORREÇÃO #8: Usar pathname do Next.js router
  
  // ✅ Hook para renovação automática de token
  const { refreshToken, checkTokenValidity } = useTokenRefresh();

  // Handle client-side mounting
  useEffect(() => {
    setMounted(true);
  }, []);

  // ✅ CORREÇÃO #12: Escutar eventos de autenticação para sincronizar estado
  useEffect(() => {
    if (!mounted) return;

    // Escutar evento de token expirado
    const unsubscribeTokenExpired = onAuthEvent(AuthEventType.TOKEN_EXPIRED, (data) => {
      debugLog.warn('🔔 Evento TOKEN_EXPIRED recebido:', data);
      
      // Atualizar estado imediatamente
      setIsAuthenticated(false);
      
      // ✅ CORREÇÃO #8: Usar pathname do Next.js router
      if (pathname !== '/login') {
        debugLog.info('🔄 Redirecionando para login após token expirado');
        router.push('/login');
      }
    });

    // Escutar evento de sessão expirada
    const unsubscribeSessionExpired = onAuthEvent(AuthEventType.SESSION_EXPIRED, (data) => {
      debugLog.warn('🔔 Evento SESSION_EXPIRED recebido:', data);
      
      // Atualizar estado imediatamente
      setIsAuthenticated(false);
      
      // ✅ CORREÇÃO #8: Usar pathname do Next.js router
      if (pathname !== '/login') {
        debugLog.info('🔄 Redirecionando para login após sessão expirada');
        router.push('/login');
      }
    });

    // Escutar evento de não autorizado (401)
    const unsubscribeUnauthorized = onAuthEvent(AuthEventType.UNAUTHORIZED, (data) => {
      debugLog.warn('🔔 Evento UNAUTHORIZED recebido:', data);
      
      // Atualizar estado imediatamente
      setIsAuthenticated(false);
      
      // ✅ CORREÇÃO #8: Usar pathname do Next.js router
      if (pathname !== '/login') {
        debugLog.info('🔄 Redirecionando para login após 401');
        router.push('/login');
      }
    });

    // Cleanup - remover listeners
    return () => {
      unsubscribeTokenExpired();
      unsubscribeSessionExpired();
      unsubscribeUnauthorized();
    };
  }, [mounted, router, pathname]); // ✅ CORREÇÃO #8: Adicionar pathname às dependências

  // Verificar autenticação ao carregar - APENAS via cookies seguros
  useEffect(() => {
    if (!mounted) return;

    const checkAuth = async () => {
      debugLog.auth('Verificando autenticação via cookies seguros...')

      try {
        // ✅ Usar o novo sistema de verificação de token
        const isValid = await checkTokenValidity();
        
        if (isValid) {
          debugLog.success('Usuário autenticado via cookies seguros!');
          setIsAuthenticated(true);
        } else {
          debugLog.info('Usuário não autenticado');
          setIsAuthenticated(false);
          
          // ✅ CORREÇÃO #8: Usar pathname do Next.js router
          if (pathname !== '/login') {
            debugLog.info('🔄 Redirecionando para login - usuário não autenticado');
            router.push('/login');
          }
        }
      } catch (error) {
        debugLog.error('Erro ao verificar autenticação:', error);
        setIsAuthenticated(false);
      }

      setLoading(false);
    };

    checkAuth();
  }, [mounted, checkTokenValidity, router, pathname]); // ✅ CORREÇÃO #8: Adicionar pathname às dependências

  const login = async (email: string, password: string) => {
    try {
      // ✅ CORREÇÃO #7: Não logar email do usuário (informação sensível)
      debugLog.auth('Tentando fazer login...');

      // Fazer login real com o backend usando cookies seguros
      const response = await fetch('/api/auth/admin-login', {
        method: 'POST',
        credentials: 'include', // Inclui cookies HttpOnly
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: email === 'admin@example.com' ? 'admin' : email,
          password
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        debugLog.error('Login falhou:', errorData);
        throw new Error('Credenciais inválidas');
      }

      const data = await response.json();
      debugLog.success('Login realizado com sucesso!');
      // ✅ CORREÇÃO #7: Não logar dados de resposta (podem conter informações sensíveis)

      // ✅ SEGURO: Tokens agora estão em cookies HttpOnly
      // ✅ SEGURO: NÃO salvar dados sensíveis (como role) em localStorage
      // Role será buscado do backend quando necessário via JWT

      setIsAuthenticated(true);
      router.push('/dashboard');
    } catch (error) {
      debugLog.error('Erro no login', error);
      throw error;
    }
  };

  const refreshTokenWrapper = async (): Promise<boolean> => {
    // ✅ Usar o hook de renovação de token
    return await refreshToken();
  };

  const logout = async () => {
    try {
      // Fazer logout seguro no backend
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include', // Inclui cookies HttpOnly
        headers: {
          'Content-Type': 'application/json'
        }
      });

      debugLog.success('Logout realizado com sucesso!');
    } catch (error) {
      debugLog.error('Erro no logout:', error);
    }

    // ✅ SEGURO: Cookies HttpOnly são removidos pelo backend
    // Limpar estado local e localStorage
    setIsAuthenticated(false);
    
    // Limpar localStorage se existir
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user');
    }
    
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, loading, refreshToken: refreshTokenWrapper }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
