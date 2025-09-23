'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated, loading } = useAuth()

  useEffect(() => {
    // Aguardar o auth-context determinar o estado de autenticação
    if (!loading) {
      if (isAuthenticated) {
        // Usuário autenticado, ir para dashboard
        router.push('/dashboard')
      } else {
        // Usuário não autenticado, ir para login
        router.push('/login')
      }
    }
  }, [isAuthenticated, loading, router])

  // Mostrar loading enquanto verifica autenticação
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">
          {loading ? 'Verificando autenticação...' : 'Redirecionando...'}
        </p>
      </div>
    </div>
  )
}
