/**
 * Componente de Filtros Analytics
 * Seletores de período, canais e outros filtros para dashboard
 */
'use client';

import React, { useState } from 'react';
import { Calendar, Filter, Download, RefreshCw } from 'lucide-react';
import { format, subDays, startOfDay, endOfDay } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { AnalyticsFilters, AnalyticsTimeRange } from '../../hooks/useAnalytics';

interface AnalyticsFiltersComponentProps {
  filters: AnalyticsFilters;
  onFiltersChange: (filters: AnalyticsFilters) => void;
  onRefresh: () => void;
  onExport: (format: 'csv' | 'excel' | 'pdf') => void;
  loading?: boolean;
  exporting?: boolean;
  availableChannels?: string[];
  availableAgents?: string[];
  lastUpdate?: Date | null;
}

// Presets de período
const TIME_PRESETS = [
  { key: 'today', label: 'Hoje', days: 0 },
  { key: '7d', label: 'Últimos 7 dias', days: 7 },
  { key: '30d', label: 'Últimos 30 dias', days: 30 },
  { key: '90d', label: 'Últimos 90 dias', days: 90 },
  { key: 'custom', label: 'Personalizado', days: null },
] as const;

const AnalyticsFiltersComponent: React.FC<AnalyticsFiltersComponentProps> = ({
  filters,
  onFiltersChange,
  onRefresh,
  onExport,
  loading = false,
  exporting = false,
  availableChannels = ['whatsapp', 'telegram', 'website'],
  availableAgents = [],
  lastUpdate,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<string>(
    filters.timeRange?.preset || '30d'
  );

  // Estado local para datas customizadas
  const [customStartDate, setCustomStartDate] = useState(
    filters.timeRange?.startDate || subDays(new Date(), 30)
  );
  const [customEndDate, setCustomEndDate] = useState(
    filters.timeRange?.endDate || new Date()
  );

  // Aplicar preset de tempo
  const handlePresetChange = (preset: string) => {
    setSelectedPreset(preset);

    if (preset === 'custom') return;

    const presetData = TIME_PRESETS.find(p => p.key === preset);
    if (!presetData) return;

    let timeRange: AnalyticsTimeRange;

    if (presetData.days === 0) {
      // Hoje
      timeRange = {
        startDate: startOfDay(new Date()),
        endDate: endOfDay(new Date()),
        preset: preset as any,
      };
    } else if (presetData.days !== null) {
      // Últimos N dias
      timeRange = {
        startDate: subDays(new Date(), presetData.days),
        endDate: new Date(),
        preset: preset as any,
      };
    } else {
      // Fallback para custom
      return;
    }

    onFiltersChange({
      ...filters,
      timeRange,
    });
  };

  // Aplicar datas customizadas
  const handleCustomDateChange = () => {
    onFiltersChange({
      ...filters,
      timeRange: {
        startDate: customStartDate,
        endDate: customEndDate,
        preset: 'custom',
      },
    });
  };

  // Alterar canais selecionados
  const handleChannelChange = (channel: string, checked: boolean) => {
    const currentChannels = filters.channels || [];
    let newChannels: string[];

    if (checked) {
      newChannels = [...currentChannels, channel];
    } else {
      newChannels = currentChannels.filter(c => c !== channel);
    }

    onFiltersChange({
      ...filters,
      channels: newChannels,
    });
  };

  // Alterar agentes selecionados
  const handleAgentChange = (agent: string, checked: boolean) => {
    const currentAgents = filters.agents || [];
    let newAgents: string[];

    if (checked) {
      newAgents = [...currentAgents, agent];
    } else {
      newAgents = currentAgents.filter(a => a !== agent);
    }

    onFiltersChange({
      ...filters,
      agents: newAgents,
    });
  };

  // Limpar filtros
  const handleClearFilters = () => {
    onFiltersChange({
      timeRange: {
        startDate: subDays(new Date(), 30),
        endDate: new Date(),
        preset: '30d',
      },
    });
    setSelectedPreset('30d');
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
      {/* Header dos filtros */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <Filter className="w-5 h-5 mr-2 text-blue-500" />
            Filtros
          </h3>

          {lastUpdate && (
            <span className="text-sm text-gray-500">
              Atualizado em {format(lastUpdate, 'HH:mm:ss')}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {/* Botão de refresh */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Atualizar
          </button>

          {/* Botões de export */}
          <div className="relative inline-block text-left">
            <button
              disabled={exporting}
              className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
            >
              <Download className="w-4 h-4 mr-2" />
              {exporting ? 'Exportando...' : 'Exportar'}
            </button>

            <div className="absolute right-0 mt-1 w-32 bg-white border border-gray-200 rounded-md shadow-lg z-10 hidden group-hover:block">
              <button
                onClick={() => onExport('csv')}
                className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left"
              >
                CSV
              </button>
              <button
                onClick={() => onExport('excel')}
                className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left"
              >
                Excel
              </button>
              <button
                onClick={() => onExport('pdf')}
                className="block w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left"
              >
                PDF
              </button>
            </div>
          </div>

          {/* Toggle filtros avançados */}
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showAdvanced ? 'Ocultar' : 'Mais filtros'}
          </button>
        </div>
      </div>

      {/* Filtro de período */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          <Calendar className="w-4 h-4 inline mr-1" />
          Período
        </label>

        <div className="flex flex-wrap gap-2 mb-4">
          {TIME_PRESETS.map((preset) => (
            <button
              key={preset.key}
              onClick={() => handlePresetChange(preset.key)}
              className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                selectedPreset === preset.key
                  ? 'bg-blue-100 border-blue-500 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>

        {/* Datas customizadas */}
        {selectedPreset === 'custom' && (
          <div className="flex space-x-4">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Data inicial
              </label>
              <input
                type="date"
                value={format(customStartDate, 'yyyy-MM-dd')}
                onChange={(e) => setCustomStartDate(new Date(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>

            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Data final
              </label>
              <input
                type="date"
                value={format(customEndDate, 'yyyy-MM-dd')}
                onChange={(e) => setCustomEndDate(new Date(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>

            <div className="flex items-end">
              <button
                onClick={handleCustomDateChange}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
              >
                Aplicar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Filtros avançados */}
      {showAdvanced && (
        <div className="pt-4 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Filtro de canais */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Canais
              </label>
              <div className="space-y-2">
                {availableChannels.map((channel) => (
                  <label key={channel} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={filters.channels?.includes(channel) || false}
                      onChange={(e) => handleChannelChange(channel, e.target.checked)}
                      className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <span className="text-sm text-gray-700 capitalize">
                      {channel}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Filtro de agentes */}
            {availableAgents.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Agentes
                </label>
                <div className="space-y-2 max-h-32 overflow-y-auto">
                  {availableAgents.map((agent) => (
                    <label key={agent} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={filters.agents?.includes(agent) || false}
                        onChange={(e) => handleAgentChange(agent, e.target.checked)}
                        className="mr-2 h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                      <span className="text-sm text-gray-700">
                        {agent}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Botão de limpar filtros */}
          <div className="mt-4 pt-4 border-t border-gray-100">
            <button
              onClick={handleClearFilters}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Limpar todos os filtros
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsFiltersComponent;
