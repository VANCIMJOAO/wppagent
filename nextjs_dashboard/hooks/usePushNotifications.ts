/**
 * 🔔 Hook para Push Notifications
 * 
 * React hook para gerenciar push notifications no dashboard.
 */

import { useState, useEffect, useCallback } from 'react';
import pushNotificationService from '../lib/push-service';

interface PushNotificationStatus {
  supported: boolean;
  permission: NotificationPermission;
  subscribed: boolean;
  endpoint?: string;
}

interface UsePushNotificationsReturn {
  status: PushNotificationStatus;
  isLoading: boolean;
  subscribe: () => Promise<boolean>;
  unsubscribe: () => Promise<boolean>;
  sendTestNotification: () => Promise<boolean>;
  refresh: () => void;
}

export function usePushNotifications(): UsePushNotificationsReturn {
  const [status, setStatus] = useState<PushNotificationStatus>({
    supported: false,
    permission: 'default',
    subscribed: false
  });
  const [isLoading, setIsLoading] = useState(true);

  // Função para atualizar status
  const updateStatus = useCallback(() => {
    const currentStatus = pushNotificationService.getSubscriptionStatus();
    setStatus(currentStatus);
  }, []);

  // Inicializar e verificar status
  useEffect(() => {
    const initialize = async () => {
      setIsLoading(true);
      
      try {
        await pushNotificationService.initialize();
        updateStatus();
      } catch (error) {
        console.error('Error initializing push notifications:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initialize();
  }, [updateStatus]);

  // Função para subscrever
  const subscribe = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      const success = await pushNotificationService.subscribe();
      updateStatus();
      return success;
    } catch (error) {
      console.error('Error subscribing:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [updateStatus]);

  // Função para dessubscrever
  const unsubscribe = useCallback(async (): Promise<boolean> => {
    setIsLoading(true);
    
    try {
      const success = await pushNotificationService.unsubscribe();
      updateStatus();
      return success;
    } catch (error) {
      console.error('Error unsubscribing:', error);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [updateStatus]);

  // Função para enviar teste
  const sendTestNotification = useCallback(async (): Promise<boolean> => {
    try {
      return await pushNotificationService.sendTestNotification();
    } catch (error) {
      console.error('Error sending test notification:', error);
      return false;
    }
  }, []);

  // Função para atualizar status manualmente
  const refresh = useCallback(() => {
    updateStatus();
  }, [updateStatus]);

  return {
    status,
    isLoading,
    subscribe,
    unsubscribe,
    sendTestNotification,
    refresh
  };
}

export default usePushNotifications;
