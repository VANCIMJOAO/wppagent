/**
 * 🚀 AUTOMATED REPORTS CONSOLIDADO - FASE 3 REFATORAÇÃO
 * ======================================================
 * 
 * Sistema de relatórios automatizados consolidado que usa componentes modulares.
 * Substitui o AutomatedReports (611 linhas) por uma implementação modular.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, FileText } from 'lucide-react';
import { ReportTemplateCard, ReportExecutionCard, REPORT_TEMPLATES, calculateNextRun } from './index';
import type { ReportTemplate, ReportExecution, ReportFormData } from './types';
import { debugLog } from '@/lib/debug';

interface AutomatedReportsProps {
  className?: string;
  onReportCreate?: (template: ReportTemplate) => void;
  onReportUpdate?: (template: ReportTemplate) => void;
  onReportDelete?: (templateId: string) => void;
}

export const ConsolidatedAutomatedReports: React.FC<AutomatedReportsProps> = ({
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

  // Carregar templates do localStorage
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
      debugLog.error('Erro ao carregar templates:', error);
    }
  }, []);

  // Carregar execuções do localStorage
  const loadExecutions = useCallback(() => {
    try {
      const saved = localStorage.getItem('automated_report_executions');
      if (saved) {
        const parsedExecutions = JSON.parse(saved);
        setExecutions(parsedExecutions.map((e: any) => ({
          ...e,
          startTime: new Date(e.startTime),
          endTime: e.endTime ? new Date(e.endTime) : undefined,
        })));
      }
    } catch (error) {
      debugLog.error('Erro ao carregar execuções:', error);
    }
  }, []);

  // Salvar templates no localStorage
  const saveTemplates = useCallback((templatesToSave: ReportTemplate[]) => {
    try {
      localStorage.setItem('automated_report_templates', JSON.stringify(templatesToSave));
    } catch (error) {
      debugLog.error('Erro ao salvar templates:', error);
    }
  }, []);

  // Salvar execuções no localStorage
  const saveExecutions = useCallback((executionsToSave: ReportExecution[]) => {
    try {
      localStorage.setItem('automated_report_executions', JSON.stringify(executionsToSave));
    } catch (error) {
      debugLog.error('Erro ao salvar execuções:', error);
    }
  }, []);

  // Handlers para templates
  const handleCreateTemplate = useCallback((data: ReportFormData) => {
    const newTemplate: ReportTemplate = {
      id: `template_${Date.now()}`,
      ...data,
      active: false,
      createdAt: new Date(),
      nextRun: calculateNextRun(data as ReportTemplate),
    };

    const updatedTemplates = [...templates, newTemplate];
    setTemplates(updatedTemplates);
    saveTemplates(updatedTemplates);
    setShowCreateForm(false);
    
    onReportCreate?.(newTemplate);
  }, [templates, saveTemplates, onReportCreate]);

  const handleUpdateTemplate = useCallback((data: ReportFormData) => {
    if (!editingTemplate) return;

    const updatedTemplate: ReportTemplate = {
      ...editingTemplate,
      ...data,
      nextRun: calculateNextRun(data as ReportTemplate),
    };

    const updatedTemplates = templates.map(t => 
      t.id === editingTemplate.id ? updatedTemplate : t
    );
    
    setTemplates(updatedTemplates);
    saveTemplates(updatedTemplates);
    setEditingTemplate(null);
    
    onReportUpdate?.(updatedTemplate);
  }, [editingTemplate, templates, saveTemplates, onReportUpdate]);

  const handleDeleteTemplate = useCallback((templateId: string) => {
    const updatedTemplates = templates.filter(t => t.id !== templateId);
    setTemplates(updatedTemplates);
    saveTemplates(updatedTemplates);
    
    onReportDelete?.(templateId);
  }, [templates, saveTemplates, onReportDelete]);

  const handleToggleTemplate = useCallback((templateId: string) => {
    const updatedTemplates = templates.map(t => 
      t.id === templateId ? { ...t, active: !t.active } : t
    );
    setTemplates(updatedTemplates);
    saveTemplates(updatedTemplates);
  }, [templates, saveTemplates]);

  const handleRunNow = useCallback((templateId: string) => {
    const template = templates.find(t => t.id === templateId);
    if (!template) return;

    const execution: ReportExecution = {
      id: `execution_${Date.now()}`,
      templateId,
      status: 'running',
      startTime: new Date(),
      recipients: {
        email: {},
        whatsapp: {},
      },
    };

    const updatedExecutions = [...executions, execution];
    setExecutions(updatedExecutions);
    saveExecutions(updatedExecutions);

    // Simular execução (em uma implementação real, isso seria uma chamada para a API)
    setTimeout(() => {
      const completedExecution: ReportExecution = {
        ...execution,
        status: 'completed',
        endTime: new Date(),
        fileUrl: '/generated-report.pdf',
        fileSize: 1024 * 1024, // 1MB
        recipients: {
          email: template.recipients.email.reduce((acc, email) => {
            acc[email] = 'sent';
            return acc;
          }, {} as Record<string, 'sent' | 'failed'>),
          whatsapp: template.recipients.whatsapp.reduce((acc, phone) => {
            acc[phone] = 'sent';
            return acc;
          }, {} as Record<string, 'sent' | 'failed'>),
        },
      };

      const finalExecutions = executions.map(e => 
        e.id === execution.id ? completedExecution : e
      );
      setExecutions(finalExecutions);
      saveExecutions(finalExecutions);

      // Atualizar template com última execução
      const updatedTemplates = templates.map(t => 
        t.id === templateId ? { ...t, lastRun: new Date() } : t
      );
      setTemplates(updatedTemplates);
      saveTemplates(updatedTemplates);
    }, 3000);
  }, [templates, executions, saveExecutions]);

  // Handlers para execuções
  const handleDownload = useCallback((executionId: string) => {
    const execution = executions.find(e => e.id === executionId);
    if (execution?.fileUrl) {
      // Simular download
      const link = document.createElement('a');
      link.href = execution.fileUrl;
      link.download = `relatorio_${executionId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }, [executions]);

  const handleResend = useCallback((executionId: string) => {
    debugLog.info('Reenviando execução:', executionId);
    // Implementar lógica de reenvio
  }, []);

  // Renderizar templates
  const renderTemplates = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Templates de Relatórios</h3>
        <Button onClick={() => setShowCreateForm(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Novo Template
        </Button>
      </div>

      <div className="grid gap-4">
        {templates.map(template => (
          <ReportTemplateCard
            key={template.id}
            template={template}
            onEdit={setEditingTemplate}
            onDelete={handleDeleteTemplate}
            onToggle={handleToggleTemplate}
            onRunNow={handleRunNow}
          />
        ))}
      </div>
    </div>
  );

  // Renderizar execuções
  const renderExecutions = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Execuções de Relatórios</h3>
      
      <div className="grid gap-4">
        {executions.map(execution => {
          const template = templates.find(t => t.id === execution.templateId);
          return (
            <ReportExecutionCard
              key={execution.id}
              execution={execution}
              template={template}
              onDownload={handleDownload}
              onResend={handleResend}
            />
          );
        })}
      </div>
    </div>
  );

  // Renderizar configurações
  const renderSettings = () => (
    <Card>
      <CardHeader>
        <CardTitle>Configurações</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-600">
          Configurações globais do sistema de relatórios automatizados.
        </p>
      </CardContent>
    </Card>
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
      {selectedTab === 'settings' && renderSettings()}

      {/* TODO: Implementar formulário de criação/edição de templates */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Criar Novo Template</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600">
                Formulário de criação de template será implementado aqui.
              </p>
              <div className="flex justify-end gap-2 mt-4">
                <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancelar
                </Button>
                <Button onClick={() => setShowCreateForm(false)}>
                  Salvar
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

// Export para compatibilidade
export default ConsolidatedAutomatedReports;
