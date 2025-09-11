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

  // Verificar autenticação ao carregar
  useEffect(() => {
    const checkAuth = () => {
      debugLog.auth('Verificando autenticação...')
      
      // Verificar tanto cookies quanto localStorage
      const authToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('auth-token='));
      
      const userStorage = localStorage.getItem('user');
      
      debugLog.auth('Status de autenticação', !!authToken)
      debugLog.info('User storage exists', !!userStorage)
      
      if (authToken || userStorage) {
        debugLog.success('Usuário autenticado!')
        setIsAuthenticated(true);
      } else {
        debugLog.info('Usuário não autenticado')
        setIsAuthenticated(false);
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      debugLog.auth(`Tentando fazer login com: ${email}`);
      
      // Fazer login real com o backend
      const response = await fetch('/api/proxy/admin/login', {
        method: 'POST',
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
      
      // Salvar token real do backend
      const token = data.access_token;
      document.cookie = `auth-token=${token}; path=/; max-age=86400`;
      
      // Salvar também no localStorage
      localStorage.setItem('user', JSON.stringify({
        id: 1,
        email: email,
        name: 'Administrador',
        role: 'admin',
        avatar_url: null
      }));
      localStorage.setItem('auth-token', token);
      
      setIsAuthenticated(true);
      router.push('/dashboard');
    } catch (error) {
      debugLog.error('Erro no login', error);
      throw error;
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      debugLog.auth('Renovando token...');
      
      // ✅ SEGURO: Usar API route segura sem credenciais hardcoded
      const response = await fetch('/api/auth/admin-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
        // ✅ Sem credenciais - API route gerencia internamente
      });

      if (!response.ok) {
        debugLog.error('Falha ao renovar token');
        return false;
      }

      const data = await response.json();
      const token = data.token; // ✅ Campo correto da nova API route
      
      // Atualizar token nos cookies e localStorage
      document.cookie = `auth-token=${token}; path=/; max-age=86400`;
      localStorage.setItem('auth-token', token);
      
      debugLog.success('Token renovado com sucesso!');
      return true;
    } catch (error) {
      debugLog.error('Erro ao renovar token', error);
      return false;
    }
  };

  const logout = () => {
    document.cookie = 'auth-token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    localStorage.removeItem('user');
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