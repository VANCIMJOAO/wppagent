import { useEffect, useRef, useCallback } from 'react';
import { debugLog } from '@/lib/debug';
import { emitAuthEvent, AuthEventType } from '@/lib/auth-events';

/**
 * Hook para renovação automática de token
 * 
 * Funcionalidades:
 * - Verifica validade do token a cada 10 minutos
 * - Renova token automaticamente quando necessário
 * - Emite eventos de autenticação para sincronização global
 * - Previne múltiplas renovações simultâneas
 * 
 * ✅ CORREÇÃO #11: Todos os logs são condicionais via debugLog
 * - debugLog só executa em NODE_ENV=development
 * - Zero logs em produção (performance e segurança)
 * - Para produção, use sistema de monitoring (Sentry, DataDog)
 */
export function useTokenRefresh() {
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isRefreshingRef = useRef(false);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    // Prevenir múltiplas renovações simultâneas
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
        emitAuthEvent(AuthEventType.TOKEN_REFRESHED, {
          source: 'use-token-refresh',
          reason: 'Token renovado com sucesso'
        });
        return true;
      } else {
        debugLog.warn('⚠️ Falha ao renovar token automaticamente');
        emitAuthEvent(AuthEventType.TOKEN_EXPIRED, {
          source: 'use-token-refresh',
          reason: 'Falha ao renovar token'
        });
        return false;
      }
    } catch (error) {
      debugLog.error('❌ Erro ao renovar token:', error);
      emitAuthEvent(AuthEventType.SESSION_EXPIRED, {
        source: 'use-token-refresh',
        reason: 'Erro ao renovar token'
      });
      return false;
    } finally {
      isRefreshingRef.current = false;
    }
  }, []);

  const checkTokenValidity = useCallback(async (): Promise<boolean> => {
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
        emitAuthEvent(AuthEventType.TOKEN_EXPIRED, {
          source: 'use-token-refresh',
          reason: 'Token inválido ou expirado'
        });
      }
      
      return isValid;
    } catch (error) {
      debugLog.error('❌ Erro ao verificar validade do token:', error);
      emitAuthEvent(AuthEventType.SESSION_EXPIRED, {
        source: 'use-token-refresh',
        reason: 'Erro ao verificar validade do token'
      });
      return false;
    }
  }, []);

  useEffect(() => {
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
          await refreshToken();
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Dependências vazias intencionais - funções são estáveis via useCallback

  return {
    refreshToken,
    checkTokenValidity
  };
}
