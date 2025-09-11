/**
 * Sistema de Relatórios Automatizados
 * Geração e envio automático de relatórios via email/WhatsApp
 */
'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Calendar,
  Clock,
  Send,
  Settings,
  FileText,
  Download,
  Mail,
  MessageSquare,
  Play,
  Pause,
  Edit3,
  Trash2,
  Plus,
  CheckCircle,
  XCircle,
  AlertCircle,
  Save
} from 'lucide-react';
import { format, addDays, addWeeks, addMonths } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// Tipos para relatórios automatizados
export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  type: 'overview' | 'performance' | 'conversations' | 'custom';
  frequency: 'daily' | 'weekly' | 'monthly' | 'custom';
  schedule: {
    time: string; // HH:mm
    dayOfWeek?: number; // 0-6 para semanal
    dayOfMonth?: number; // 1-31 para mensal
    customCron?: string; // Para frequência customizada
  };
  recipients: {
    email: string[];
    whatsapp: string[];
  };
  format: 'pdf' | 'excel' | 'csv' | 'html';
  sections: ReportSection[];
  filters: Record<string, any>;
  active: boolean;
  createdAt: Date;
  lastRun?: Date;
  nextRun?: Date;
}

export interface ReportSection {
  id: string;
  title: string;
  type: 'metric_summary' | 'chart' | 'table' | 'text' | 'image';
  config: {
    dataSource: string;
    metric?: string;
    chartType?: 'line' | 'bar' | 'pie' | 'area';
    period?: string;
    filters?: Record<string, any>;
    customText?: string;
    showTrends?: boolean;
    includePreviousPeriod?: boolean;
  };
  order: number;
}

export interface ReportExecution {
  id: string;
  templateId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: Date;
  completedAt?: Date;
  error?: string;
  fileUrl?: string;
  recipients: string[];
  deliveryStatus: {
    email: Record<string, 'sent' | 'failed'>;
    whatsapp: Record<string, 'sent' | 'failed'>;
  };
}

// Templates pré-configurados
const REPORT_TEMPLATES: Partial<ReportTemplate>[] = [
  {
    name: 'Relatório Diário de Overview',
    description: 'Resumo diário das principais métricas',
    type: 'overview',
    frequency: 'daily',
    schedule: { time: '09:00' },
    format: 'pdf',
    sections: [
      {
        id: 'summary',
        title: 'Resumo Executivo',
        type: 'metric_summary',
        config: {
          dataSource: 'overview',
          period: 'yesterday',
          showTrends: true,
          includePreviousPeriod: true,
        },
        order: 1,
      },
      {
        id: 'conversations',
        title: 'Conversas por Canal',
        type: 'chart',
        config: {
          dataSource: 'channels',
          chartType: 'bar',
          period: 'yesterday',
        },
        order: 2,
      },
      {
        id: 'satisfaction',
        title: 'Satisfação do Cliente',
        type: 'chart',
        config: {
          dataSource: 'conversations',
          chartType: 'pie',
          metric: 'satisfaction',
          period: 'yesterday',
        },
        order: 3,
      },
    ],
  },
  {
    name: 'Relatório Semanal de Performance',
    description: 'Análise semanal de performance dos agentes',
    type: 'performance',
    frequency: 'weekly',
    schedule: { time: '08:00', dayOfWeek: 1 }, // Segunda-feira
    format: 'excel',
    sections: [
      {
        id: 'agent_performance',
        title: 'Performance Individual dos Agentes',
        type: 'table',
        config: {
          dataSource: 'performance',
          period: 'last_week',
          showTrends: true,
        },
        order: 1,
      },
      {
        id: 'response_times',
        title: 'Tempos de Resposta',
        type: 'chart',
        config: {
          dataSource: 'performance',
          chartType: 'line',
          metric: 'response_times',
          period: 'last_week',
        },
        order: 2,
      },
    ],
  },
  {
    name: 'Relatório Mensal Executivo',
    description: 'Relatório completo mensal para executivos',
    type: 'custom',
    frequency: 'monthly',
    schedule: { time: '07:00', dayOfMonth: 1 },
    format: 'pdf',
    sections: [
      {
        id: 'executive_summary',
        title: 'Resumo Executivo',
        type: 'text',
        config: {
          dataSource: 'overview',
          customText: 'Análise mensal completa das operações de atendimento',
        },
        order: 1,
      },
      {
        id: 'kpis',
        title: 'Principais Indicadores',
        type: 'metric_summary',
        config: {
          dataSource: 'overview',
          period: 'last_month',
          showTrends: true,
          includePreviousPeriod: true,
        },
        order: 2,
      },
      {
        id: 'trends',
        title: 'Tendências Mensais',
        type: 'chart',
        config: {
          dataSource: 'overview',
          chartType: 'line',
          period: 'last_month',
        },
        order: 3,
      },
    ],
  },
];

interface AutomatedReportsProps {
  className?: string;
  onReportCreate?: (template: ReportTemplate) => void;
  onReportUpdate?: (template: ReportTemplate) => void;
  onReportDelete?: (templateId: string) => void;
}

export const AutomatedReports: React.FC<AutomatedReportsProps> = ({
  className = '',
  onReportCreate,
  onReportUpdate,
  onReportDelete,
}) => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [executions, setExecutions] = useState<ReportExecution[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<ReportTemplate | null>(null);
  const [selectedTab, setSelectedTab] = useState<'templates' | 'executions' | 'settings'>('templates');

  // Carregar dados iniciais
  useEffect(() => {
    loadTemplates();
    loadExecutions();
  }, []);

  // ✅ SEGURO: localStorage para templates de relatório (não-sensível)
  const loadTemplates = useCallback(() => {
    try {
      const saved = localStorage.getItem('automated_report_templates');
      if (saved) {
        const parsedTemplates = JSON.parse(saved);
        setTemplates(parsedTemplates.map((t: any) => ({
          ...t,
          createdAt: new Date(t.createdAt),
          lastRun: t.lastRun ? new Date(t.lastRun) : undefined,
          nextRun: t.nextRun ? new Date(t.nextRun) : undefined,
        })));
      } else {
        // Inicializar com templates padrão
        const defaultTemplates = REPORT_TEMPLATES.map((template, index) => ({
          ...template,
          id: `template_${index}`,
          recipients: { email: [], whatsapp: [] },
          filters: {},
          active: false,
          createdAt: new Date(),
          nextRun: calculateNextRun(template as ReportTemplate),
        })) as ReportTemplate[];
        
        setTemplates(defaultTemplates);
        saveTemplates(defaultTemplates);
      }
    } catch (error) {
      console.error('Erro ao carregar templates:', error);
    }
  }, []);

  // Carregar execuções do localStorage
  const loadExecutions = useCallback(() => {
    try {
      const saved = localStorage.getItem('report_executions');
      if (saved) {
        const parsedExecutions = JSON.parse(saved);
        setExecutions(parsedExecutions.map((e: any) => ({
          ...e,
          startedAt: new Date(e.startedAt),
          completedAt: e.completedAt ? new Date(e.completedAt) : undefined,
        })));
      }
    } catch (error) {
      console.error('Erro ao carregar execuções:', error);
    }
  }, []);

  // Salvar templates
  const saveTemplates = useCallback((templates: ReportTemplate[]) => {
    localStorage.setItem('automated_report_templates', JSON.stringify(templates));
  }, []);

  // Calcular próxima execução
  const calculateNextRun = (template: ReportTemplate): Date => {
    const now = new Date();
    const [hours, minutes] = template.schedule.time.split(':').map(Number);
    
    let nextRun = new Date(now);
    nextRun.setHours(hours, minutes, 0, 0);
    
    // Se o horário já passou hoje, calcular para o próximo período
    if (nextRun <= now) {
      switch (template.frequency) {
        case 'daily':
          nextRun = addDays(nextRun, 1);
          break;
        case 'weekly':
          nextRun = addWeeks(nextRun, 1);
          break;
        case 'monthly':
          nextRun = addMonths(nextRun, 1);
          break;
      }
    }
    
    return nextRun;
  };

  // Alternar status ativo do template
  const toggleTemplateActive = useCallback((templateId: string) => {
    const updatedTemplates = templates.map(template => {
      if (template.id === templateId) {
        const updated = {
          ...template,
          active: !template.active,
          nextRun: !template.active ? calculateNextRun(template) : undefined,
        };
        return updated;
      }
      return template;
    });
    
    setTemplates(updatedTemplates);
    saveTemplates(updatedTemplates);
  }, [templates, saveTemplates]);

  // Executar relatório manualmente
  const executeReport = useCallback(async (templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;

    const execution: ReportExecution = {
      id: `execution_${Date.now()}`,
      templateId,
      status: 'running',
      startedAt: new Date(),
      recipients: [...template.recipients.email, ...template.recipients.whatsapp],
      deliveryStatus: { email: {}, whatsapp: {} },
    };

    setExecutions(prev => [execution, ...prev]);

    // Simular execução (em produção, seria uma chamada para API)
    setTimeout(() => {
      const completedExecution: ReportExecution = {
        ...execution,
        status: 'completed',
        completedAt: new Date(),
        fileUrl: `/reports/${execution.id}.pdf`,
      };

      setExecutions(prev => 
        prev.map(e => e.id === execution.id ? completedExecution : e)
      );

      // Atualizar template com última execução
      const updatedTemplates = templates.map(t => 
        t.id === templateId 
          ? { ...t, lastRun: new Date(), nextRun: calculateNextRun(t) }
          : t
      );
      setTemplates(updatedTemplates);
      saveTemplates(updatedTemplates);
    }, 3000);
  }, [templates, saveTemplates]);

  // Remover template
  const deleteTemplate = useCallback((templateId: string) => {
    const updatedTemplates = templates.filter(t => t.id !== templateId);
    setTemplates(updatedTemplates);
    saveTemplates(updatedTemplates);
    onReportDelete?.(templateId);
  }, [templates, saveTemplates, onReportDelete]);

  // Renderizar lista de templates
  const renderTemplates = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Templates de Relatório</h3>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Novo Template
        </Button>
      </div>

      <div className="grid gap-4">
        {templates.map(template => (
          <Card key={template.id}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h4 className="font-medium">{template.name}</h4>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      template.active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {template.active ? 'Ativo' : 'Inativo'}
                    </span>
                  </div>
                  
                  <p className="text-sm text-gray-600 mt-1">
                    {template.description}
                  </p>
                  
                  <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {template.frequency === 'daily' && 'Diário'}
                      {template.frequency === 'weekly' && 'Semanal'}
                      {template.frequency === 'monthly' && 'Mensal'}
                    </div>
                    
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      {template.schedule.time}
                    </div>
                    
                    <div className="flex items-center">
                      <FileText className="w-4 h-4 mr-1" />
                      {template.format.toUpperCase()}
                    </div>

                    {template.nextRun && (
                      <div className="flex items-center">
                        <AlertCircle className="w-4 h-4 mr-1" />
                        Próximo: {format(template.nextRun, 'dd/MM HH:mm', { locale: ptBR })}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => executeReport(template.id)}
                    disabled={!template.active}
                  >
                    <Play className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => toggleTemplateActive(template.id)}
                  >
                    {template.active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setEditingTemplate(template)}
                  >
                    <Edit3 className="w-4 h-4" />
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteTemplate(template.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  // Renderizar histórico de execuções
  const renderExecutions = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-medium">Histórico de Execuções</h3>
      
      <div className="grid gap-4">
        {executions.map(execution => {
          const template = templates.find(t => t.id === execution.templateId);
          
          return (
            <Card key={execution.id}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{template?.name}</h4>
                    <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                      <span>
                        {format(execution.startedAt, 'dd/MM/yyyy HH:mm', { locale: ptBR })}
                      </span>
                      
                      <div className="flex items-center">
                        {execution.status === 'completed' && (
                          <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
                        )}
                        {execution.status === 'failed' && (
                          <XCircle className="w-4 h-4 text-red-500 mr-1" />
                        )}
                        {execution.status === 'running' && (
                          <AlertCircle className="w-4 h-4 text-blue-500 mr-1" />
                        )}
                        {execution.status}
                      </div>
                      
                      <span>
                        {execution.recipients.length} destinatários
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {execution.fileUrl && (
                      <Button variant="ghost" size="sm">
                        <Download className="w-4 h-4" />
                      </Button>
                    )}
                    
                    <Button variant="ghost" size="sm">
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Cabeçalho */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            Relatórios Automatizados
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        {(['templates', 'executions', 'settings'] as const).map(tab => (
          <Button
            key={tab}
            variant={selectedTab === tab ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setSelectedTab(tab)}
            className="flex-1"
          >
            {tab === 'templates' && 'Templates'}
            {tab === 'executions' && 'Execuções'}
            {tab === 'settings' && 'Configurações'}
          </Button>
        ))}
      </div>

      {/* Conteúdo das tabs */}
      {selectedTab === 'templates' && renderTemplates()}
      {selectedTab === 'executions' && renderExecutions()}
      {selectedTab === 'settings' && (
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-medium mb-4">Configurações Globais</h3>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Servidor SMTP</label>
                <input 
                  type="text" 
                  className="w-full mt-1 p-2 border rounded" 
                  placeholder="smtp.gmail.com"
                />
              </div>
              <div>
                <label className="text-sm font-medium">API WhatsApp</label>
                <input 
                  type="text" 
                  className="w-full mt-1 p-2 border rounded" 
                  placeholder="https://api.whatsapp.com"
                />
              </div>
              <Button>
                <Save className="w-4 h-4 mr-2" />
                Salvar Configurações
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AutomatedReports;
