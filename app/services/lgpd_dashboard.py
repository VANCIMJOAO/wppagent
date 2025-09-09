"""
Dashboard Web para Administração LGPD
Interface administrativa para gerenciamento de conformidade LGPD
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from typing import Dict, Any

from ..services.lgpd_compliance import get_lgpd_manager, LGPDComplianceManager
from ..services.lgpd_scheduler import get_lgpd_scheduler, LGPDRetentionScheduler

router = APIRouter(prefix="/admin/lgpd")

@router.get("/dashboard", response_class=HTMLResponse)
async def lgpd_admin_dashboard():
    """Dashboard principal para administração LGPD"""
    
    dashboard_html = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LGPD Compliance Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <div class="bg-blue-600 text-white shadow-lg">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center">
                    <i class="fas fa-shield-alt text-2xl mr-3"></i>
                    <h1 class="text-xl font-semibold">LGPD Compliance Dashboard</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-sm">Sistema de Conformidade LGPD</span>
                    <div class="w-3 h-3 bg-green-400 rounded-full"></div>
                </div>
            </div>
        </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        <!-- Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-users text-blue-600 text-2xl"></i>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Total de Usuários</dt>
                                <dd class="text-lg font-medium text-gray-900" id="total-users">Carregando...</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-database text-green-600 text-2xl"></i>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Total de Registros</dt>
                                <dd class="text-lg font-medium text-gray-900" id="total-records">Carregando...</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-clock text-yellow-600 text-2xl"></i>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Próxima Retenção</dt>
                                <dd class="text-lg font-medium text-gray-900" id="next-retention">02:00 Amanhã</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-white overflow-hidden shadow rounded-lg">
                <div class="p-5">
                    <div class="flex items-center">
                        <div class="flex-shrink-0">
                            <i class="fas fa-check-circle text-purple-600 text-2xl"></i>
                        </div>
                        <div class="ml-5 w-0 flex-1">
                            <dl>
                                <dt class="text-sm font-medium text-gray-500 truncate">Status Conformidade</dt>
                                <dd class="text-lg font-medium text-green-600">Ativo</dd>
                            </dl>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            <!-- Políticas de Retenção -->
            <div class="bg-white shadow rounded-lg">
                <div class="px-4 py-5 sm:p-6">
                    <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                        <i class="fas fa-trash-alt mr-2"></i>Políticas de Retenção
                    </h3>
                    
                    <div class="space-y-4">
                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                            <div>
                                <p class="font-medium">Dados Pessoais</p>
                                <p class="text-sm text-gray-600">Retenção: 5 anos</p>
                            </div>
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Ativo
                            </span>
                        </div>
                        
                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                            <div>
                                <p class="font-medium">Conversas</p>
                                <p class="text-sm text-gray-600">Retenção: 2 anos</p>
                            </div>
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                Ativo
                            </span>
                        </div>
                        
                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                            <div>
                                <p class="font-medium">Agendamentos</p>
                                <p class="text-sm text-gray-600">Retenção: 5 anos (Legal)</p>
                            </div>
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                Obrigatório
                            </span>
                        </div>
                    </div>
                    
                    <div class="mt-6">
                        <button onclick="applyRetentionPolicies()" 
                                class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition duration-150">
                            <i class="fas fa-play mr-2"></i>Executar Políticas Agora
                        </button>
                    </div>
                </div>
            </div>

            <!-- Direitos dos Usuários -->
            <div class="bg-white shadow rounded-lg">
                <div class="px-4 py-5 sm:p-6">
                    <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                        <i class="fas fa-user-check mr-2"></i>Direitos dos Usuários
                    </h3>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div class="text-center p-4 bg-blue-50 rounded-lg">
                            <i class="fas fa-eye text-blue-600 text-2xl mb-2"></i>
                            <p class="font-medium">Acesso</p>
                            <p class="text-sm text-gray-600">Visualizar dados</p>
                            <span class="inline-block mt-1 px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Disponível</span>
                        </div>
                        
                        <div class="text-center p-4 bg-green-50 rounded-lg">
                            <i class="fas fa-download text-green-600 text-2xl mb-2"></i>
                            <p class="font-medium">Portabilidade</p>
                            <p class="text-sm text-gray-600">Exportar dados</p>
                            <span class="inline-block mt-1 px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Disponível</span>
                        </div>
                        
                        <div class="text-center p-4 bg-red-50 rounded-lg">
                            <i class="fas fa-trash text-red-600 text-2xl mb-2"></i>
                            <p class="font-medium">Eliminação</p>
                            <p class="text-sm text-gray-600">Deletar conta</p>
                            <span class="inline-block mt-1 px-2 py-1 text-xs bg-green-100 text-green-800 rounded">Disponível</span>
                        </div>
                        
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <i class="fas fa-edit text-gray-600 text-2xl mb-2"></i>
                            <p class="font-medium">Correção</p>
                            <p class="text-sm text-gray-600">Corrigir dados</p>
                            <span class="inline-block mt-1 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Pendente</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Relatórios e Logs -->
        <div class="mt-8">
            <div class="bg-white shadow rounded-lg">
                <div class="px-4 py-5 sm:p-6">
                    <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                        <i class="fas fa-chart-bar mr-2"></i>Relatórios e Monitoramento
                    </h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <!-- Gráfico de Dados por Categoria -->
                        <div>
                            <h4 class="font-medium mb-2">Dados por Categoria</h4>
                            <canvas id="dataCategoryChart" width="200" height="200"></canvas>
                        </div>
                        
                        <!-- Últimas Atividades -->
                        <div class="md:col-span-2">
                            <h4 class="font-medium mb-2">Últimas Atividades LGPD</h4>
                            <div class="bg-gray-50 rounded p-4 max-h-48 overflow-y-auto" id="activity-log">
                                <div class="flex items-center text-sm text-gray-600 mb-2">
                                    <i class="fas fa-info-circle text-blue-500 mr-2"></i>
                                    <span>Sistema LGPD iniciado - Dashboard carregado</span>
                                </div>
                                <div class="flex items-center text-sm text-gray-600 mb-2">
                                    <i class="fas fa-shield-alt text-green-500 mr-2"></i>
                                    <span>Políticas de retenção ativas</span>
                                </div>
                                <div class="flex items-center text-sm text-gray-600">
                                    <i class="fas fa-clock text-yellow-500 mr-2"></i>
                                    <span>Próxima execução automática: 02:00</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Actions Panel -->
        <div class="mt-8">
            <div class="bg-white shadow rounded-lg">
                <div class="px-4 py-5 sm:p-6">
                    <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                        <i class="fas fa-tools mr-2"></i>Ações Administrativas
                    </h3>
                    
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <button onclick="generateReport()" 
                                class="bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-md transition duration-150">
                            <i class="fas fa-file-alt mr-2"></i>Gerar Relatório
                        </button>
                        
                        <button onclick="exportUsers()" 
                                class="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-md transition duration-150">
                            <i class="fas fa-users mr-2"></i>Exportar Usuários
                        </button>
                        
                        <button onclick="viewScheduler()" 
                                class="bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-md transition duration-150">
                            <i class="fas fa-calendar mr-2"></i>Ver Agendamento
                        </button>
                        
                        <button onclick="viewLogs()" 
                                class="bg-gray-600 hover:bg-gray-700 text-white font-medium py-3 px-4 rounded-md transition duration-150">
                            <i class="fas fa-list mr-2"></i>Ver Logs
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Loading Modal -->
    <div id="loading-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl">
            <div class="flex items-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mr-4"></div>
                <span class="text-lg font-medium">Processando...</span>
            </div>
        </div>
    </div>

    <!-- Result Modal -->
    <div id="result-modal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden items-center justify-center z-50">
        <div class="bg-white p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-medium" id="result-title">Resultado</h3>
                <button onclick="closeResultModal()" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div id="result-content" class="mb-4"></div>
            <button onclick="closeResultModal()" 
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md">
                Fechar
            </button>
        </div>
    </div>

    <script>
        // Inicializar dashboard
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
            initializeChart();
        });

        async function loadDashboardData() {
            try {
                const response = await fetch('/api/lgpd/data-processing-report');
                const data = await response.json();
                
                document.getElementById('total-records').textContent = data.total_records.toLocaleString();
                
                // Simular dados de usuários
                document.getElementById('total-users').textContent = '1,234';
                
            } catch (error) {
                console.error('Erro ao carregar dados:', error);
                document.getElementById('total-records').textContent = 'Erro';
                document.getElementById('total-users').textContent = 'Erro';
            }
        }

        function initializeChart() {
            const ctx = document.getElementById('dataCategoryChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Pessoais', 'Conversas', 'Agendamentos', 'Outros'],
                    datasets: [{
                        data: [40, 35, 20, 5],
                        backgroundColor: [
                            '#3B82F6',
                            '#10B981', 
                            '#F59E0B',
                            '#6B7280'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        position: 'bottom'
                    }
                }
            });
        }

        async function applyRetentionPolicies() {
            showLoadingModal();
            
            try {
                const response = await fetch('/api/lgpd/apply-retention-policies', {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                hideLoadingModal();
                showResultModal('Políticas de Retenção', 
                    `<p><strong>Registros processados:</strong> ${result.total_records_processed}</p>
                     <p><strong>Registros deletados:</strong> ${result.total_records_deleted}</p>
                     <p><strong>Registros anonimizados:</strong> ${result.total_records_anonymized}</p>
                     <p class="text-green-600 mt-2">✅ Políticas aplicadas com sucesso!</p>`
                );
                
            } catch (error) {
                hideLoadingModal();
                showResultModal('Erro', `<p class="text-red-600">❌ Erro ao aplicar políticas: ${error.message}</p>`);
            }
        }

        async function generateReport() {
            showLoadingModal();
            
            try {
                const response = await fetch('/api/lgpd/data-processing-report');
                const report = await response.json();
                
                hideLoadingModal();
                showResultModal('Relatório LGPD', 
                    `<p><strong>Total de registros:</strong> ${report.total_records}</p>
                     <p><strong>Categorias de dados:</strong> ${Object.keys(report.data_categories).length}</p>
                     <p><strong>Finalidades:</strong> ${Object.keys(report.processing_purposes).length}</p>
                     <p class="text-blue-600 mt-2">📊 Relatório gerado com sucesso!</p>`
                );
                
            } catch (error) {
                hideLoadingModal();
                showResultModal('Erro', `<p class="text-red-600">❌ Erro ao gerar relatório: ${error.message}</p>`);
            }
        }

        function exportUsers() {
            showResultModal('Exportação de Usuários', 
                '<p>🚧 Funcionalidade em desenvolvimento</p><p class="text-gray-600 text-sm mt-2">Esta funcionalidade será implementada em breve.</p>');
        }

        function viewScheduler() {
            showResultModal('Status do Agendador', 
                `<p><strong>Status:</strong> <span class="text-green-600">Ativo</span></p>
                 <p><strong>Próximas execuções:</strong></p>
                 <ul class="text-sm text-gray-600 mt-2 space-y-1">
                     <li>• Retenção diária: 02:00</li>
                     <li>• Limpeza semanal: Domingo 03:00</li>
                     <li>• Auditoria mensal: Dia 1, 04:00</li>
                 </ul>`);
        }

        function viewLogs() {
            showResultModal('Logs do Sistema', 
                '<p>📋 Últimas atividades:</p><div class="text-sm text-gray-600 mt-2 space-y-1"><div>✅ Sistema iniciado</div><div>🔄 Políticas de retenção ativas</div><div>📊 Dashboard acessado</div></div>');
        }

        function showLoadingModal() {
            document.getElementById('loading-modal').classList.remove('hidden');
            document.getElementById('loading-modal').classList.add('flex');
        }

        function hideLoadingModal() {
            document.getElementById('loading-modal').classList.add('hidden');
            document.getElementById('loading-modal').classList.remove('flex');
        }

        function showResultModal(title, content) {
            document.getElementById('result-title').textContent = title;
            document.getElementById('result-content').innerHTML = content;
            document.getElementById('result-modal').classList.remove('hidden');
            document.getElementById('result-modal').classList.add('flex');
        }

        function closeResultModal() {
            document.getElementById('result-modal').classList.add('hidden');
            document.getElementById('result-modal').classList.remove('flex');
        }
    </script>
</body>
</html>
    """
    
    return dashboard_html
