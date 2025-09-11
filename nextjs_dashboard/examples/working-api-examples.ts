/**
 * 🧪 Exemplos Funcionais do Cliente API Tipado
 * ===========================================
 * 
 * Demonstra como usar o cliente API com type safety completo.
 * Todos os tipos são auto-gerados e sincronizados com o backend.
 */

import apiClient from '../lib/api-client';
import type { paths, components } from '../types/api-generated';

// ===== TIPOS EXTRAÍDOS =====
type HealthResponse = components['schemas']['HealthCheckResponse'];
type AppInfoResponse = components['schemas']['AppInfo'];
type SystemMetricsResponse = components['schemas']['SystemMetrics'];

// ===== EXEMPLOS DE USO =====

export async function exemploHealthCheck(): Promise<HealthResponse> {
  try {
    // ✅ Type-safe: TypeScript conhece a estrutura da resposta
    const health = await apiClient.get('/health');
    
    // ✅ Auto-complete funciona perfeitamente
    console.log('Status:', health.status);
    console.log('Service:', health.service);
    console.log('Timestamp:', health.timestamp);
    console.log('Version:', health.version);
    
    return health;
  } catch (error) {
    console.error('Erro no health check:', error);
    throw error;
  }
}

export async function exemploAppInfo(): Promise<AppInfoResponse> {
  try {
    // ✅ Type-safe: resposta tipada automaticamente
    const appInfo = await apiClient.get('/');
    
    // ✅ TypeScript sabe exatamente quais propriedades existem
    console.log('App:', appInfo.message);
    console.log('Version:', appInfo.version);
    console.log('Status:', appInfo.status);
    console.log('Environment:', appInfo.environment);
    console.log('Docs URL:', appInfo.docs_url);
    
    return appInfo;
  } catch (error) {
    console.error('Erro ao buscar info da app:', error);
    throw error;
  }
}

export async function exemploMetricas(): Promise<SystemMetricsResponse> {
  try {
    // ✅ Type-safe: resposta tipada automaticamente
    const metrics = await apiClient.get('/metrics/system');
    
    // ✅ TypeScript sabe exatamente quais propriedades existem
    console.log('Database healthy:', metrics.database?.healthy);
    console.log('Database status:', metrics.database?.status);
    console.log('Redis healthy:', metrics.redis?.healthy);
    console.log('Cache service healthy:', metrics.cache_service?.healthy);
    
    return metrics;
  } catch (error) {
    console.error('Erro ao buscar métricas:', error);
    throw error;
  }
}

// ===== HOOKS PARA REACT =====

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: exemploHealthCheck,
    refetchInterval: 30000 // Verifica a cada 30s
  });
}

export function useAppInfo() {
  return useQuery({
    queryKey: ['app-info'],
    queryFn: exemploAppInfo,
    staleTime: 5 * 60 * 1000 // 5 minutos
  });
}

export function useSystemMetrics() {
  return useQuery({
    queryKey: ['system-metrics'],
    queryFn: exemploMetricas,
    refetchInterval: 10000 // Atualiza a cada 10s
  });
}

// ===== EXEMPLO DE TRATAMENTO DE ERRO TIPADO =====

export async function exemploComTratamentoDeErro() {
  try {
    const result = await apiClient.get('/health');
    return result;
  } catch (error) {
    if (error && typeof error === 'object' && 'status' in error) {
      const apiError = error as any;
      
      switch (apiError.status) {
        case 401:
          console.error('Não autorizado - fazer logout');
          // Redirecionar para login
          break;
        case 403:
          console.error('Acesso negado');
          break;
        case 404:
          console.error('Recurso não encontrado');
          break;
        case 500:
          console.error('Erro interno do servidor');
          break;
        default:
          console.error('Erro desconhecido:', apiError);
      }
    }
    throw error;
  }
}

// ===== DEMONSTRAÇÃO DE TYPE SAFETY =====

export function demonstracaoTypeSafety() {
  // ✅ Estas funções mostram que o TypeScript está validando tipos corretamente:
  
  // Exemplo 1: Auto-complete funciona
  const demonstrarAutoComplete = async () => {
    const health = await apiClient.get('/health');
    // TypeScript mostrará: status, timestamp, service, version
    console.log(health.status); // ✅ Auto-complete
  };
  
  // Exemplo 2: Endpoints inválidos são rejeitados
  const demonstrarValidacaoEndpoint = async () => {
    // ❌ Isso causará erro de compilação:
    // const invalid = await apiClient.get('/endpoint-inexistente');
  };
  
  // Exemplo 3: Estrutura de resposta é validada
  const demonstrarValidacaoResposta = async () => {
    const health = await apiClient.get('/health');
    // ❌ Isso causará erro de compilação:
    // console.log(health.propriedade_inexistente);
  };
}

export default {
  exemploHealthCheck,
  exemploAppInfo,
  exemploMetricas,
  exemploComTratamentoDeErro,
  useHealthCheck,
  useAppInfo,
  useSystemMetrics,
  demonstracaoTypeSafety
};
