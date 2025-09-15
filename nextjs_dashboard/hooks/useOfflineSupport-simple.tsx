/**
 * Simplified useOfflineSupport hook for build compatibility
 */

import { useState, useEffect } from 'react';

export enum OfflineStatus {
  ONLINE = 'online',
  OFFLINE = 'offline'
}

interface OfflineHookResult {
  status: OfflineStatus;
  queueSize: number;
  isSyncing: boolean;
  syncNow: () => Promise<boolean>;
  clearQueue: () => Promise<void>;
  getQueuedItems: () => any[];
  isOnline: boolean;
  isOffline: boolean;
}

export function useOfflineSupport(): OfflineHookResult {
  const [status, setStatus] = useState<OfflineStatus>(
    typeof navigator !== 'undefined' && navigator.onLine
      ? OfflineStatus.ONLINE
      : OfflineStatus.OFFLINE
  );
  const [queueSize] = useState(0);
  const [isSyncing] = useState(false);

  useEffect(() => {
    const handleOnline = () => setStatus(OfflineStatus.ONLINE);
    const handleOffline = () => setStatus(OfflineStatus.OFFLINE);

    if (typeof window !== 'undefined') {
      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }
  }, []);

  const syncNow = async (): Promise<boolean> => {
    return true;
  };

  const clearQueue = async (): Promise<void> => {
    return;
  };

  const getQueuedItems = () => {
    return [];
  };

  return {
    status,
    queueSize,
    isSyncing,
    syncNow,
    clearQueue,
    getQueuedItems,
    isOnline: status === OfflineStatus.ONLINE,
    isOffline: status === OfflineStatus.OFFLINE
  };
}

export default useOfflineSupport;
