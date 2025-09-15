/**
 * 🎯 React Hook for Real-time Updates
 * ===================================
 *
 * Hook personalizado para conectar componentes React
 * com o sistema de real-time updates via WebSocket.
 *
 * Funcionalidades:
 * - Auto-connect/disconnect baseado no ciclo de vida do componente
 * - Event handlers tipados
 * - Estado reativo da conexão
 * - Integration com Context API
 *
 * Status: Resolução completa do problema 4.1 Real-time Updates Parciais
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  realtimeClient,
  EventType,
  RoomType,
  ConnectionState,
  WebSocketMessage,
  ConnectionStats
} from '../lib/websocket-client';

// Types para o hook
export interface UseRealtimeOptions {
  room?: RoomType | string;
  autoConnect?: boolean;
  debugMode?: boolean;
}

export interface UseRealtimeReturn {
  // Connection state
  isConnected: boolean;
  isAuthenticated: boolean;
  connectionState: ConnectionState;
  currentRoom: string;

  // Actions
  connect: (room?: string) => Promise<void>;
  disconnect: () => void;
  joinRoom: (room: string) => void;
  leaveRoom: () => void;
  sendMessage: (message: string, room?: string) => void;

  // Event subscription
  on: (eventType: EventType | string, handler: (data: any, message: WebSocketMessage) => void) => void;
  off: (eventType: EventType | string, handler?: (data: any, message: WebSocketMessage) => void) => void;

  // Utilities
  getStats: () => void;
  getRoomUsers: (room?: string) => void;
}

/**
 * 🎯 Hook principal para real-time updates
 */
export function useRealtime(options: UseRealtimeOptions = {}): UseRealtimeReturn {
  const {
    room = RoomType.GENERAL,
    autoConnect = true,
    debugMode = false
  } = options;

  // Estado do hook
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [currentRoom, setCurrentRoom] = useState<string>(room);

  // Refs para cleanup
  const handlersRef = useRef<Map<string, (data: any, message: WebSocketMessage) => void>>(new Map());

  // Derived state
  const isConnected = connectionState === ConnectionState.CONNECTED ||
                     connectionState === ConnectionState.AUTHENTICATED;
  const isAuthenticated = connectionState === ConnectionState.AUTHENTICATED;

  // Actions
  const connect = useCallback(async (targetRoom?: string) => {
    const roomToConnect = targetRoom || room;
    setCurrentRoom(roomToConnect);
    await realtimeClient.connect(roomToConnect);
  }, [room]);

  const disconnect = useCallback(() => {
    realtimeClient.disconnect();
  }, []);

  const joinRoom = useCallback((targetRoom: string) => {
    setCurrentRoom(targetRoom);
    realtimeClient.joinRoom(targetRoom);
  }, []);

  const leaveRoom = useCallback(() => {
    realtimeClient.leaveRoom();
  }, []);

  const sendMessage = useCallback((message: string, targetRoom?: string) => {
    realtimeClient.sendRoomMessage(message, targetRoom);
  }, []);

  const getStats = useCallback(() => {
    realtimeClient.getStats();
  }, []);

  const getRoomUsers = useCallback((targetRoom?: string) => {
    realtimeClient.getRoomUsers(targetRoom);
  }, []);

  // Event subscription
  const on = useCallback((eventType: EventType | string, handler: (data: any, message: WebSocketMessage) => void) => {
    handlersRef.current.set(`${eventType}_${Math.random()}`, handler);
    realtimeClient.on(eventType, handler);
  }, []);

  const off = useCallback((eventType: EventType | string, handler?: (data: any, message: WebSocketMessage) => void) => {
    realtimeClient.off(eventType, handler);

    // Remove from our ref tracking
    if (handler) {
      Array.from(handlersRef.current.entries()).forEach(([key, h]) => {
        if (h === handler) {
          handlersRef.current.delete(key);
        }
      });
    }
  }, []);

  // Setup connection state handler
  useEffect(() => {
    const handleConnectionStateChange = (state: ConnectionState, error?: string) => {
      setConnectionState(state);

      if (debugMode) {
        console.log('[useRealtime] Connection state changed:', state, error);
      }
    };

    realtimeClient.onConnectionStateChange(handleConnectionStateChange);

    // Set initial state
    setConnectionState(realtimeClient.state);
    setCurrentRoom(realtimeClient.room || 'general');

    return () => {
      // Cleanup - remove state handler (if there was a way)
    };
  }, [debugMode]);

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && !isConnected) {
      connect();
    }

    return () => {
      if (autoConnect) {
        // Clean up handlers
        handlersRef.current.forEach((handler, key) => {
          const [eventType] = key.split('_');
          realtimeClient.off(eventType, handler);
        });
        handlersRef.current.clear();
      }
    };
  }, [autoConnect, isConnected, connect]);

  return {
    // State
    isConnected,
    isAuthenticated,
    connectionState,
    currentRoom,

    // Actions
    connect,
    disconnect,
    joinRoom,
    leaveRoom,
    sendMessage,

    // Event handling
    on,
    off,

    // Utilities
    getStats,
    getRoomUsers
  };
}

/**
 * 📅 Hook especializado para updates de appointments
 */
export function useAppointmentRealtime() {
  const realtime = useRealtime({
    room: RoomType.APPOINTMENTS,
    autoConnect: true
  });

  // Estado específico para appointments
  const [appointmentUpdates, setAppointmentUpdates] = useState<{
    created: any[];
    updated: any[];
    deleted: any[];
  }>({
    created: [],
    updated: [],
    deleted: []
  });

  // Handlers específicos
  useEffect(() => {
    const handleAppointmentCreated = (data: any) => {
      setAppointmentUpdates(prev => ({
        ...prev,
        created: [data, ...prev.created.slice(0, 9)] // Keep last 10
      }));
    };

    const handleAppointmentUpdated = (data: any) => {
      setAppointmentUpdates(prev => ({
        ...prev,
        updated: [data, ...prev.updated.slice(0, 9)]
      }));
    };

    const handleAppointmentDeleted = (data: any) => {
      setAppointmentUpdates(prev => ({
        ...prev,
        deleted: [data, ...prev.deleted.slice(0, 9)]
      }));
    };

    realtime.on(EventType.APPOINTMENT_CREATED, handleAppointmentCreated);
    realtime.on(EventType.APPOINTMENT_UPDATED, handleAppointmentUpdated);
    realtime.on(EventType.APPOINTMENT_DELETED, handleAppointmentDeleted);

    return () => {
      realtime.off(EventType.APPOINTMENT_CREATED, handleAppointmentCreated);
      realtime.off(EventType.APPOINTMENT_UPDATED, handleAppointmentUpdated);
      realtime.off(EventType.APPOINTMENT_DELETED, handleAppointmentDeleted);
    };
  }, [realtime]);

  return {
    ...realtime,
    appointmentUpdates,
    clearUpdates: () => setAppointmentUpdates({ created: [], updated: [], deleted: [] })
  };
}

/**
 * 📊 Hook especializado para dashboard real-time
 */
export function useDashboardRealtime() {
  const realtime = useRealtime({
    room: RoomType.DASHBOARD,
    autoConnect: true
  });

  // Estado específico para dashboard
  const [dashboardData, setDashboardData] = useState<{
    stats?: ConnectionStats;
    notifications: any[];
    systemMessages: any[];
  }>({
    notifications: [],
    systemMessages: []
  });

  useEffect(() => {
    const handleSystemNotification = (data: any) => {
      const notification = {
        ...data,
        id: Math.random().toString(36).substr(2, 9),
        timestamp: new Date().toISOString()
      };

      setDashboardData(prev => ({
        ...prev,
        notifications: [notification, ...prev.notifications.slice(0, 19)] // Keep last 20
      }));
    };

    const handleStats = (data: any) => {
      setDashboardData(prev => ({
        ...prev,
        stats: data.stats
      }));
    };

    realtime.on(EventType.SYSTEM_NOTIFICATION, handleSystemNotification);
    realtime.on('stats', handleStats);

    // Request stats periodically
    const statsInterval = setInterval(() => {
      if (realtime.isConnected) {
        realtime.getStats();
      }
    }, 30000); // Every 30 seconds

    return () => {
      realtime.off(EventType.SYSTEM_NOTIFICATION, handleSystemNotification);
      realtime.off('stats', handleStats);
      clearInterval(statsInterval);
    };
  }, [realtime]);

  return {
    ...realtime,
    dashboardData,
    clearNotifications: () => setDashboardData(prev => ({ ...prev, notifications: [] })),
    clearSystemMessages: () => setDashboardData(prev => ({ ...prev, systemMessages: [] }))
  };
}

/**
 * 🔔 Hook para notificações em tempo real
 */
export function useNotifications() {
  const realtime = useRealtime({
    room: RoomType.NOTIFICATIONS,
    autoConnect: true
  });

  const [notifications, setNotifications] = useState<any[]>([]);

  useEffect(() => {
    const handleNotification = (data: any, message: WebSocketMessage) => {
      const notification = {
        id: Math.random().toString(36).substr(2, 9),
        type: message.type,
        data,
        timestamp: message.timestamp || new Date().toISOString(),
        read: false
      };

      setNotifications(prev => [notification, ...prev]);
    };

    // Subscribe to various notification types
    [
      EventType.APPOINTMENT_CREATED,
      EventType.APPOINTMENT_UPDATED,
      EventType.APPOINTMENT_DELETED,
      EventType.SYSTEM_NOTIFICATION,
      EventType.USER_STATUS_CHANGED
    ].forEach(eventType => {
      realtime.on(eventType, handleNotification);
    });

    return () => {
      [
        EventType.APPOINTMENT_CREATED,
        EventType.APPOINTMENT_UPDATED,
        EventType.APPOINTMENT_DELETED,
        EventType.SYSTEM_NOTIFICATION,
        EventType.USER_STATUS_CHANGED
      ].forEach(eventType => {
        realtime.off(eventType, handleNotification);
      });
    };
  }, [realtime]);

  const markAsRead = useCallback((notificationId: string) => {
    setNotifications(prev =>
      prev.map(notif =>
        notif.id === notificationId
          ? { ...notif, read: true }
          : notif
      )
    );
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  return {
    ...realtime,
    notifications,
    unreadCount,
    markAsRead,
    clearAll
  };
}
