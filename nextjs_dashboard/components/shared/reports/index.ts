/**
 * 🚀 REPORTS MODULE - FASE 3 REFATORAÇÃO
 * ========================================
 * 
 * Barrel file para exportar todos os componentes do sistema de relatórios refatorado.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

export { ReportTemplateCard } from './report-template-card';
export { ReportExecutionCard } from './report-execution-card';
export { REPORT_TEMPLATES, calculateNextRun } from './report-templates';
export type { 
  ReportTemplate, 
  ReportSection, 
  ReportExecution, 
  ReportFormData,
  ReportTemplateCardProps,
  ReportExecutionCardProps,
  ReportFormProps
} from './types';
