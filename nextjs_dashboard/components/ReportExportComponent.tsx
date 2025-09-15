/**
 * Componente de Exportação de Relatórios
 * Sistema avançado para gerar CSV, Excel e PDF
 */
'use client';

import React, { useState, useCallback } from 'react';
import {
  FileSpreadsheet,
  FileText,
  Download,
  Calendar,
  Filter,
  Users,
  CheckCircle,
  AlertCircle,
  Settings
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface ReportFilters {
  dateFrom?: string;
  dateTo?: string;
  status?: string;
  userId?: number;
}

interface ExportConfig {
  reportType: 'appointments' | 'conversations' | 'dashboard';
  format: 'csv' | 'excel' | 'pdf';
  filters: ReportFilters;
}

const ReportExportComponent: React.FC = () => {
  const [config, setConfig] = useState<ExportConfig>({
    reportType: 'appointments',
    format: 'excel',
    filters: {}
  });

  const [isExporting, setIsExporting] = useState(false);
  const [lastExport, setLastExport] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Tradução dos tipos de relatórios
  const reportTypes = {
    appointments: {
      name: 'Agendamentos',
      description: 'Relatório completo de agendamentos com status e métricas',
      icon: Calendar,
      color: 'text-blue-600'
    },
    conversations: {
      name: 'Conversas',
      description: 'Histórico e análise de conversas com clientes',
      icon: Users,
      color: 'text-green-600'
    },
    dashboard: {
      name: 'Dashboard Executivo',
      description: 'Métricas gerais e indicadores de performance',
      icon: Settings,
      color: 'text-purple-600'
    }
  };

  // Tradução dos formatos
  const formats = {
    csv: {
      name: 'CSV',
      description: 'Planilha simples compatível com Excel',
      icon: FileText,
      color: 'text-gray-600',
      features: ['Dados brutos', 'Compatível Excel', 'Arquivo leve']
    },
    excel: {
      name: 'Excel',
      description: 'Planilha formatada com gráficos e resumo',
      icon: FileSpreadsheet,
      color: 'text-green-600',
      features: ['Formatação avançada', 'Múltiplas abas', 'Gráficos', 'Resumo executivo']
    },
    pdf: {
      name: 'PDF',
      description: 'Documento profissional para impressão',
      icon: FileText,
      color: 'text-red-600',
      features: ['Layout profissional', 'Tabelas formatadas', 'Para impressão']
    }
  };

  // Status para filtros de agendamentos
  const appointmentStatuses = [
    { value: '', label: 'Todos os status' },
    { value: 'pending', label: 'Pendente' },
    { value: 'confirmed', label: 'Confirmado' },
    { value: 'completed', label: 'Concluído' },
    { value: 'cancelled', label: 'Cancelado' }
  ];

  const handleExport = useCallback(async () => {
    setIsExporting(true);
    setError(null);

    try {
      // Construir URL com parâmetros
      const baseUrl = `/api/reports/${config.reportType}/export`;
      const params = new URLSearchParams({
        format: config.format
      });

      // Adicionar filtros
      if (config.filters.dateFrom) {
        params.append('date_from', config.filters.dateFrom);
      }
      if (config.filters.dateTo) {
        params.append('date_to', config.filters.dateTo);
      }
      if (config.filters.status) {
        params.append('status', config.filters.status);
      }
      if (config.filters.userId) {
        params.append('user_id', config.filters.userId.toString());
      }

      const url = `${baseUrl}?${params.toString()}`;

      // Fazer request
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }

      // Obter o blob do arquivo
      const blob = await response.blob();

      // Extrair nome do arquivo do header Content-Disposition
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `relatorio_${config.reportType}_${format(new Date(), 'yyyyMMdd_HHmmss')}.${config.format === 'excel' ? 'xlsx' : config.format}`;

      if (contentDisposition) {
        const matches = contentDisposition.match(/filename="?(.+)"?/);
        if (matches) {
          filename = matches[1];
        }
      }

      // Criar link de download
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      // Atualizar estado de sucesso
      setLastExport(format(new Date(), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR }));

    } catch (err) {
      console.error('Erro na exportação:', err);
      setError(err instanceof Error ? err.message : 'Erro desconhecido ao exportar relatório');
    } finally {
      setIsExporting(false);
    }
  }, [config]);

  const updateFilters = useCallback((newFilters: Partial<ReportFilters>) => {
    setConfig(prev => ({
      ...prev,
      filters: { ...prev.filters, ...newFilters }
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setConfig(prev => ({
      ...prev,
      filters: {}
    }));
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">
          Exportação de Relatórios
        </h2>
        {lastExport && (
          <div className="flex items-center text-sm text-green-600">
            <CheckCircle className="w-4 h-4 mr-1" />
            Último: {lastExport}
          </div>
        )}
      </div>

      {/* Seleção do Tipo de Relatório */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-700">Tipo de Relatório</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(reportTypes).map(([key, type]) => {
            const IconComponent = type.icon;
            return (
              <div
                key={key}
                onClick={() => setConfig(prev => ({ ...prev, reportType: key as any }))}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  config.reportType === key
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <IconComponent className={`w-6 h-6 ${type.color}`} />
                  <div>
                    <h4 className="font-semibold text-gray-900">{type.name}</h4>
                    <p className="text-sm text-gray-600">{type.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Seleção do Formato */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-700">Formato de Exportação</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(formats).map(([key, format]) => {
            const IconComponent = format.icon;
            return (
              <div
                key={key}
                onClick={() => setConfig(prev => ({ ...prev, format: key as any }))}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  config.format === key
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <IconComponent className={`w-6 h-6 ${format.color}`} />
                    <div>
                      <h4 className="font-semibold text-gray-900">{format.name}</h4>
                      <p className="text-sm text-gray-600">{format.description}</p>
                    </div>
                  </div>
                  <div className="space-y-1">
                    {format.features.map((feature, index) => (
                      <span key={index} className="inline-block bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded mr-1">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Filtros */}
      <div className="space-y-4 border-t pt-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-700 flex items-center">
            <Filter className="w-5 h-5 mr-2" />
            Filtros
          </h3>
          <button
            onClick={clearFilters}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Limpar filtros
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Data Inicial */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Inicial
            </label>
            <input
              type="date"
              value={config.filters.dateFrom || ''}
              onChange={(e) => updateFilters({ dateFrom: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Data Final */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Data Final
            </label>
            <input
              type="date"
              value={config.filters.dateTo || ''}
              onChange={(e) => updateFilters({ dateTo: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Status (apenas para agendamentos) */}
          {config.reportType === 'appointments' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={config.filters.status || ''}
                onChange={(e) => updateFilters({ status: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {appointmentStatuses.map(status => (
                  <option key={status.value} value={status.value}>
                    {status.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* ID do Usuário */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ID do Usuário
            </label>
            <input
              type="number"
              placeholder="Filtrar por usuário específico"
              value={config.filters.userId || ''}
              onChange={(e) => updateFilters({
                userId: e.target.value ? parseInt(e.target.value) : undefined
              })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Erro */}
      {error && (
        <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Botão de Exportação */}
      <div className="flex justify-center pt-6">
        <button
          onClick={handleExport}
          disabled={isExporting}
          className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-semibold transition-all ${
            isExporting
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 focus:ring-4 focus:ring-blue-300'
          } text-white`}
        >
          <Download className={`w-5 h-5 ${isExporting ? 'animate-bounce' : ''}`} />
          <span>
            {isExporting ? 'Gerando Relatório...' : 'Exportar Relatório'}
          </span>
        </button>
      </div>

      {/* Informações Adicionais */}
      <div className="bg-gray-50 rounded-lg p-4 space-y-2">
        <h4 className="font-semibold text-gray-700">Informações do Relatório</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
          <div>
            <strong>Tipo:</strong> {reportTypes[config.reportType].name}
          </div>
          <div>
            <strong>Formato:</strong> {formats[config.format].name}
          </div>
          <div>
            <strong>Filtros ativos:</strong> {Object.values(config.filters).filter(Boolean).length || 'Nenhum'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportExportComponent;
