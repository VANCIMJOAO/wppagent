/**
 * Componente de Drill-Down para Analytics
 * Permite detalhar métricas específicas com navegação hierárquica
 */
'use client';

import React, { useState, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  ChevronRight, 
  ArrowLeft, 
  TrendingUp, 
  Users, 
  MessageCircle, 
  Target,
  Calendar,
  BarChart3
} from 'lucide-react';
import { useAnalytics } from '@/hooks/useAnalytics';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// Tipos para drill-down
export interface DrillDownLevel {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  endpoint: string;
  filters?: Record<string, any>;
  parentId?: string;
}

export interface DrillDownPath {
  levels: DrillDownLevel[];
  currentLevel: number;
}

// Configuração dos níveis de drill-down
const DRILL_DOWN_CONFIGS: Record<string, DrillDownLevel[]> = {
  conversations: [
    {
      id: 'conversations-overview',
      title: 'Visão Geral de Conversas',
      description: 'Métricas gerais de conversas',
      icon: <MessageCircle className="w-5 h-5" />,
      endpoint: 'conversations',
    },
    {
      id: 'conversations-by-channel',
      title: 'Conversas por Canal',
      description: 'Breakdown por canal de comunicação',
      icon: <BarChart3 className="w-5 h-5" />,
      endpoint: 'conversations',
      filters: { groupBy: 'channel' },
      parentId: 'conversations-overview',
    },
    {
      id: 'conversations-by-agent',
      title: 'Conversas por Agente',
      description: 'Performance individual dos agentes',
      icon: <Users className="w-5 h-5" />,
      endpoint: 'conversations',
      filters: { groupBy: 'agent' },
      parentId: 'conversations-overview',
    },
    {
      id: 'conversations-by-hour',
      title: 'Conversas por Horário',
      description: 'Distribuição ao longo do dia',
      icon: <Calendar className="w-5 h-5" />,
      endpoint: 'conversations',
      filters: { groupBy: 'hour' },
      parentId: 'conversations-overview',
    },
  ],
  performance: [
    {
      id: 'performance-overview',
      title: 'Performance Geral',
      description: 'KPIs principais do sistema',
      icon: <TrendingUp className="w-5 h-5" />,
      endpoint: 'performance',
    },
    {
      id: 'agent-performance',
      title: 'Performance de Agentes',
      description: 'Métricas individuais por agente',
      icon: <Users className="w-5 h-5" />,
      endpoint: 'performance',
      filters: { focus: 'agents' },
      parentId: 'performance-overview',
    },
    {
      id: 'system-performance',
      title: 'Performance do Sistema',
      description: 'Métricas técnicas e infraestrutura',
      icon: <Target className="w-5 h-5" />,
      endpoint: 'performance',
      filters: { focus: 'system' },
      parentId: 'performance-overview',
    },
  ],
};

interface DrillDownProps {
  metricType: 'conversations' | 'performance' | 'channels';
  initialData?: any;
  onLevelChange?: (level: DrillDownLevel, data: any) => void;
  className?: string;
}

export const DrillDownAnalytics: React.FC<DrillDownProps> = ({
  metricType,
  initialData,
  onLevelChange,
  className = '',
}) => {
  const [drillPath, setDrillPath] = useState<DrillDownPath>({
    levels: DRILL_DOWN_CONFIGS[metricType] || [],
    currentLevel: 0,
  });

  const currentLevel = drillPath.levels[drillPath.currentLevel];
  const canGoBack = drillPath.currentLevel > 0;
  const canGoDeeper = drillPath.currentLevel < drillPath.levels.length - 1;

  // Hook para dados do nível atual
  const { data, loading, error } = useAnalytics(
    currentLevel?.endpoint || metricType,
    currentLevel?.filters ? { ...currentLevel.filters } : {}
  );

  // Navegar para nível mais profundo
  const drillDown = useCallback((targetLevelId?: string) => {
    if (!canGoDeeper) return;

    const nextLevelIndex = targetLevelId 
      ? drillPath.levels.findIndex(l => l.id === targetLevelId)
      : drillPath.currentLevel + 1;

    if (nextLevelIndex > -1 && nextLevelIndex < drillPath.levels.length) {
      setDrillPath(prev => ({
        ...prev,
        currentLevel: nextLevelIndex,
      }));

      const nextLevel = drillPath.levels[nextLevelIndex];
      onLevelChange?.(nextLevel, data);
    }
  }, [canGoDeeper, drillPath, data, onLevelChange]);

  // Voltar ao nível anterior
  const drillUp = useCallback(() => {
    if (!canGoBack) return;

    setDrillPath(prev => ({
      ...prev,
      currentLevel: prev.currentLevel - 1,
    }));
  }, [canGoBack]);

  // Reset para o primeiro nível
  const resetToDrillRoot = useCallback(() => {
    setDrillPath(prev => ({
      ...prev,
      currentLevel: 0,
    }));
  }, []);

  if (!currentLevel) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center text-gray-500">
            <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <p>Configuração de drill-down não encontrada para "{metricType}"</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {currentLevel.icon}
            <div>
              <CardTitle className="text-lg">{currentLevel.title}</CardTitle>
              <p className="text-sm text-gray-600">{currentLevel.description}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {canGoBack && (
              <Button
                variant="outline"
                size="sm"
                onClick={drillUp}
                className="flex items-center space-x-1"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Voltar</span>
              </Button>
            )}

            {drillPath.currentLevel > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={resetToDrillRoot}
                className="text-blue-600 hover:text-blue-800"
              >
                Início
              </Button>
            )}
          </div>
        </div>

        {/* Breadcrumb */}
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          {drillPath.levels.slice(0, drillPath.currentLevel + 1).map((level, index) => (
            <React.Fragment key={level.id}>
              {index > 0 && <ChevronRight className="w-4 h-4" />}
              <button
                onClick={() => setDrillPath(prev => ({ ...prev, currentLevel: index }))}
                className="hover:text-blue-600 transition-colors"
              >
                {level.title}
              </button>
            </React.Fragment>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {loading && (
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="grid grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-20 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Erro ao carregar dados detalhados: {error}</p>
          </div>
        )}

        {data && !loading && (
          <div className="space-y-6">
            {/* Resumo do nível atual */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">Resumo</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {data.totalConversations?.toLocaleString() || data.agentPerformance?.length || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">
                    {metricType === 'conversations' ? 'Conversas' : 'Agentes'}
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {data.totalMessages?.toLocaleString() || (data as any).systemPerformance?.uptime || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">
                    {metricType === 'conversations' ? 'Mensagens' : 'Uptime %'}
                  </div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {data.avgResponseTime || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Tempo Resposta</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {data.overallSatisfaction?.toFixed(1) || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Satisfação</div>
                </div>
              </div>
            </div>

            {/* Opções de drill-down */}
            {canGoDeeper && (
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Detalhar por:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {drillPath.levels
                    .filter(level => level.parentId === currentLevel.id)
                    .map((nextLevel) => (
                      <button
                        key={nextLevel.id}
                        onClick={() => drillDown(nextLevel.id)}
                        className="p-4 border rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                      >
                        <div className="flex items-center space-x-3">
                          {nextLevel.icon}
                          <div>
                            <div className="font-medium">{nextLevel.title}</div>
                            <div className="text-sm text-gray-600">{nextLevel.description}</div>
                          </div>
                        </div>
                      </button>
                    ))
                  }
                </div>
              </div>
            )}

            {/* Dados específicos do nível */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Dados Detalhados</h4>
              <div className="bg-gray-50 rounded-lg p-4">
                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                  {JSON.stringify(data, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DrillDownAnalytics;
