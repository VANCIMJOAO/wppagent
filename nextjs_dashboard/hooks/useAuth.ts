/**
 * Hook de autenticação real com backend
 */

import { useState, useEffect, useCallback } from 'react'

export interface User {
  username: string
  role: string
  permissions: string[]
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

export function useAuth() {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Verificar token armazenado
    const storedToken = localStorage.getItem('auth-token')
    if (storedToken) {
      setToken(storedToken)
      // Decodificar JWT para obter user info
      try {
        const payload = JSON.parse(atob(storedToken.split('.')[1]))
        setUser({
          username: payload.sub,
          role: payload.role,
          permissions: payload.permissions || []
        })
      } catch (error) {
        console.error('Erro ao decodificar token:', error)
        localStorage.removeItem('auth-token')
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    try {
      const response = await fetch('/api/proxy/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })

      if (!response.ok) {
        throw new Error('Credenciais inválidas')
      }

      const data: AuthResponse = await response.json()
      
      setToken(data.access_token)
      localStorage.setItem('auth-token', data.access_token)
      
      // Decodificar JWT para obter user info
      const payload = JSON.parse(atob(data.access_token.split('.')[1]))
      setUser({
        username: payload.sub,
        role: payload.role,
        permissions: payload.permissions || []
      })

      return true
    } catch (error) {
      console.error('Erro no login:', error)
      throw error
    }
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('auth-token')
  }, [])

  const authenticatedFetch = useCallback(async (url: string, options: RequestInit = {}) => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {})
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    return fetch(url, {
      ...options,
      headers
    })
  }, [token])

  return {
    token,
    user,
    loading,
    isAuthenticated: !!token,
    login,
    logout,
    authenticatedFetch
  }
}

export function useAuthenticatedFetch() {
  const { authenticatedFetch, isAuthenticated } = useAuth()
  return { authenticatedFetch, isAuthenticated }
}
