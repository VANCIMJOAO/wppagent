/**
 * 🚀 REPORT TEMPLATES - FASE 3 REFATORAÇÃO
 * ==========================================
 * 
 * Templates pré-configurados para relatórios automatizados.
 * Extraído do AutomatedReports para melhor organização.
 * 
 * Autor: Claude AI - Refatoração Auditoria
 * Data: 02/10/2025
 */

import { ReportTemplate } from './types';

// Templates pré-configurados
export const REPORT_TEMPLATES: Partial<ReportTemplate>[] = [
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

// Função para calcular próxima execução
export function calculateNextRun(template: ReportTemplate): Date {
  const now = new Date();
  const schedule = template.schedule;
  
  switch (template.frequency) {
    case 'daily':
      const dailyTime = new Date();
      dailyTime.setHours(parseInt(schedule.time.split(':')[0]));
      dailyTime.setMinutes(parseInt(schedule.time.split(':')[1]));
      dailyTime.setSeconds(0);
      
      if (dailyTime <= now) {
        dailyTime.setDate(dailyTime.getDate() + 1);
      }
      return dailyTime;
      
    case 'weekly':
      const weeklyTime = new Date();
      const targetDay = schedule.dayOfWeek || 1;
      const currentDay = weeklyTime.getDay();
      const daysUntilTarget = (targetDay - currentDay + 7) % 7;
      
      weeklyTime.setDate(weeklyTime.getDate() + daysUntilTarget);
      weeklyTime.setHours(parseInt(schedule.time.split(':')[0]));
      weeklyTime.setMinutes(parseInt(schedule.time.split(':')[1]));
      weeklyTime.setSeconds(0);
      
      return weeklyTime;
      
    case 'monthly':
      const monthlyTime = new Date();
      const targetDate = schedule.dayOfMonth || 1;
      
      monthlyTime.setDate(targetDate);
      monthlyTime.setHours(parseInt(schedule.time.split(':')[0]));
      monthlyTime.setMinutes(parseInt(schedule.time.split(':')[1]));
      monthlyTime.setSeconds(0);
      
      if (monthlyTime <= now) {
        monthlyTime.setMonth(monthlyTime.getMonth() + 1);
      }
      return monthlyTime;
      
    default:
      return new Date(now.getTime() + 24 * 60 * 60 * 1000); // 24 horas
  }
}
