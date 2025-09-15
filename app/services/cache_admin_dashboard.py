"""
Interface Web para Cache Invalidation Manual
Dashboard administrativo para gerenciamento de cache
"""

import json
from typing import Dict

from fastapi import Request
from fastapi.responses import HTMLResponse


def generate_cache_admin_dashboard() -> str:
    """Gera HTML do dashboard administrativo"""
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cache Invalidation Manager</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .loading { animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="container mx-auto px-4 py-4">
            <div class="flex justify-between items-center">
                <h1 class="text-2xl font-bold text-gray-900">
                    🗂️ Cache Invalidation Manager
                </h1>
                <div class="flex gap-4">
                    <button onclick="loadStats()" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                        🔄 Atualizar Stats
                    </button>
                    <div id="connectionStatus" class="px-3 py-2 rounded text-sm bg-green-100 text-green-800">
                        🟢 Conectado
                    </div>
                </div>
            </div>
        </div>
    </header>

    <div class="container mx-auto px-4 py-6">
        <!-- Statistics Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div class="bg-white p-6 rounded-lg shadow-sm">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">Total Keys</p>
                        <p id="totalKeys" class="text-2xl font-bold text-gray-900">-</p>
                    </div>
                    <div class="bg-blue-100 p-3 rounded-full">
                        🔑
                    </div>
                </div>
            </div>

            <div class="bg-white p-6 rounded-lg shadow-sm">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">Memory Usage</p>
                        <p id="memoryUsage" class="text-2xl font-bold text-gray-900">-</p>
                    </div>
                    <div class="bg-yellow-100 p-3 rounded-full">
                        💾
                    </div>
                </div>
            </div>

            <div class="bg-white p-6 rounded-lg shadow-sm">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">Hit Rate</p>
                        <p id="hitRate" class="text-2xl font-bold text-gray-900">-</p>
                    </div>
                    <div class="bg-green-100 p-3 rounded-full">
                        🎯
                    </div>
                </div>
            </div>

            <div class="bg-white p-6 rounded-lg shadow-sm">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm text-gray-600">Invalidations</p>
                        <p id="invalidationCount" class="text-2xl font-bold text-gray-900">-</p>
                    </div>
                    <div class="bg-red-100 p-3 rounded-full">
                        🗑️
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Manual Invalidation Panel -->
            <div class="bg-white rounded-lg shadow-sm p-6">
                <h2 class="text-xl font-semibold mb-4 text-gray-900">🚀 Invalidação Manual</h2>

                <div class="space-y-4">
                    <!-- Tabs -->
                    <div class="border-b border-gray-200">
                        <nav class="-mb-px flex space-x-8">
                            <button onclick="setInvalidationTab('keys')" id="keysTab" class="py-2 px-1 border-b-2 border-blue-500 text-blue-600 font-medium text-sm">
                                Chaves Específicas
                            </button>
                            <button onclick="setInvalidationTab('patterns')" id="patternsTab" class="py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm">
                                Padrões
                            </button>
                            <button onclick="setInvalidationTab('scopes')" id="scopesTab" class="py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm">
                                Escopos
                            </button>
                        </nav>
                    </div>

                    <!-- Keys Tab -->
                    <div id="keysPanel" class="space-y-3">
                        <label class="block text-sm font-medium text-gray-700">
                            Chaves (uma por linha):
                        </label>
                        <textarea id="keysInput" rows="4" class="w-full border border-gray-300 rounded-md px-3 py-2"
                                  placeholder="customer:123&#10;analytics:dashboard:summary&#10;conversation:456"></textarea>
                    </div>

                    <!-- Patterns Tab -->
                    <div id="patternsPanel" class="space-y-3 hidden">
                        <label class="block text-sm font-medium text-gray-700">
                            Padrões (uma por linha):
                        </label>
                        <textarea id="patternsInput" rows="4" class="w-full border border-gray-300 rounded-md px-3 py-2"
                                  placeholder="analytics:*&#10;customer:*&#10;conversation:*"></textarea>
                    </div>

                    <!-- Scopes Tab -->
                    <div id="scopesPanel" class="space-y-3 hidden">
                        <label class="block text-sm font-medium text-gray-700">
                            Escopos:
                        </label>
                        <div class="grid grid-cols-2 gap-2">
                            <label class="flex items-center">
                                <input type="checkbox" value="analytics" class="scope-checkbox mr-2"> Analytics
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" value="customers" class="scope-checkbox mr-2"> Customers
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" value="conversations" class="scope-checkbox mr-2"> Conversations
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" value="appointments" class="scope-checkbox mr-2"> Appointments
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" value="templates" class="scope-checkbox mr-2"> Templates
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" value="reports" class="scope-checkbox mr-2"> Reports
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" value="dashboard" class="scope-checkbox mr-2"> Dashboard
                            </label>
                            <label class="flex items-center">
                                <input type="checkbox" value="all" class="scope-checkbox mr-2"> <strong>ALL</strong>
                            </label>
                        </div>
                    </div>

                    <!-- Options -->
                    <div class="space-y-2">
                        <label class="flex items-center">
                            <input type="checkbox" id="cascadeOption" class="mr-2"> Invalidação em Cascata
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" id="dryRunOption" class="mr-2"> Dry Run (simular apenas)
                        </label>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                Motivo:
                            </label>
                            <input type="text" id="reasonInput" class="w-full border border-gray-300 rounded-md px-3 py-2"
                                   placeholder="Motivo da invalidação" value="Manual invalidation via dashboard">
                        </div>
                    </div>

                    <!-- Execute Button -->
                    <button onclick="executeInvalidation()" id="executeBtn"
                            class="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
                        🗑️ Executar Invalidação
                    </button>
                </div>
            </div>

            <!-- Cache Keys Browser -->
            <div class="bg-white rounded-lg shadow-sm p-6">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-semibold text-gray-900">🔍 Explorador de Chaves</h2>
                    <button onclick="loadKeys()" class="text-blue-600 hover:text-blue-800">
                        🔄 Atualizar
                    </button>
                </div>

                <!-- Search -->
                <div class="mb-4">
                    <input type="text" id="keysSearch" class="w-full border border-gray-300 rounded-md px-3 py-2"
                           placeholder="Buscar por padrão (ex: analytics:*)" onkeyup="searchKeys()">
                </div>

                <!-- Keys List -->
                <div id="keysList" class="space-y-2 max-h-96 overflow-y-auto">
                    <div class="text-center py-4 text-gray-500">
                        Carregando chaves...
                    </div>
                </div>
            </div>
        </div>

        <!-- Invalidation History -->
        <div class="mt-6 bg-white rounded-lg shadow-sm p-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold text-gray-900">📜 Histórico de Invalidações</h2>
                <button onclick="loadHistory()" class="text-blue-600 hover:text-blue-800">
                    🔄 Atualizar
                </button>
            </div>

            <div id="historyList" class="space-y-3">
                <div class="text-center py-4 text-gray-500">
                    Carregando histórico...
                </div>
            </div>
        </div>

        <!-- Results Modal -->
        <div id="resultsModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden">
            <div class="flex items-center justify-center min-h-screen p-4">
                <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-96 overflow-y-auto">
                    <div class="p-6">
                        <div class="flex justify-between items-center mb-4">
                            <h3 class="text-lg font-semibold" id="resultsTitle">Resultado</h3>
                            <button onclick="closeResultsModal()" class="text-gray-500 hover:text-gray-700">
                                ✕
                            </button>
                        </div>
                        <div id="resultsContent"></div>
                        <div class="mt-4 flex justify-end">
                            <button onclick="closeResultsModal()" class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">
                                Fechar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentTab = 'keys';

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
            loadKeys();
            loadHistory();
        });

        function setInvalidationTab(tab) {
            currentTab = tab;

            // Hide all panels
            document.getElementById('keysPanel').classList.add('hidden');
            document.getElementById('patternsPanel').classList.add('hidden');
            document.getElementById('scopesPanel').classList.add('hidden');

            // Reset tab styles
            document.getElementById('keysTab').className = 'py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm';
            document.getElementById('patternsTab').className = 'py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm';
            document.getElementById('scopesTab').className = 'py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm';

            // Show active panel and tab
            document.getElementById(tab + 'Panel').classList.remove('hidden');
            document.getElementById(tab + 'Tab').className = 'py-2 px-1 border-b-2 border-blue-500 text-blue-600 font-medium text-sm';
        }

        async function loadStats() {
            try {
                const response = await fetch('/api/cache/statistics');
                const result = await response.json();

                if (result.success) {
                    const stats = result.data;
                    document.getElementById('totalKeys').textContent = stats.total_keys?.toLocaleString() || '0';
                    document.getElementById('memoryUsage').textContent = stats.memory_usage_mb + ' MB';
                    document.getElementById('hitRate').textContent = (stats.hit_rate * 100).toFixed(1) + '%';
                    document.getElementById('invalidationCount').textContent = stats.last_invalidations || '0';
                }
            } catch (error) {
                console.error('Erro ao carregar estatísticas:', error);
                showError('Erro ao carregar estatísticas');
            }
        }

        async function loadKeys(pattern = '*') {
            try {
                const response = await fetch(`/api/cache/keys?pattern=${encodeURIComponent(pattern)}&limit=100`);
                const result = await response.json();

                if (result.success) {
                    const keysList = document.getElementById('keysList');

                    if (result.data.keys.length === 0) {
                        keysList.innerHTML = '<div class="text-center py-4 text-gray-500">Nenhuma chave encontrada</div>';
                        return;
                    }

                    keysList.innerHTML = result.data.keys.map(key => `
                        <div class="flex justify-between items-center p-2 bg-gray-50 rounded border">
                            <code class="text-sm text-gray-800">${key}</code>
                            <button onclick="addKeyToInvalidation('${key}')" class="text-blue-600 hover:text-blue-800 text-sm">
                                ➕ Adicionar
                            </button>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Erro ao carregar chaves:', error);
            }
        }

        function searchKeys() {
            const pattern = document.getElementById('keysSearch').value || '*';
            loadKeys(pattern);
        }

        function addKeyToInvalidation(key) {
            const keysInput = document.getElementById('keysInput');
            const currentValue = keysInput.value;

            if (currentValue && !currentValue.endsWith('\\n')) {
                keysInput.value = currentValue + '\\n' + key;
            } else {
                keysInput.value = currentValue + key;
            }

            // Switch to keys tab
            setInvalidationTab('keys');
        }

        async function executeInvalidation() {
            const executeBtn = document.getElementById('executeBtn');
            executeBtn.disabled = true;
            executeBtn.innerHTML = '⏳ Executando...';

            try {
                const request = buildInvalidationRequest();

                if (!request) {
                    showError('Configuração inválida para invalidação');
                    return;
                }

                const response = await fetch('/api/cache/invalidate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(request)
                });

                const result = await response.json();
                showResults(result);

                // Refresh data
                if (result.success && !result.dry_run) {
                    setTimeout(() => {
                        loadStats();
                        loadHistory();
                    }, 1000);
                }

            } catch (error) {
                showError('Erro na invalidação: ' + error.message);
            } finally {
                executeBtn.disabled = false;
                executeBtn.innerHTML = '🗑️ Executar Invalidação';
            }
        }

        function buildInvalidationRequest() {
            const request = {
                invalidation_type: 'manual',
                reason: document.getElementById('reasonInput').value || 'Manual invalidation',
                cascade: document.getElementById('cascadeOption').checked,
                dry_run: document.getElementById('dryRunOption').checked
            };

            if (currentTab === 'keys') {
                const keysText = document.getElementById('keysInput').value.trim();
                if (!keysText) return null;
                request.keys = keysText.split('\\n').filter(k => k.trim());
            } else if (currentTab === 'patterns') {
                const patternsText = document.getElementById('patternsInput').value.trim();
                if (!patternsText) return null;
                request.patterns = patternsText.split('\\n').filter(p => p.trim());
            } else if (currentTab === 'scopes') {
                const checkedScopes = Array.from(document.querySelectorAll('.scope-checkbox:checked')).map(cb => cb.value);
                if (checkedScopes.length === 0) return null;
                request.scopes = checkedScopes;
            }

            return request;
        }

        async function loadHistory() {
            try {
                const response = await fetch('/api/cache/history?limit=20');
                const result = await response.json();

                if (result.success) {
                    const historyList = document.getElementById('historyList');

                    if (result.data.invalidations.length === 0) {
                        historyList.innerHTML = '<div class="text-center py-4 text-gray-500">Nenhum histórico encontrado</div>';
                        return;
                    }

                    historyList.innerHTML = result.data.invalidations.map(item => `
                        <div class="border border-gray-200 rounded p-3">
                            <div class="flex justify-between items-start">
                                <div>
                                    <div class="text-sm font-medium">${item.type || 'Manual'}</div>
                                    <div class="text-xs text-gray-600">${new Date(item.timestamp).toLocaleString('pt-BR')}</div>
                                </div>
                                <div class="text-right">
                                    <div class="text-sm font-medium">${item.keys_count || item.invalidated_count || 0} chaves</div>
                                    <div class="text-xs text-gray-600">${item.execution_time_ms || 0}ms</div>
                                </div>
                            </div>
                            ${item.reason ? `<div class="text-xs text-gray-500 mt-1">${item.reason}</div>` : ''}
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Erro ao carregar histórico:', error);
            }
        }

        function showResults(result) {
            const modal = document.getElementById('resultsModal');
            const title = document.getElementById('resultsTitle');
            const content = document.getElementById('resultsContent');

            title.textContent = result.success ?
                (result.dry_run ? 'Simulação Concluída' : 'Invalidação Concluída') :
                'Erro na Invalidação';

            let html = `
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-gray-50 p-3 rounded">
                            <div class="text-sm font-medium">Status</div>
                            <div class="text-lg ${result.success ? 'text-green-600' : 'text-red-600'}">
                                ${result.success ? '✅ Sucesso' : '❌ Erro'}
                            </div>
                        </div>
                        <div class="bg-gray-50 p-3 rounded">
                            <div class="text-sm font-medium">Total de Chaves</div>
                            <div class="text-lg">${result.total_keys}</div>
                        </div>
                        <div class="bg-gray-50 p-3 rounded">
                            <div class="text-sm font-medium">Tempo de Execução</div>
                            <div class="text-lg">${result.execution_time_ms?.toFixed(1)}ms</div>
                        </div>
                        <div class="bg-gray-50 p-3 rounded">
                            <div class="text-sm font-medium">Tipo</div>
                            <div class="text-lg">${result.dry_run ? '🧪 Simulação' : '🗑️ Real'}</div>
                        </div>
                    </div>
            `;

            if (result.errors && result.errors.length > 0) {
                html += `
                    <div class="bg-red-50 p-3 rounded">
                        <div class="text-sm font-medium text-red-800">Erros:</div>
                        <ul class="text-sm text-red-600 mt-1 list-disc list-inside">
                            ${result.errors.map(error => `<li>${error}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            if (result.invalidated_keys && result.invalidated_keys.length > 0 && result.invalidated_keys.length <= 20) {
                html += `
                    <div class="bg-blue-50 p-3 rounded">
                        <div class="text-sm font-medium text-blue-800">Chaves ${result.dry_run ? 'que seriam invalidadas' : 'invalidadas'}:</div>
                        <div class="text-sm text-blue-600 mt-1 max-h-40 overflow-y-auto">
                            ${result.invalidated_keys.map(key => `<code class="block">${key}</code>`).join('')}
                        </div>
                    </div>
                `;
            }

            html += '</div>';
            content.innerHTML = html;
            modal.classList.remove('hidden');
        }

        function closeResultsModal() {
            document.getElementById('resultsModal').classList.add('hidden');
        }

        function showError(message) {
            showResults({
                success: false,
                errors: [message],
                total_keys: 0,
                execution_time_ms: 0
            });
        }
    </script>
</body>
</html>
    """


async def cache_admin_dashboard():
    """Endpoint para dashboard administrativo"""
    return HTMLResponse(content=generate_cache_admin_dashboard())
