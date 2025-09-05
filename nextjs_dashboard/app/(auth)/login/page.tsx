'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { MessageCircle, Lock, Mail, Eye, EyeOff } from "lucide-react"
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    console.log('Tentando login com:', { email, password })

    try {
      // Para agora, usar autenticação local simples
      // TODO: Implementar autenticação real com backend
      
      if (email === 'admin' && password === 'senha_admin_segura') {
        console.log('Login bem-sucedido!')
        
        // Salvar token e dados do usuário
        const userData = {
          id: '1',
          email: email,
          name: 'Administrador',
          role: 'admin',
          avatar_url: null,
          access_token: 'authenticated',
          token_type: 'Bearer',
          expires_in: 3600
        }
        
        localStorage.setItem('user', JSON.stringify(userData))
        console.log('Dados salvos no localStorage:', userData)
        
        // Salvar também no cookie para o middleware
        document.cookie = `auth-token=authenticated; path=/; max-age=3600`;
        console.log('Cookie JWT definido. Redirecionando...')
        
        // Redirecionar para dashboard
        router.push('/dashboard')
      } else {
        setError('Credenciais incorretas. Use: admin / senha_admin_segura')
      }
    } catch (err) {
      console.error('Erro durante login:', err)
      
      // Fallback para demonstração se API não estiver disponível
      if (email === 'admin' && password === 'senha_admin_segura') {
        console.log('API indisponível, usando fallback demo...')
        
        const userData = {
          id: 1,
          email: email,
          name: 'Administrador',
          role: 'admin',
          avatar_url: null,
          access_token: 'demo-token',
          token_type: 'bearer'
        }
        
        localStorage.setItem('user', JSON.stringify(userData))
        document.cookie = 'auth-token=demo-token; path=/; max-age=86400';
        
        router.push('/dashboard')
      } else {
        setError('Credenciais incorretas. Use: admin / senha_admin_segura')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 via-purple-600 to-indigo-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo e Header */}
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center mb-4">
            <MessageCircle className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">WppAgent</h1>
          <p className="text-blue-100">Dashboard de Atendimento</p>
        </div>

        {/* Card de Login */}
        <Card className="backdrop-blur-sm bg-white/10 border-white/20 text-white">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl text-white">Entrar</CardTitle>
            <CardDescription className="text-blue-100">
              Acesse sua conta para continuar
            </CardDescription>
          </CardHeader>
          
          <form onSubmit={handleLogin}>
            <CardContent className="space-y-4">
              {error && (
                <Alert className="bg-red-500/20 border-red-400/50 text-white">
                  <Lock className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Campo Username */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-white">Username</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-300" />
                  <Input
                    id="email"
                    type="text"
                    placeholder="admin"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-gray-300 focus:border-white/40"
                    required
                  />
                </div>
              </div>

              {/* Campo Senha */}
              <div className="space-y-2">
                <Label htmlFor="password" className="text-white">Senha</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-300" />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="senha_admin_segura"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 pr-10 bg-white/10 border-white/20 text-white placeholder:text-gray-300 focus:border-white/40"
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 text-gray-300 hover:text-white"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              {/* Credenciais de Demonstração */}
              <div className="bg-white/5 rounded-lg p-3 text-sm">
                <p className="text-blue-100 font-medium mb-1">Credenciais de demonstração:</p>
                <p className="text-blue-200">Email: admin@exemplo.com</p>
                <p className="text-blue-200">Senha: admin123</p>
              </div>
            </CardContent>

            <CardFooter>
              <Button 
                type="submit" 
                className="w-full bg-white text-blue-600 hover:bg-white/90"
                disabled={isLoading}
              >
                {isLoading ? 'Entrando...' : 'Entrar'}
              </Button>
            </CardFooter>
          </form>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8 text-blue-100 text-sm">
          <p>&copy; 2024 WppAgent Dashboard</p>
        </div>
      </div>
    </div>
  )
}