/**
 * 🚀 REPORTS TYPES - FASE 3 REFATORAÇÃO
 * ======================================
 * 
 * Tipos para o sistema de relatórios automatizados refatorado.
 * Extraído do AutomatedReports para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

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
  type: 'metric_summary' | 'chart' | 'table' | 'text';
  config: Record<string, any>;
  order: number;
}

export interface ReportExecution {
  id: string;
  templateId: string;
  status: 'running' | 'completed' | 'failed';
  startTime: Date;
  endTime?: Date;
  fileUrl?: string;
  fileSize?: number;
  recipients: {
    email: Record<string, 'sent' | 'failed'>;
    whatsapp: Record<string, 'sent' | 'failed'>;
  };
}

export interface ReportFormData {
  name: string;
  description: string;
  type: ReportTemplate['type'];
  frequency: ReportTemplate['frequency'];
  schedule: ReportTemplate['schedule'];
  recipients: ReportTemplate['recipients'];
  format: ReportTemplate['format'];
  sections: ReportSection[];
  filters: Record<string, any>;
}

export interface ReportTemplateCardProps {
  template: ReportTemplate;
  onEdit: (template: ReportTemplate) => void;
  onDelete: (templateId: string) => void;
  onToggle: (templateId: string) => void;
  onRunNow: (templateId: string) => void;
}

export interface ReportExecutionCardProps {
  execution: ReportExecution;
  template: ReportTemplate | undefined;
  onDownload: (executionId: string) => void;
  onResend: (executionId: string) => void;
}

export interface ReportFormProps {
  template?: ReportTemplate | null;
  onSave: (data: ReportFormData) => void;
  onCancel: () => void;
  isLoading?: boolean;
}
