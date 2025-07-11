import { useEffect, useCallback } from 'react';
import { useAppSelector } from './useAppSelector';
import { websocketService } from '../services/websocketService';

type EventCallback = (data: any) => void;

export const useWebSocket = () => {
  const { user } = useAppSelector((state) => state.auth);

  useEffect(() => {
    if (user) {
      const userType = user.role === 'parent' ? 'parent' : 'student';
      websocketService.connect(user.id.toString(), userType);
    }

    return () => {
      if (!user) {
        websocketService.disconnect();
      }
    };
  }, [user]);

  const subscribe = useCallback((event: string, callback: EventCallback) => {
    websocketService.on(event, callback);
    
    return () => {
      websocketService.off(event, callback);
    };
  }, []);

  const emit = useCallback((event: string, data: any) => {
    websocketService.emit(event, data);
  }, []);

  const joinRoom = useCallback((room: string) => {
    websocketService.joinRoom(room);
  }, []);

  const leaveRoom = useCallback((room: string) => {
    websocketService.leaveRoom(room);
  }, []);

  const isConnected = useCallback(() => {
    return websocketService.isConnected();
  }, []);

  return {
    subscribe,
    emit,
    joinRoom,
    leaveRoom,
    isConnected,
    websocketService,
  };
};