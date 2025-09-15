/**
 * 🔍 Token Debug Hook and Dashboard
 * ================================
 *
 * Hook e componente para debugging do TokenManager e monitoramento
 * de race conditions em tempo real.
 *
 * Funcionalidades:
 * - Monitoramento em tempo real do estado dos tokens
 * - Detecção de race conditions
 * - Logs de refresh attempts
 * - Interface visual para debugging
 * - Métricas de performance
 *
 * Autor: Claude AI
 * Status: Tool de debugging para JWT Race Condition
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { tokenManager, getTokenInfo } from '../lib/token-manager';

interface TokenDebugInfo {
  hasAccessToken: boolean;
  hasRefreshToken: boolean;
  isValid: boolean;
  expiresIn: number | null;
  isRefreshing: boolean;
  lastUpdate: Date;
}

interface RefreshAttempt {
  timestamp: Date;
  success: boolean;
  duration: number;
  error?: string;
}

export function useTokenDebug() {
  const [tokenInfo, setTokenInfo] = useState<TokenDebugInfo | null>(null);
  const [refreshAttempts, setRefreshAttempts] = useState<RefreshAttempt[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);

  /**
   * 📊 Update token info
   */
  const updateTokenInfo = useCallback(() => {
    const info = getTokenInfo();
    setTokenInfo({
      ...info,
      lastUpdate: new Date()
    });
  }, []);

  /**
   * 🔄 Test token refresh
   */
  const testTokenRefresh = useCallback(async () => {
    const startTime = Date.now();
    const attempt: RefreshAttempt = {
      timestamp: new Date(),
      success: false,
      duration: 0
    };

    try {
      await tokenManager.forceRefresh();
      attempt.success = true;
      attempt.duration = Date.now() - startTime;

      console.log('✅ Test refresh successful');

    } catch (error: any) {
      attempt.success = false;
      attempt.duration = Date.now() - startTime;
      attempt.error = error.message;

      console.error('❌ Test refresh failed:', error);
    }

    setRefreshAttempts(prev => [attempt, ...prev.slice(0, 9)]); // Keep last 10 attempts
    updateTokenInfo();
  }, [updateTokenInfo]);

  /**
   * 🗑️ Clear debug data
   */
  const clearDebugData = useCallback(() => {
    setRefreshAttempts([]);
    updateTokenInfo();
  }, [updateTokenInfo]);

  /**
   * 🎯 Start/stop monitoring
   */
  const toggleMonitoring = useCallback(() => {
    setIsMonitoring(prev => !prev);
  }, []);

  /**
   * 🔄 Auto-update token info when monitoring
   */
  useEffect(() => {
    if (!isMonitoring) return;

    const interval = setInterval(updateTokenInfo, 1000); // Update every second
    return () => clearInterval(interval);
  }, [isMonitoring, updateTokenInfo]);

  /**
   * 🚀 Initial load
   */
  useEffect(() => {
    updateTokenInfo();
  }, [updateTokenInfo]);

  return {
    tokenInfo,
    refreshAttempts,
    isMonitoring,
    updateTokenInfo,
    testTokenRefresh,
    clearDebugData,
    toggleMonitoring
  };
}

/**
 * 📱 Token Debug Dashboard Component
 */
export function TokenDebugDashboard() {
  const {
    tokenInfo,
    refreshAttempts,
    isMonitoring,
    updateTokenInfo,
    testTokenRefresh,
    clearDebugData,
    toggleMonitoring
  } = useTokenDebug();

  const formatTimeRemaining = (seconds: number | null): string => {
    if (seconds === null) return 'N/A';
    if (seconds <= 0) return 'EXPIRED';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${remainingSeconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      return `${remainingSeconds}s`;
    }
  };

  const getStatusColor = (isValid: boolean, expiresIn: number | null): string => {
    if (!isValid || (expiresIn !== null && expiresIn <= 0)) return 'text-red-500';
    if (expiresIn !== null && expiresIn < 300) return 'text-yellow-500'; // Less than 5 minutes
    return 'text-green-500';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          🔍 Token Debug Dashboard
        </h2>
        <div className="flex gap-2">
          <button
            onClick={toggleMonitoring}
            className={`px-3 py-1 rounded text-sm font-medium ${
              isMonitoring
                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
          >
            {isMonitoring ? '⏸️ Stop' : '▶️ Monitor'}
          </button>
        </div>
      </div>

      {/* Token Status */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded">
          <h3 className="font-semibold text-sm text-gray-600">Access Token</h3>
          <p className={`text-lg font-bold ${tokenInfo?.hasAccessToken ? 'text-green-500' : 'text-red-500'}`}>
            {tokenInfo?.hasAccessToken ? '✅ Present' : '❌ Missing'}
          </p>
        </div>

        <div className="bg-gray-50 p-4 rounded">
          <h3 className="font-semibold text-sm text-gray-600">Refresh Token</h3>
          <p className={`text-lg font-bold ${tokenInfo?.hasRefreshToken ? 'text-green-500' : 'text-red-500'}`}>
            {tokenInfo?.hasRefreshToken ? '✅ Present' : '❌ Missing'}
          </p>
        </div>

        <div className="bg-gray-50 p-4 rounded">
          <h3 className="font-semibold text-sm text-gray-600">Token Status</h3>
          <p className={`text-lg font-bold ${getStatusColor(tokenInfo?.isValid ?? false, tokenInfo?.expiresIn ?? null)}`}>
            {tokenInfo?.isValid ? '✅ Valid' : '❌ Invalid'}
          </p>
        </div>

        <div className="bg-gray-50 p-4 rounded">
          <h3 className="font-semibold text-sm text-gray-600">Time Remaining</h3>
          <p className={`text-lg font-bold ${getStatusColor(tokenInfo?.isValid ?? false, tokenInfo?.expiresIn ?? null)}`}>
            {formatTimeRemaining(tokenInfo?.expiresIn ?? null)}
          </p>
        </div>
      </div>

      {/* Refresh Status */}
      {tokenInfo?.isRefreshing && (
        <div className="bg-blue-50 border border-blue-200 p-4 rounded mb-6">
          <p className="text-blue-700 font-medium">
            🔄 Token refresh in progress...
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={updateTokenInfo}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          🔄 Refresh Info
        </button>

        <button
          onClick={testTokenRefresh}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          disabled={tokenInfo?.isRefreshing}
        >
          🧪 Test Refresh
        </button>

        <button
          onClick={clearDebugData}
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
        >
          🗑️ Clear Data
        </button>
      </div>

      {/* Refresh Attempts History */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3">
          📊 Recent Refresh Attempts ({refreshAttempts.length})
        </h3>

        {refreshAttempts.length === 0 ? (
          <p className="text-gray-500 italic">No refresh attempts recorded</p>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {refreshAttempts.map((attempt, index) => (
              <div
                key={index}
                className={`p-3 rounded border-l-4 ${
                  attempt.success
                    ? 'border-green-400 bg-green-50'
                    : 'border-red-400 bg-red-50'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className={`font-medium ${
                      attempt.success ? 'text-green-700' : 'text-red-700'
                    }`}>
                      {attempt.success ? '✅ Success' : '❌ Failed'}
                    </p>
                    <p className="text-sm text-gray-600">
                      {attempt.timestamp.toLocaleTimeString()}
                    </p>
                    {attempt.error && (
                      <p className="text-sm text-red-600 mt-1">
                        Error: {attempt.error}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">
                      {attempt.duration}ms
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Last Update */}
      {tokenInfo?.lastUpdate && (
        <div className="mt-4 text-center text-sm text-gray-500">
          Last updated: {tokenInfo.lastUpdate.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}

export default TokenDebugDashboard;
