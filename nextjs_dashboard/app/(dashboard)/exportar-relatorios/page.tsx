/**
 * Página de Exportação de Relatórios
 * Sistema completo para geração de relatórios em CSV, Excel e PDF
 */
'use client';

import React from 'react';
import { useAuth } from '@/contexts/auth-context';
import ReportExportComponent from '@/components/ReportExportComponent';
import { FileSpreadsheet, TrendingUp, Shield } from 'lucide-react';

const ExportarRelatoriosPage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Shield className="w-16 h-16 text-gray-400 mx-auto" />
          <h2 className="text-xl font-semibold text-gray-600">
            Acesso Restrito
          </h2>
          <p className="text-gray-500">
            Faça login para acessar o sistema de relatórios.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header da Página */}
      <div className="flex items-center space-x-4">
        <div className="p-2 bg-blue-100 rounded-lg">
          <FileSpreadsheet className="w-8 h-8 text-blue-600" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Sistema de Exportação de Relatórios
          </h1>
          <p className="text-gray-600 mt-1">
            Gere relatórios detalhados em CSV, Excel e PDF para análise e compliance
          </p>
        </div>
      </div>

      {/* Conteúdo Principal */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Componente Principal de Exportação */}
        <div className="lg:col-span-3">
          <ReportExportComponent />
        </div>

        {/* Sidebar com Informações e Histórico */}
        <div className="space-y-6">
          {/* Card de Status */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-green-600" />
              Status do Sistema
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Formatos Disponíveis</span>
                <span className="text-green-600 font-semibold">3</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Tipos de Relatório</span>
                <span className="text-blue-600 font-semibold">3</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Sistema</span>
                <span className="text-green-600 font-semibold">Online</span>
              </div>
            </div>
          </div>

          {/* Guia Rápido */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Guia Rápido
            </h3>
            <div className="space-y-4 text-sm">
              <div>
                <h4 className="font-semibold text-blue-600">1. Escolha o Tipo</h4>
                <p className="text-gray-600">Selecione entre Agendamentos, Conversas ou Dashboard</p>
              </div>
              <div>
                <h4 className="font-semibold text-green-600">2. Selecione o Formato</h4>
                <p className="text-gray-600">CSV para dados brutos, Excel para análise, PDF para apresentação</p>
              </div>
              <div>
                <h4 className="font-semibold text-purple-600">3. Configure Filtros</h4>
                <p className="text-gray-600">Defina período, status e outros filtros específicos</p>
              </div>
              <div>
                <h4 className="font-semibold text-orange-600">4. Exportar</h4>
                <p className="text-gray-600">Clique em Exportar e o arquivo será baixado automaticamente</p>
              </div>
            </div>
          </div>

          {/* Dicas */}
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <h4 className="font-semibold text-amber-800 mb-2">💡 Dicas</h4>
            <ul className="space-y-1 text-sm text-amber-700">
              <li>• Use Excel para relatórios com gráficos</li>
              <li>• PDF é ideal para apresentações</li>
              <li>• CSV é perfeito para análise externa</li>
              <li>• Filtre por período para relatórios específicos</li>
            </ul>
          </div>

          {/* Formatos Detalhados */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Características dos Formatos
            </h3>
            <div className="space-y-4 text-sm">
              <div className="border-l-4 border-gray-400 pl-3">
                <h4 className="font-semibold text-gray-700">CSV</h4>
                <p className="text-gray-600">Arquivo leve, compatível com Excel, ideal para análise de dados</p>
              </div>
              <div className="border-l-4 border-green-400 pl-3">
                <h4 className="font-semibold text-green-700">Excel</h4>
                <p className="text-gray-600">Formatação avançada, múltiplas abas, gráficos automáticos</p>
              </div>
              <div className="border-l-4 border-red-400 pl-3">
                <h4 className="font-semibold text-red-700">PDF</h4>
                <p className="text-gray-600">Layout profissional, ideal para impressão e apresentação</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportarRelatoriosPage;
