/**
 * Sistema de Alertas Inteligentes para Analytics
 * Monitora métricas e dispara notificações baseadas em thresholds
 */
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Bell, 
  Settings, 
  TrendingDown,
  TrendingUp,
  Clock,
  Users,
  MessageCircle
} from 'lucide-react';
import { useAnalytics } from '@/hooks/useAnalytics';

// Tipos para alertas
export interface AlertThreshold {
  id: string;
  metric: string;
  label: string;
  condition: 'greater_than' | 'less_than' | 'equals' | 'not_equals';
  value: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled: boolean;
  description: string;
  icon: React.ReactNode;
}

export interface Alert {
  id: string;
  thresholdId: string;
  metric: string;
  currentValue: number;
  thresholdValue: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: Date;
  acknowledged: boolean;
  resolved: boolean;
  description: string;
}

// Configuração padrão de thresholds
const DEFAULT_THRESHOLDS: AlertThreshold[] = [
  {
    id: 'response_time_high',
    metric: 'avgResponseTime',
    label: 'Tempo de Resposta Alto',
    condition: 'greater_than',
    value: 60, // 60 segundos
    severity: 'high',
    enabled: true,
    description: 'Alerta quando tempo médio de resposta excede 60 segundos',
    icon: <Clock className="w-4 h-4" />,
  },
  {
    id: 'satisfaction_low',
    metric: 'overallSatisfaction',
    label: 'Satisfação Baixa',
    condition: 'less_than',
    value: 4.0,
    severity: 'medium',
    enabled: true,
    description: 'Alerta quando satisfação geral cai abaixo de 4.0',
    icon: <TrendingDown className="w-4 h-4" />,
  },
  {
    id: 'conversations_spike',
    metric: 'totalConversations',
    label: 'Pico de Conversas',
    condition: 'greater_than',
    value: 5000,
    severity: 'medium',
    enabled: true,
    description: 'Alerta quando número de conversas excede 5000',
    icon: <MessageCircle className="w-4 h-4" />,
  },
  {
    id: 'agents_offline',
    metric: 'activeAgents',
    label: 'Poucos Agentes Online',
    condition: 'less_than',
    value: 2,
    severity: 'critical',
    enabled: true,
    description: 'Alerta crítico quando menos de 2 agentes estão online',
    icon: <Users className="w-4 h-4" />,
  },
];

const SEVERITY_COLORS = {
  low: 'bg-blue-100 text-blue-800 border-blue-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  critical: 'bg-red-100 text-red-800 border-red-200',
};

const SEVERITY_ICONS = {
  low: <CheckCircle className="w-4 h-4" />,
  medium: <AlertTriangle className="w-4 h-4" />,
  high: <AlertTriangle className="w-4 h-4" />,
  critical: <XCircle className="w-4 h-4" />,
};

interface AlertsSystemProps {
  className?: string;
  onAlertTriggered?: (alert: Alert) => void;
  enableNotifications?: boolean;
}

export const AlertsSystem: React.FC<AlertsSystemProps> = ({
  className = '',
  onAlertTriggered,
  enableNotifications = true,
}) => {
  const [thresholds, setThresholds] = useState<AlertThreshold[]>(DEFAULT_THRESHOLDS);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [showSettings, setShowSettings] = useState(false);

  // Dados do analytics para monitoramento
  const { data: analyticsData, loading } = useAnalytics('overview', {}, 30000); // Refresh a cada 30s

  // Função para avaliar thresholds
  const evaluateThresholds = useCallback((data: any) => {
    if (!data) return;

    const newAlerts: Alert[] = [];

    thresholds
      .filter(threshold => threshold.enabled)
      .forEach(threshold => {
        const currentValue = data[threshold.metric];
        if (currentValue === undefined || currentValue === null) return;

        let shouldTrigger = false;

        switch (threshold.condition) {
          case 'greater_than':
            shouldTrigger = currentValue > threshold.value;
            break;
          case 'less_than':
            shouldTrigger = currentValue < threshold.value;
            break;
          case 'equals':
            shouldTrigger = currentValue === threshold.value;
            break;
          case 'not_equals':
            shouldTrigger = currentValue !== threshold.value;
            break;
        }

        if (shouldTrigger) {
          const existingAlert = alerts.find(
            alert => alert.thresholdId === threshold.id && !alert.resolved
          );

          if (!existingAlert) {
            const newAlert: Alert = {
              id: `alert_${Date.now()}_${threshold.id}`,
              thresholdId: threshold.id,
              metric: threshold.metric,
              currentValue,
              thresholdValue: threshold.value,
              severity: threshold.severity,
              message: `${threshold.label}: ${currentValue} ${threshold.condition.replace('_', ' ')} ${threshold.value}`,
              timestamp: new Date(),
              acknowledged: false,
              resolved: false,
              description: threshold.description,
            };

            newAlerts.push(newAlert);
            onAlertTriggered?.(newAlert);

            // Notificação do browser
            if (enableNotifications && 'Notification' in window && Notification.permission === 'granted') {
              new Notification(`WhatsApp Analytics - ${threshold.label}`, {
                body: newAlert.message,
                icon: '/favicon.ico',
                tag: newAlert.id,
              });
            }
          }
        }
      });

    if (newAlerts.length > 0) {
      setAlerts(prev => [...newAlerts, ...prev]);
    }
  }, [thresholds, alerts, onAlertTriggered, enableNotifications]);

  // Solicitar permissão para notificações
  useEffect(() => {
    if (enableNotifications && 'Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, [enableNotifications]);

  // Avaliar thresholds quando dados mudarem
  useEffect(() => {
    if (analyticsData && !loading) {
      evaluateThresholds(analyticsData);
    }
  }, [analyticsData, loading, evaluateThresholds]);

  // Reconhecer alerta
  const acknowledgeAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId 
        ? { ...alert, acknowledged: true }
        : alert
    ));
  }, []);

  // Resolver alerta
  const resolveAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId 
        ? { ...alert, resolved: true }
        : alert
    ));
  }, []);

  // Alternar threshold
  const toggleThreshold = useCallback((thresholdId: string) => {
    setThresholds(prev => prev.map(threshold =>
      threshold.id === thresholdId
        ? { ...threshold, enabled: !threshold.enabled }
        : threshold
    ));
  }, []);

  const activeAlerts = alerts.filter(alert => !alert.resolved);
  const criticalAlerts = activeAlerts.filter(alert => alert.severity === 'critical');

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header com contador de alertas */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Bell className="w-6 h-6 text-blue-500" />
              <div>
                <CardTitle>Sistema de Alertas</CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  Monitoramento inteligente com {thresholds.filter(t => t.enabled).length} regras ativas
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {activeAlerts.length > 0 && (
                <Badge variant="destructive">
                  {activeAlerts.length} ativo{activeAlerts.length !== 1 ? 's' : ''}
                </Badge>
              )}
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSettings(!showSettings)}
              >
                <Settings className="w-4 h-4 mr-2" />
                Configurar
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Alertas críticos em destaque */}
          {criticalAlerts.length > 0 && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h4 className="font-medium text-red-900 mb-3 flex items-center">
                <XCircle className="w-5 h-5 mr-2" />
                Alertas Críticos ({criticalAlerts.length})
              </h4>
              <div className="space-y-2">
                {criticalAlerts.map((alert) => (
                  <div key={alert.id} className="flex items-center justify-between p-2 bg-white rounded border-l-4 border-red-500">
                    <div>
                      <div className="font-medium text-red-900">{alert.message}</div>
                      <div className="text-sm text-red-700">
                        {alert.timestamp.toLocaleString('pt-BR')}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      {!alert.acknowledged && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          Reconhecer
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => resolveAlert(alert.id)}
                      >
                        Resolver
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Lista de todos os alertas ativos */}
          {activeAlerts.length > 0 ? (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">
                Alertas Ativos ({activeAlerts.length})
              </h4>
              <div className="space-y-3">
                {activeAlerts
                  .filter(alert => alert.severity !== 'critical')
                  .slice(0, 5)
                  .map((alert) => (
                    <div key={alert.id} className={`p-4 rounded-lg border ${SEVERITY_COLORS[alert.severity]}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          {SEVERITY_ICONS[alert.severity]}
                          <div>
                            <div className="font-medium">{alert.message}</div>
                            <div className="text-sm opacity-75">
                              {alert.description}
                            </div>
                            <div className="text-xs opacity-75 mt-1">
                              {alert.timestamp.toLocaleString('pt-BR')}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          {alert.acknowledged && (
                            <Badge variant="secondary">Reconhecido</Badge>
                          )}
                          
                          <div className="flex space-x-1">
                            {!alert.acknowledged && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => acknowledgeAlert(alert.id)}
                              >
                                Reconhecer
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => resolveAlert(alert.id)}
                            >
                              Resolver
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
              <p className="text-lg font-medium">Tudo funcionando bem!</p>
              <p className="text-sm">Nenhum alerta ativo no momento</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Configurações de Thresholds */}
      {showSettings && (
        <Card>
          <CardHeader>
            <CardTitle>Configurações de Alertas</CardTitle>
            <p className="text-sm text-gray-600">
              Configure os thresholds para monitoramento automático
            </p>
          </CardHeader>
          
          <CardContent>
            <div className="space-y-4">
              {thresholds.map((threshold) => (
                <div key={threshold.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {threshold.icon}
                    <div>
                      <div className="font-medium">{threshold.label}</div>
                      <div className="text-sm text-gray-600">{threshold.description}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        Condição: {threshold.metric} {threshold.condition.replace('_', ' ')} {threshold.value}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <Badge variant={threshold.enabled ? 'default' : 'secondary'}>
                      {threshold.severity}
                    </Badge>
                    
                    <Button
                      variant={threshold.enabled ? 'destructive' : 'default'}
                      size="sm"
                      onClick={() => toggleThreshold(threshold.id)}
                    >
                      {threshold.enabled ? 'Desabilitar' : 'Habilitar'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AlertsSystem;
