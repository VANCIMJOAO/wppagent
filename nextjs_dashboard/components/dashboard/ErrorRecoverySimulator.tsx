/**
 * Simulador de Cenários de Error Recovery
 * Permite testar diferentes tipos de falhas e recuperações
 */
'use client'

import React, { useState, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
// Slider component not available, using input range
import {
  Zap,
  Wifi,
  WifiOff,
  Server,
  Clock,
  AlertTriangle,
  Settings,
  Play,
  Square,
  RotateCcw,
  Activity,
  Database,
  Network
} from 'lucide-react'
import { toast } from 'sonner'

// Tipos de cenários de erro disponíveis
type ErrorScenario = {
  id: string
  name: string
  description: string
  type: 'network' | 'server' | 'timeout' | 'auth' | 'mixed'
  severity: 'low' | 'medium' | 'high' | 'critical'
  duration: number // em segundos
  icon: React.ReactNode
}

const ERROR_SCENARIOS: ErrorScenario[] = [
  {
    id: 'network_slow',
    name: 'Rede Lenta',
    description: 'Simula conexão lenta (2G/3G)',
    type: 'network',
    severity: 'low',
    duration: 30,
    icon: <Network className="w-4 h-4" />
  },
  {
    id: 'network_unstable',
    name: 'Rede Instável',
    description: 'Conexão intermitente com falhas ocasionais',
    type: 'network',
    severity: 'medium',
    duration: 60,
    icon: <WifiOff className="w-4 h-4" />
  },
  {
    id: 'server_overload',
    name: 'Servidor Sobrecarregado',
    description: 'Respostas lentas e timeouts (503 errors)',
    type: 'server',
    severity: 'high',
    duration: 45,
    icon: <Server className="w-4 h-4" />
  },
  {
    id: 'server_maintenance',
    name: 'Manutenção',
    description: 'Servidor indisponível temporariamente',
    type: 'server',
    severity: 'critical',
    duration: 120,
    icon: <Settings className="w-4 h-4" />
  },
  {
    id: 'timeout_cascade',
    name: 'Timeouts em Cascata',
    description: 'Múltiplos timeouts sequenciais',
    type: 'timeout',
    severity: 'high',
    duration: 90,
    icon: <Clock className="w-4 h-4" />
  },
  {
    id: 'auth_expired',
    name: 'Sessão Expirada',
    description: 'Token de autenticação inválido (401)',
    type: 'auth',
    severity: 'medium',
    duration: 20,
    icon: <AlertTriangle className="w-4 h-4" />
  },
  {
    id: 'disaster_scenario',
    name: 'Cenário Catastrófico',
    description: 'Múltiplas falhas simultâneas',
    type: 'mixed',
    severity: 'critical',
    duration: 180,
    icon: <Zap className="w-4 h-4" />
  }
]

interface ErrorRecoverySimulatorProps {
  className?: string
}

export const ErrorRecoverySimulator: React.FC<ErrorRecoverySimulatorProps> = ({
  className = ''
}) => {
  const [isSimulating, setIsSimulating] = useState(false)
  const [activeScenario, setActiveScenario] = useState<ErrorScenario | null>(null)
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('')
  const [customDuration, setCustomDuration] = useState<number[]>([60])
  const [autoRecover, setAutoRecover] = useState(true)
  const [networkThrottling, setNetworkThrottling] = useState(false)
  const [cacheCorruption, setCacheCorruption] = useState(false)
  const [simultaneousErrors, setSimultaneousErrors] = useState(false)

  // Estado de monitoramento
  const [recoveryAttempts, setRecoveryAttempts] = useState(0)
  const [totalFailures, setTotalFailures] = useState(0)
  const [averageRecoveryTime, setAverageRecoveryTime] = useState(0)
  const [currentMode, setCurrentMode] = useState<'normal' | 'cached' | 'degraded' | 'offline'>('normal')

  const startSimulation = useCallback(async () => {
    const scenario = ERROR_SCENARIOS.find(s => s.id === selectedScenarioId)
    if (!scenario) {
      toast.error('Selecione um cenário para simular')
      return
    }

    setIsSimulating(true)
    setActiveScenario(scenario)
    setRecoveryAttempts(0)
    setTotalFailures(0)

    const startTime = Date.now()

    // Simular o erro baseado no cenário
    const simulateError = () => {
      switch (scenario.type) {
        case 'network':
          setCurrentMode('offline')
          toast.warning(`🌐 ${scenario.name} - Tentando recovery automático...`)
          break
        case 'server':
          setCurrentMode('degraded')
          toast.error(`🔥 ${scenario.name} - Sistema em modo degradado`)
          break
        case 'timeout':
          setCurrentMode('cached')
          toast.info(`⏱️ ${scenario.name} - Usando dados em cache`)
          break
        case 'auth':
          setCurrentMode('normal')
          toast.warning(`🔐 ${scenario.name} - Reautenticando...`)
          break
        case 'mixed':
          setCurrentMode('offline')
          toast.error(`💥 ${scenario.name} - Múltiplas falhas detectadas!`)
          break
      }
    }

    simulateError()

    // Simular tentativas de recovery
    const recoveryInterval = setInterval(() => {
      setRecoveryAttempts(prev => {
        const newAttempts = prev + 1

        // Log das tentativas
        console.log(`Recovery attempt ${newAttempts} for scenario: ${scenario.name}`)

        // Simular sucesso gradual baseado na severidade
        const successChance = scenario.severity === 'critical' ? 0.1 :
                             scenario.severity === 'high' ? 0.25 :
                             scenario.severity === 'medium' ? 0.4 : 0.6

        if (Math.random() < successChance && newAttempts > 2) {
          clearInterval(recoveryInterval)
          const recoveryTime = Date.now() - startTime
          setAverageRecoveryTime(recoveryTime / 1000)
          setCurrentMode('normal')
          toast.success(`✅ Recovery bem-sucedido! Tempo: ${(recoveryTime / 1000).toFixed(1)}s`)

          if (autoRecover) {
            setTimeout(() => {
              setIsSimulating(false)
              setActiveScenario(null)
            }, 3000)
          }
        } else {
          setTotalFailures(prev => prev + 1)
          toast.warning(`🔄 Tentativa ${newAttempts} falhou - Retry em ${2 ** newAttempts}s`)
        }

        return newAttempts
      })
    }, 3000) // Tentativa a cada 3 segundos

    // Auto-stop após duração do cenário (se autoRecover estiver ativo)
    if (autoRecover) {
      setTimeout(() => {
        clearInterval(recoveryInterval)
        setIsSimulating(false)
        setActiveScenario(null)
        setCurrentMode('normal')
        toast.info('Simulação finalizada automaticamente')
      }, scenario.duration * 1000)
    }

  }, [selectedScenarioId, autoRecover])

  const stopSimulation = useCallback(() => {
    setIsSimulating(false)
    setActiveScenario(null)
    setCurrentMode('normal')
    toast.info('Simulação interrompida manualmente')
  }, [])

  const resetStats = useCallback(() => {
    setRecoveryAttempts(0)
    setTotalFailures(0)
    setAverageRecoveryTime(0)
    toast.success('Estatísticas resetadas')
  }, [])

  const getSeverityColor = (severity: ErrorScenario['severity']) => {
    switch (severity) {
      case 'low': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'critical': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getModeColor = (mode: typeof currentMode) => {
    switch (mode) {
      case 'normal': return 'bg-green-500'
      case 'cached': return 'bg-yellow-500'
      case 'degraded': return 'bg-orange-500'
      case 'offline': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Cabeçalho */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-blue-600" />
            <span>Simulador de Error Recovery</span>
            {isSimulating && (
              <Badge variant="destructive" className="animate-pulse">
                Simulando
              </Badge>
            )}
          </CardTitle>
          <p className="text-sm text-gray-600">
            Teste diferentes cenários de falha e observe como o sistema se recupera
          </p>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuração da Simulação */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Configuração de Cenário</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Seleção de Cenário */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Cenário de Erro
              </label>
              <Select value={selectedScenarioId} onValueChange={setSelectedScenarioId}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione um cenário..." />
                </SelectTrigger>
                <SelectContent>
                  {ERROR_SCENARIOS.map(scenario => (
                    <SelectItem key={scenario.id} value={scenario.id}>
                      <div className="flex items-center space-x-2">
                        {scenario.icon}
                        <span>{scenario.name}</span>
                        <Badge className={getSeverityColor(scenario.severity)}>
                          {scenario.severity}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedScenarioId && (
                <p className="text-xs text-gray-600 mt-2">
                  {ERROR_SCENARIOS.find(s => s.id === selectedScenarioId)?.description}
                </p>
              )}
            </div>

            {/* Duração Customizada */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Duração (segundos): {customDuration[0]}s
              </label>
              <input
                type="range"
                min="10"
                max="300"
                step="10"
                value={customDuration[0]}
                onChange={(e) => setCustomDuration([parseInt(e.target.value)])}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Opções Avançadas */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Auto Recovery</span>
                <Switch
                  checked={autoRecover}
                  onCheckedChange={setAutoRecover}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Network Throttling</span>
                <Switch
                  checked={networkThrottling}
                  onCheckedChange={setNetworkThrottling}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Cache Corruption</span>
                <Switch
                  checked={cacheCorruption}
                  onCheckedChange={setCacheCorruption}
                />
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm">Simultaneous Errors</span>
                <Switch
                  checked={simultaneousErrors}
                  onCheckedChange={setSimultaneousErrors}
                />
              </div>
            </div>

            {/* Controles */}
            <div className="flex space-x-2 pt-4">
              <Button
                onClick={startSimulation}
                disabled={isSimulating || !selectedScenarioId}
                className="flex-1"
              >
                <Play className="w-4 h-4 mr-2" />
                Iniciar Simulação
              </Button>

              {isSimulating && (
                <Button
                  onClick={stopSimulation}
                  variant="outline"
                  className="flex-1"
                >
                  <Square className="w-4 h-4 mr-2" />
                  Parar
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Status e Monitoramento */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Status de Recovery</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Status Atual */}
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${getModeColor(currentMode)} animate-pulse`}></div>
                <span className="font-medium capitalize">{currentMode} Mode</span>
              </div>

              {isSimulating && (
                <Badge variant="outline">
                  {activeScenario?.name}
                </Badge>
              )}
            </div>

            {/* Métricas de Recovery */}
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {recoveryAttempts}
                </div>
                <div className="text-sm text-gray-600">Tentativas</div>
              </div>

              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">
                  {totalFailures}
                </div>
                <div className="text-sm text-gray-600">Falhas</div>
              </div>
            </div>

            {/* Tempo Médio de Recovery */}
            {averageRecoveryTime > 0 && (
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {averageRecoveryTime.toFixed(1)}s
                </div>
                <div className="text-sm text-gray-600">Tempo Recovery</div>
              </div>
            )}

            {/* Reset */}
            <Button
              onClick={resetStats}
              variant="ghost"
              size="sm"
              className="w-full"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset Estatísticas
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Lista de Cenários Disponíveis */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Cenários Disponíveis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ERROR_SCENARIOS.map(scenario => (
              <div
                key={scenario.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedScenarioId === scenario.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedScenarioId(scenario.id)}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {scenario.icon}
                    <span className="font-medium">{scenario.name}</span>
                  </div>
                  <Badge className={getSeverityColor(scenario.severity)}>
                    {scenario.severity}
                  </Badge>
                </div>

                <p className="text-sm text-gray-600 mb-2">
                  {scenario.description}
                </p>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Tipo: {scenario.type}</span>
                  <span>Duração: {scenario.duration}s</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ErrorRecoverySimulator
