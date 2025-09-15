"use client"

import React from 'react'
import { useBackendStatus, useRealDashboardData } from '@/hooks/useBackendStatus'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function BackendDiagnostic() {
  const backendStatus = useBackendStatus()
  const realData = useRealDashboardData()

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-3xl font-bold">🔍 Diagnóstico de Backend</h1>

      {/* Status de Conectividade */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Status de Conectividade
            <Badge variant={backendStatus.connected ? "default" : "destructive"}>
              {backendStatus.connected ? "Conectado" : "Desconectado"}
            </Badge>
          </CardTitle>
          <CardDescription>
            Última verificação: {backendStatus.lastCheck.toLocaleTimeString()}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {backendStatus.error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800 text-sm">Erro: {backendStatus.error}</p>
            </div>
          )}

          <div className="space-y-2">
            <h4 className="font-semibold">Endpoints Testados:</h4>
            {Object.entries(backendStatus.endpoints).map(([endpoint, status]) => (
              <div key={endpoint} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <code className="text-sm">{endpoint}</code>
                <Badge variant={status ? "default" : "secondary"}>
                  {status ? "✅ OK" : "❌ Falha"}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Dados Reais Encontrados */}
      <Card>
        <CardHeader>
          <CardTitle>Dados Reais do Backend</CardTitle>
          <CardDescription>
            Tentativa de buscar dados reais de vários endpoints
          </CardDescription>
        </CardHeader>
        <CardContent>
          {realData.loading && (
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
              <span>Buscando dados reais...</span>
            </div>
          )}

          {realData.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-800 text-sm">Erro: {realData.error}</p>
            </div>
          )}

          {realData.data && (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge variant="default">✅ Dados Encontrados</Badge>
                <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                  {realData.data.endpoint}
                </code>
              </div>

              <div className="bg-gray-50 p-4 rounded-md">
                <h4 className="font-semibold mb-2">Estrutura dos Dados:</h4>
                <pre className="text-xs overflow-auto max-h-96">
                  {JSON.stringify(realData.data.data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {!realData.loading && !realData.error && !realData.data && (
            <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
              <p className="text-yellow-800 text-sm">
                Nenhum endpoint de dados encontrado. O backend pode não estar disponível ou os endpoints podem ser diferentes.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recomendações */}
      <Card>
        <CardHeader>
          <CardTitle>🎯 Próximos Passos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">
              1. Verificar se o backend está rodando no Railway
            </p>
            <p className="text-sm text-gray-600">
              2. Conferir se os endpoints da API estão corretos
            </p>
            <p className="text-sm text-gray-600">
              3. Verificar configurações de CORS no backend
            </p>
            <p className="text-sm text-gray-600">
              4. Testar conectividade direta com o backend
            </p>
          </div>

          <div className="mt-4 pt-4 border-t">
            <p className="text-sm font-medium mb-2">Backend URL:</p>
            <code className="text-sm bg-gray-100 px-2 py-1 rounded">
              wppagent-production.up.railway.app
            </code>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
