"use client";

import { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Verificar autenticação ao carregar
  useEffect(() => {
    const checkAuth = () => {
      console.log('AuthContext: Verificando autenticação...')
      
      // Verificar tanto cookies quanto localStorage
      const authToken = document.cookie
        .split('; ')
        .find(row => row.startsWith('auth-token='));
      
      const userStorage = localStorage.getItem('user');
      
      console.log('AuthContext: Auth token:', authToken)
      console.log('AuthContext: User storage:', userStorage)
      
      if (authToken || userStorage) {
        console.log('AuthContext: Usuário autenticado!')
        setIsAuthenticated(true);
      } else {
        console.log('AuthContext: Usuário não autenticado')
        setIsAuthenticated(false);
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      // Simular autenticação
      if (email && password) {
        document.cookie = 'auth-token=authenticated; path=/; max-age=86400';
        // Salvar também no localStorage
        localStorage.setItem('user', JSON.stringify({
          id: 1,
          email: email,
          name: 'Administrador',
          role: 'admin',
          avatar_url: null
        }));
        setIsAuthenticated(true);
        router.push('/dashboard');
      } else {
        throw new Error('Credenciais inválidas');
      }
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    document.cookie = 'auth-token=; path=/; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, loading }}>
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