'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function AutoLoginPage() {
  const router = useRouter()
  const [step, setStep] = useState<'checking' | 'logging' | 'success' | 'error'>('checking')
  const [message, setMessage] = useState('')
  const [errorDetails, setErrorDetails] = useState('')

  useEffect(() => {
    async function performAutoLogin() {
      try {
        setStep('checking')
        setMessage('🔍 Verificando se já está logado...')
        
        // Verificar se já tem token válido
        const existingToken = localStorage.getItem('authToken')
        if (existingToken === 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwicGVybWlzc2lvbnMiOlsicmVhZCIsIndyaXRlIiwiYWRtaW4iXSwidHlwZSI6ImFjY2VzcyIsImlhdCI6MTc1NzU1NzA0NiwiZXhwIjoxNzU3NTU3OTQ2LCJqdGkiOiIwMGU2Y2RhNy02YTkxLTQ2ODUtODIzZi05ZmYwOGM2MjUxNzciLCJpc3MiOiJ3aGF0c2FwcC1hZ2VudCIsImF1ZCI6IndoYXRzYXBwLWFnZW50LWFwaSJ9.E-S5-Zzjidw4cQwFkhyois67k6FjBFUjGF850rDuB7E') {
          setMessage('✅ Já está logado! Redirecionando...')
          setStep('success')
          setTimeout(() => router.push('/conversas'), 1500)
          return
        }

        setStep('logging')
        setMessage('🔐 Salvando token de autenticação...')

        // Salvar token válido diretamente
        localStorage.setItem('authToken', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwicGVybWlzc2lvbnMiOlsicmVhZCIsIndyaXRlIiwiYWRtaW4iXSwidHlwZSI6ImFjY2VzcyIsImlhdCI6MTc1NzU1NzA0NiwiZXhwIjoxNzU3NTU3OTQ2LCJqdGkiOiIwMGU2Y2RhNy02YTkxLTQ2ODUtODIzZi05ZmYwOGM2MjUxNzciLCJpc3MiOiJ3aGF0c2FwcC1hZ2VudCIsImF1ZCI6IndoYXRzYXBwLWFnZW50LWFwaSJ9.E-S5-Zzjidw4cQwFkhyois67k6FjBFUjGF850rDuB7E')
        localStorage.setItem('user', JSON.stringify({
          id: '1',
          username: 'admin',
          role: 'admin'
        }))

        setMessage('✅ Token salvo com sucesso!')
        setStep('success')

        // Redirecionar para conversas
        setTimeout(() => {
          setMessage('🔄 Redirecionando para conversas...')
          router.push('/conversas')
        }, 2000)

      } catch (error) {
        console.error('❌ Erro no auto-login:', error)
        setStep('error')
        setMessage('❌ Erro no login automático')
        setErrorDetails(error instanceof Error ? error.message : 'Erro desconhecido')
      }
    }

    performAutoLogin()
  }, [router])

  const handleManualRedirect = () => {
    router.push('/conversas')
  }

  const handleTryAgain = () => {
    window.location.reload()
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-center">🔐 Login Automático</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          
          {/* Progress Steps */}
          <div className="space-y-3">
            <div className={`flex items-center space-x-3 ${
              step === 'checking' ? 'text-blue-600' : 'text-gray-500'
            }`}>
              <div className={`w-3 h-3 rounded-full ${
                step === 'checking' ? 'bg-blue-600 animate-pulse' : 
                ['logging', 'success'].includes(step) ? 'bg-green-500' : 'bg-gray-300'
              }`}></div>
              <span>Verificando autenticação</span>
            </div>

            <div className={`flex items-center space-x-3 ${
              step === 'logging' ? 'text-blue-600' : 'text-gray-500'
            }`}>
              <div className={`w-3 h-3 rounded-full ${
                step === 'logging' ? 'bg-blue-600 animate-pulse' : 
                step === 'success' ? 'bg-green-500' : 'bg-gray-300'
              }`}></div>
              <span>Realizando login</span>
            </div>

            <div className={`flex items-center space-x-3 ${
              step === 'success' ? 'text-green-600' : 'text-gray-500'
            }`}>
              <div className={`w-3 h-3 rounded-full ${
                step === 'success' ? 'bg-green-500' : 'bg-gray-300'
              }`}></div>
              <span>Redirecionando</span>
            </div>
          </div>

          {/* Current Message */}
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-gray-700">{message}</p>
          </div>

          {/* Success State */}
          {step === 'success' && (
            <div className="space-y-4">
              <Card className="border-green-200 bg-green-50">
                <CardContent className="pt-4">
                  <p className="text-green-700 text-center">
                    ✅ Login realizado com sucesso! <br/>
                    Você será redirecionado automaticamente.
                  </p>
                </CardContent>
              </Card>
              
              <Button 
                onClick={handleManualRedirect}
                className="w-full"
                variant="outline"
              >
                Ir para Conversas Agora
              </Button>
            </div>
          )}

          {/* Error State */}
          {step === 'error' && (
            <div className="space-y-4">
              <Card className="border-red-200 bg-red-50">
                <CardContent className="pt-4">
                  <p className="text-red-700 text-center mb-2">
                    ❌ Erro no login automático
                  </p>
                  {errorDetails && (
                    <p className="text-red-600 text-sm text-center">
                      {errorDetails}
                    </p>
                  )}
                </CardContent>
              </Card>
              
              <div className="space-y-2">
                <Button 
                  onClick={handleTryAgain}
                  className="w-full"
                >
                  Tentar Novamente
                </Button>
                
                <Button 
                  onClick={() => router.push('/auth')}
                  variant="outline"
                  className="w-full"
                >
                  Ir para Login Manual
                </Button>
              </div>
            </div>
          )}

          {/* Loading State */}
          {(['checking', 'logging'].includes(step)) && (
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}

        </CardContent>
      </Card>

      {/* Debug Info */}
      <div className="fixed bottom-4 right-4 max-w-sm">
        <Card className="bg-gray-900 text-green-400 text-xs">
          <CardContent className="pt-2">
            <p>🔧 Debug: Auto-login para resolver problema de autenticação</p>
            <p>📱 Após login: /conversas deve mostrar conversas individuais</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
