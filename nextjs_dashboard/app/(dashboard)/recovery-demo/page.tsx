/**
 * Página de Demonstração do Error Recovery System
 * Combina dashboard robusto com simulador de cenários de erro
 */
import React from 'react'
import { Metadata } from 'next'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import DashboardWithRecovery from '@/components/dashboard/DashboardWithRecovery'
import ErrorRecoverySimulator from '@/components/dashboard/ErrorRecoverySimulator'
import {
  Shield,
  Activity,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Zap
} from 'lucide-react'

export const metadata: Metadata = {
  title: 'Error Recovery Demo - Sistema Robusto',
  description: 'Demonstração do sistema avançado de recuperação de erros com retry logic, cache fallback e modo degradado'
}

export default function ErrorRecoveryDemoPage() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-4 mb-8">
        <div className="flex items-center justify-center space-x-3">
          <Shield className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">
            Sistema de Error Recovery
          </h1>
          <Shield className="w-8 h-8 text-blue-600" />
        </div>

        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          Demonstração completa do sistema robusto de recuperação de erros, com retry automático,
          cache fallback, detecção de rede e modo degradado.
        </p>

        {/* Features Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
          <div className="flex flex-col items-center p-4 bg-blue-50 rounded-lg">
            <RefreshCw className="w-8 h-8 text-blue-600 mb-2" />
            <h3 className="font-semibold text-blue-900">Retry Logic</h3>
            <p className="text-sm text-blue-700 text-center">
              Exponential backoff automático
            </p>
          </div>

          <div className="flex flex-col items-center p-4 bg-green-50 rounded-lg">
            <CheckCircle className="w-8 h-8 text-green-600 mb-2" />
            <h3 className="font-semibold text-green-900">Cache Fallback</h3>
            <p className="text-sm text-green-700 text-center">
              Dados salvos localmente
            </p>
          </div>

          <div className="flex flex-col items-center p-4 bg-orange-50 rounded-lg">
            <AlertTriangle className="w-8 h-8 text-orange-600 mb-2" />
            <h3 className="font-semibold text-orange-900">Modo Degradado</h3>
            <p className="text-sm text-orange-700 text-center">
              Funcionalidade essencial mantida
            </p>
          </div>

          <div className="flex flex-col items-center p-4 bg-purple-50 rounded-lg">
            <Activity className="w-8 h-8 text-purple-600 mb-2" />
            <h3 className="font-semibold text-purple-900">Network Detection</h3>
            <p className="text-sm text-purple-700 text-center">
              Monitoramento em tempo real
            </p>
          </div>
        </div>
      </div>

      {/* Tabs com Dashboard e Simulador */}
      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="dashboard" className="flex items-center space-x-2">
            <Activity className="w-4 h-4" />
            <span>Dashboard Robusto</span>
          </TabsTrigger>
          <TabsTrigger value="simulator" className="flex items-center space-x-2">
            <Zap className="w-4 h-4" />
            <span>Simulador de Erros</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard" className="space-y-4">
          <div className="bg-white rounded-lg p-1">
            <DashboardWithRecovery />
          </div>
        </TabsContent>

        <TabsContent value="simulator" className="space-y-4">
          <div className="bg-white rounded-lg p-1">
            <ErrorRecoverySimulator />
          </div>
        </TabsContent>
      </Tabs>

      {/* Instruções de Uso */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Shield className="w-5 h-5 mr-2 text-blue-600" />
          Como Usar o Sistema de Recovery
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">🎯 Dashboard Robusto</h3>
            <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
              <li>Monitora automaticamente o status da conexão</li>
              <li>Exibe diferentes estados visuais por modo de recovery</li>
              <li>Permite retry manual e limpeza de cache</li>
              <li>Mostra métricas de rede e tempo de resposta</li>
              <li>Alertas contextuais para cada situação</li>
            </ul>
          </div>

          <div>
            <h3 className="font-medium text-gray-900 mb-2">⚡ Simulador de Erros</h3>
            <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
              <li>Teste 7 cenários diferentes de falha</li>
              <li>Configure duração e comportamento automático</li>
              <li>Monitore tentativas e tempo de recuperação</li>
              <li>Simule condições extremas de rede</li>
              <li>Observe o sistema em ação durante as falhas</li>
            </ul>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-100 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">💡 Dica de Teste</h4>
          <p className="text-sm text-blue-800">
            1. Abra as duas abas lado a lado<br />
            2. No <strong>Simulador</strong>, selecione um cenário e inicie<br />
            3. No <strong>Dashboard</strong>, observe como o sistema reage automaticamente<br />
            4. Teste os botões de retry manual e limpeza de cache<br />
            5. Verifique os alertas e mudanças visuais de estado
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center py-8 border-t">
        <p className="text-sm text-gray-500">
          Sistema de Error Recovery implementado com <strong>React Query</strong>, <strong>LocalStorage Cache</strong> e <strong>Network API</strong>
        </p>
      </div>
    </div>
  )
}
