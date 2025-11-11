/**
 * WebSocket Hook for Real-time Collaboration
 *
 * Provides WebSocket connection management and real-time event handling
 * for comments, presence, notifications, and other collaborative features.
 */

'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import type {
  WSMessage,
  WSMessageType,
  UserPresence,
  TypingIndicator,
  Comment,
  Notification,
} from '@/types/collaboration';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

interface UseWebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WSMessage) => void;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  error: Event | null;
  send: (message: WSMessage) => void;
  joinRoom: (roomType: string, roomId: string) => void;
  leaveRoom: (roomType: string, roomId: string) => void;
  connect: () => void;
  disconnect: () => void;
}

/**
 * Hook for managing WebSocket connections
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    onConnect,
    onDisconnect,
    onError,
    onMessage,
    autoConnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Event | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setIsConnecting(true);
    setError(null);

    const token = localStorage.getItem('access_token');
    const wsUrl = token ? `${WS_URL}?token=${token}` : WS_URL;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;
        onConnect?.();
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        wsRef.current = null;
        onDisconnect?.();

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (event) => {
        setError(event);
        setIsConnecting(false);
        onError?.(event);
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setIsConnecting(false);
      console.error('Failed to create WebSocket connection:', err);
    }
  }, [onConnect, onDisconnect, onError, onMessage, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const send = useCallback((message: WSMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }, []);

  const joinRoom = useCallback(
    (roomType: string, roomId: string) => {
      send({
        type: 'join_room' as WSMessageType,
        data: { room_type: roomType, room_id: roomId },
        timestamp: new Date().toISOString(),
      });
    },
    [send]
  );

  const leaveRoom = useCallback(
    (roomType: string, roomId: string) => {
      send({
        type: 'leave_room' as WSMessageType,
        data: { room_type: roomType, room_id: roomId },
        timestamp: new Date().toISOString(),
      });
    },
    [send]
  );

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    error,
    send,
    joinRoom,
    leaveRoom,
    connect,
    disconnect,
  };
}

/**
 * Hook for managing user presence in a resource
 */
export function usePresence(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string
) {
  const [activeUsers, setActiveUsers] = useState<UserPresence[]>([]);

  const handleMessage = useCallback((message: WSMessage) => {
    if (message.type === 'user_presence') {
      const presence: UserPresence = message.data;
      setActiveUsers((prev) => {
        const existingIndex = prev.findIndex((u) => u.user_id === presence.user_id);
        if (existingIndex >= 0) {
          // Update existing user
          const updated = [...prev];
          updated[existingIndex] = presence;
          return updated;
        } else if (presence.status !== 'offline') {
          // Add new user
          return [...prev, presence];
        }
        return prev;
      });

      // Remove offline users after a delay
      if (presence.status === 'offline') {
        setTimeout(() => {
          setActiveUsers((prev) =>
            prev.filter((u) => u.user_id !== presence.user_id)
          );
        }, 5000);
      }
    }
  }, []);

  const ws = useWebSocket({
    onMessage: handleMessage,
  });

  useEffect(() => {
    if (ws.isConnected) {
      ws.joinRoom(resourceType, resourceId);
      return () => {
        ws.leaveRoom(resourceType, resourceId);
      };
    }
  }, [ws.isConnected, resourceType, resourceId, ws]);

  return {
    activeUsers,
    ...ws,
  };
}

/**
 * Hook for real-time comments
 */
export function useRealtimeComments(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string,
  onCommentAdded?: (comment: Comment) => void,
  onCommentUpdated?: (comment: Comment) => void,
  onCommentDeleted?: (commentId: string) => void
) {
  const handleMessage = useCallback(
    (message: WSMessage) => {
      switch (message.type) {
        case 'comment_added':
          onCommentAdded?.(message.data);
          break;
        case 'comment_updated':
          onCommentUpdated?.(message.data);
          break;
        case 'comment_deleted':
          onCommentDeleted?.(message.data.comment_id);
          break;
      }
    },
    [onCommentAdded, onCommentUpdated, onCommentDeleted]
  );

  const ws = useWebSocket({
    onMessage: handleMessage,
  });

  useEffect(() => {
    if (ws.isConnected) {
      ws.joinRoom(resourceType, resourceId);
      return () => {
        ws.leaveRoom(resourceType, resourceId);
      };
    }
  }, [ws.isConnected, resourceType, resourceId, ws]);

  return ws;
}

/**
 * Hook for typing indicators
 */
export function useTypingIndicator(
  resourceType: 'video' | 'project' | 'clip',
  resourceId: string
) {
  const [typingUsers, setTypingUsers] = useState<TypingIndicator[]>([]);
  const typingTimeoutRef = useRef<{ [userId: string]: NodeJS.Timeout }>({});

  const handleMessage = useCallback((message: WSMessage) => {
    if (message.type === 'user_typing') {
      const typing: TypingIndicator = message.data;

      if (typing.is_typing) {
        setTypingUsers((prev) => {
          const existingIndex = prev.findIndex((t) => t.user_id === typing.user_id);
          if (existingIndex >= 0) {
            const updated = [...prev];
            updated[existingIndex] = typing;
            return updated;
          }
          return [...prev, typing];
        });

        // Clear existing timeout
        if (typingTimeoutRef.current[typing.user_id]) {
          clearTimeout(typingTimeoutRef.current[typing.user_id]);
        }

        // Set timeout to remove typing indicator
        typingTimeoutRef.current[typing.user_id] = setTimeout(() => {
          setTypingUsers((prev) =>
            prev.filter((t) => t.user_id !== typing.user_id)
          );
        }, 3000);
      } else {
        // User stopped typing
        setTypingUsers((prev) =>
          prev.filter((t) => t.user_id !== typing.user_id)
        );
        if (typingTimeoutRef.current[typing.user_id]) {
          clearTimeout(typingTimeoutRef.current[typing.user_id]);
        }
      }
    }
  }, []);

  const ws = useWebSocket({
    onMessage: handleMessage,
  });

  const sendTypingIndicator = useCallback(
    (isTyping: boolean) => {
      ws.send({
        type: 'user_typing' as WSMessageType,
        data: {
          resource_type: resourceType,
          resource_id: resourceId,
          is_typing: isTyping,
        },
        timestamp: new Date().toISOString(),
      });
    },
    [ws, resourceType, resourceId]
  );

  useEffect(() => {
    if (ws.isConnected) {
      ws.joinRoom(resourceType, resourceId);
      return () => {
        ws.leaveRoom(resourceType, resourceId);
      };
    }
  }, [ws.isConnected, resourceType, resourceId, ws]);

  return {
    typingUsers,
    sendTypingIndicator,
    ...ws,
  };
}

/**
 * Hook for real-time notifications
 */
export function useRealtimeNotifications(
  onNotification?: (notification: Notification) => void
) {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const handleMessage = useCallback(
    (message: WSMessage) => {
      if (message.type === 'notification') {
        const notification: Notification = message.data;
        setNotifications((prev) => [notification, ...prev]);
        onNotification?.(notification);
      }
    },
    [onNotification]
  );

  const ws = useWebSocket({
    onMessage: handleMessage,
  });

  return {
    notifications,
    ...ws,
  };
}
