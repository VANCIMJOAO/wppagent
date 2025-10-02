'use client'

import { useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Calendar, 
  User, 
  Bell, 
  CheckCircle, 
  AlertCircle, 
  XCircle, 
  Info,
  Zap
} from 'lucide-react'

export default function ToastTestPage() {
  const [toastCount, setToastCount] = useState(0)

  const testAppointmentCreated = () => {
    toast.success('📅 Novo agendamento criado!', {
      description: 'Para: João Silva - Consulta Médica'
    })
    setToastCount(prev => prev + 1)
  }

  const testAppointmentUpdated = () => {
    toast.info('✏️ Agendamento atualizado!', {
      description: 'João Silva - Status: confirmado'
    })
    setToastCount(prev => prev + 1)
  }

  const testAppointmentCancelled = () => {
    toast.error('❌ Agendamento cancelado', {
      description: 'Cliente: Maria Santos'
    })
    setToastCount(prev => prev + 1)
  }

  const testSystemNotification = () => {
    toast.info('🔔 Notificação', {
      description: 'Nova notificação do sistema'
    })
    setToastCount(prev => prev + 1)
  }

  const testConnectionToast = () => {
    toast.success('🔌 Conectado em tempo real', {
      description: 'Notificações ativas'
    })
    setToastCount(prev => prev + 1)
  }

  const testMultipleToasts = () => {
    const toasts = [
      () => toast.success('📅 Agendamento 1 criado!'),
      () => toast.info('📅 Agendamento 2 atualizado!'),
      () => toast.error('❌ Agendamento 3 cancelado'),
      () => toast.info('🔔 Notificação do sistema'),
      () => toast.success('✅ Todos os testes concluídos!')
    ]

    toasts.forEach((showToast, index) => {
      setTimeout(() => {
        showToast()
        setToastCount(prev => prev + 1)
      }, index * 1000)
    })
  }

  const testCustomToast = () => {
    toast.custom((t) => (
      <div className="bg-blue-500 text-white p-4 rounded-lg shadow-lg">
        <div className="flex items-center space-x-2">
          <Zap className="w-5 h-5" />
          <div>
            <p className="font-bold">Toast Personalizado!</p>
            <p className="text-sm opacity-90">Este é um toast customizado para teste</p>
          </div>
        </div>
      </div>
    ))
    setToastCount(prev => prev + 1)
  }

  const clearAllToasts = () => {
    toast.dismiss()
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">🧪 Teste de Toasts</h1>
          <p className="text-gray-600 mt-1">Teste manual dos toasts do sistema</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="text-sm">
            Toasts enviados: {toastCount}
          </Badge>
          <Button onClick={clearAllToasts} variant="outline" size="sm">
            Limpar Todos
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Toasts de Agendamento */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="w-5 h-5 text-blue-500" />
              <span>Agendamentos</span>
            </CardTitle>
            <CardDescription>
              Teste toasts relacionados a agendamentos
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              onClick={testAppointmentCreated} 
              className="w-full bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Agendamento Criado
            </Button>
            
            <Button 
              onClick={testAppointmentUpdated} 
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              <AlertCircle className="w-4 h-4 mr-2" />
              Agendamento Atualizado
            </Button>
            
            <Button 
              onClick={testAppointmentCancelled} 
              className="w-full bg-red-600 hover:bg-red-700"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Agendamento Cancelado
            </Button>
          </CardContent>
        </Card>

        {/* Toasts do Sistema */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Bell className="w-5 h-5 text-purple-500" />
              <span>Sistema</span>
            </CardTitle>
            <CardDescription>
              Teste notificações do sistema
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              onClick={testSystemNotification} 
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              <Info className="w-4 h-4 mr-2" />
              Notificação do Sistema
            </Button>
            
            <Button 
              onClick={testConnectionToast} 
              className="w-full bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Conexão WebSocket
            </Button>
            
            <Button 
              onClick={testCustomToast} 
              className="w-full bg-indigo-600 hover:bg-indigo-700"
            >
              <Zap className="w-4 h-4 mr-2" />
              Toast Personalizado
            </Button>
          </CardContent>
        </Card>

        {/* Testes em Lote */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-orange-500" />
              <span>Testes em Lote</span>
            </CardTitle>
            <CardDescription>
              Teste múltiplos toasts sequenciais
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button 
              onClick={testMultipleToasts} 
              className="w-full bg-orange-600 hover:bg-orange-700"
            >
              <Zap className="w-4 h-4 mr-2" />
              Múltiplos Toasts
            </Button>
            
            <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
              <p><strong>Dica:</strong> Os toasts aparecerão um por segundo para simular notificações reais.</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Instruções */}
      <Card>
        <CardHeader>
          <CardTitle>📋 Instruções</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p><strong>1.</strong> Clique nos botões acima para testar diferentes tipos de toast</p>
            <p><strong>2.</strong> Observe os toasts aparecendo no canto da tela</p>
            <p><strong>3.</strong> Use "Limpar Todos" para fechar todos os toasts</p>
            <p><strong>4.</strong> Os toasts são os mesmos que apareceriam com notificações reais</p>
            <p><strong>5.</strong> Para testar notificações reais, use o script Python de notificações</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

