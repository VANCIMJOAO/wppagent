import { useEffect, useRef } from 'react';
import { debugLog } from '@/lib/debug';

/**
 * Hook para renovação automática de token
 * Verifica e renova o token antes que expire
 */
export function useTokenRefresh() {
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isRefreshingRef = useRef(false);

  const refreshToken = async (): Promise<boolean> => {
    if (isRefreshingRef.current) {
      debugLog.warn('⚠️ Renovação de token já em andamento, pulando...');
      return false;
    }

    try {
      isRefreshingRef.current = true;
      debugLog.auth('🔄 Iniciando renovação automática de token...');

      const response = await fetch('/api/auth/refresh-token', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        debugLog.success('✅ Token renovado automaticamente!');
        return true;
      } else {
        debugLog.warn('⚠️ Falha ao renovar token automaticamente');
        return false;
      }
    } catch (error) {
      debugLog.error('❌ Erro ao renovar token:', error);
      return false;
    } finally {
      isRefreshingRef.current = false;
    }
  };

  const checkTokenValidity = async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/auth/status', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        debugLog.warn('⚠️ Resposta não OK do /api/auth/status:', response.status);
        return false;
      }

      const data = await response.json();
      const isValid = data.isAuthenticated === true;
      
      if (isValid) {
        debugLog.success('✅ Token válido via secure cookie');
      } else {
        debugLog.warn('⚠️ Token inválido ou expirado');
        
        // ✅ CORREÇÃO: Redirecionamento removido para evitar loop infinito
        // O auth-context.tsx agora centraliza todos os redirecionamentos
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          debugLog.info('🔄 Token expirado detectado - deixando auth-context fazer redirecionamento');
          // Redirecionamento centralizado no auth-context.tsx
        }
      }
      
      return isValid;
    } catch (error) {
      debugLog.error('❌ Erro ao verificar validade do token:', error);
      
      // ✅ CORREÇÃO: Redirecionamento removido para evitar loop infinito
      // O auth-context.tsx agora centraliza todos os redirecionamentos
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        debugLog.info('🔄 Erro de verificação detectado - deixando auth-context fazer redirecionamento');
        // Redirecionamento centralizado no auth-context.tsx
      }
      
      return false;
    }
  };

  useEffect(() => {
    // Verificar token a cada 10 minutos (token agora expira em 2 horas)
    const checkInterval = 10 * 60 * 1000; // 10 minutos
    
    const startTokenRefresh = () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }

      refreshIntervalRef.current = setInterval(async () => {
        debugLog.info('🔍 Verificando validade do token...');
        
        const isValid = await checkTokenValidity();
        
        if (!isValid) {
          debugLog.warn('⚠️ Token inválido, tentando renovar...');
          const refreshed = await refreshToken();
          
          if (!refreshed) {
            debugLog.error('❌ Falha ao renovar token - deixando auth-context fazer redirecionamento');
            // ✅ CORREÇÃO: NÃO redirecionar aqui - auth-context centraliza redirecionamentos
            // window.location.href = '/login'; // REMOVIDO para evitar loop infinito
          }
        } else {
          debugLog.success('✅ Token válido');
        }
      }, checkInterval);
    };

    // Iniciar verificação após 30 segundos
    const initialDelay = setTimeout(startTokenRefresh, 30000);

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
      clearTimeout(initialDelay);
    };
  }, [refreshToken, checkTokenValidity]); // ✅ CORREÇÃO: Dependências corretas

  return {
    refreshToken,
    checkTokenValidity
  };
}
