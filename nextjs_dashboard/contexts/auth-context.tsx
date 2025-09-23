"use client";

import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { debugLog } from '@/lib/debug';
import { useTokenRefresh } from '@/hooks/use-token-refresh';

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
  
  // ✅ Hook para renovação automática de token
  const { refreshToken, checkTokenValidity } = useTokenRefresh();

  // Handle client-side mounting
  useEffect(() => {
    setMounted(true);
  }, []);

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
          
          // ✅ Redirecionar para login se não autenticado e não estiver na página de login
          if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
            debugLog.info('🔄 Redirecionando para login - usuário não autenticado');
            debugLog.info('🔄 Caminho atual:', window.location.pathname);
            debugLog.info('🔄 Tentando router.push para /login...');
            // ✅ CORREÇÃO: Usar router do Next.js ao invés de window.location para evitar loop
            router.push('/login');
            debugLog.info('🔄 router.push executado');
          }
        }
      } catch (error) {
        debugLog.error('Erro ao verificar autenticação:', error);
        setIsAuthenticated(false);
      }

      setLoading(false);
    };

    checkAuth();
  }, [mounted]); // Removido checkTokenValidity da dependência

  const login = async (email: string, password: string) => {
    try {
      debugLog.auth(`Tentando fazer login com: ${email}`);

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
      debugLog.info('Dados do login:', data);

      // ✅ SEGURO: Tokens agora estão em cookies HttpOnly
      // Não precisamos mais gerenciar tokens no frontend

      debugLog.info('Definindo isAuthenticated como true...');
      setIsAuthenticated(true);
      
      debugLog.info('Redirecionando para /dashboard...');
      debugLog.info('Router disponível:', !!router);
      
      // ✅ CORREÇÃO: Redirecionamento simples e direto
      debugLog.info('🔄 Executando redirecionamento...');
      
      // Usar window.location.href para navegação mais robusta em desenvolvimento
      if (typeof window !== 'undefined') {
        debugLog.info('🔄 Usando window.location.href para redirecionamento robusto');
        window.location.href = '/dashboard';
      } else {
        // Fallback para router.push se window não disponível
        router.push('/dashboard');
        debugLog.info('✅ router.push executado como fallback');
      }
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
    // Apenas limpar estado local
    setIsAuthenticated(false);
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
