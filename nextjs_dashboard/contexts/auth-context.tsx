"use client";

import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { debugLog } from '@/lib/debug';

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
  const router = useRouter();

  // Verificar autenticação ao carregar - APENAS via cookies seguros
  useEffect(() => {
    const checkAuth = async () => {
      debugLog.auth('Verificando autenticação via cookies seguros...')

      try {
        // Tentar acessar endpoint protegido para verificar autenticação
        const response = await fetch('/api/proxy/auth/status', {
          method: 'GET',
          credentials: 'include', // Inclui cookies HttpOnly
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const userData = await response.json();
          debugLog.success('Usuário autenticado via cookies seguros!');
          setIsAuthenticated(true);
        } else {
          debugLog.info('Usuário não autenticado');
          setIsAuthenticated(false);
        }
      } catch (error) {
        debugLog.error('Erro ao verificar autenticação:', error);
        setIsAuthenticated(false);
      }

      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      debugLog.auth(`Tentando fazer login com: ${email}`);

      // Fazer login real com o backend usando cookies seguros
      const response = await fetch('/api/proxy/auth/login', {
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

      // ✅ SEGURO: Tokens agora estão em cookies HttpOnly
      // Não precisamos mais gerenciar tokens no frontend

      setIsAuthenticated(true);
      router.push('/dashboard');
    } catch (error) {
      debugLog.error('Erro no login', error);
      throw error;
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      debugLog.auth('Renovando token via cookies seguros...');

      const response = await fetch('/api/proxy/auth/refresh', {
        method: 'POST',
        credentials: 'include', // Inclui cookies HttpOnly
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        debugLog.error('Falha ao renovar token');
        return false;
      }

      const data = await response.json();
      debugLog.success('Token renovado com sucesso!');
      return true;
    } catch (error) {
      debugLog.error('Erro ao renovar token', error);
      return false;
    }
  };

  const logout = async () => {
    try {
      // Fazer logout seguro no backend
      await fetch('/api/proxy/auth/logout', {
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
    <AuthContext.Provider value={{ isAuthenticated, login, logout, loading, refreshToken }}>
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
