import { io, Socket } from 'socket.io-client';
import { store } from '../store/store';
import { addNotification } from '../store/slices/notificationSlice';

type WebSocketEventCallback = (data: any) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private eventHandlers: Map<string, Set<WebSocketEventCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(userId: string, userType: 'student' | 'parent') {
    if (this.socket?.connected) {
      console.log('WebSocket already connected');
      return;
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'http://localhost:8000';
    
    this.socket = io(wsUrl, {
      path: '/ws/socket.io/',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
    });

    this.setupEventHandlers(userId, userType);
  }

  private setupEventHandlers(userId: string, userType: 'student' | 'parent') {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      
      this.socket?.emit('authenticate', { user_id: userId, user_type: userType });
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
    });

    this.socket.on('authenticated', (data) => {
      console.log('WebSocket authenticated:', data);
    });

    this.socket.on('learning_progress', (data) => {
      this.triggerEvent('learning_progress', data);
    });

    this.socket.on('quest_completion', (data) => {
      this.triggerEvent('quest_completion', data);
      
      store.dispatch(addNotification({
        id: Date.now().toString(),
        type: 'success',
        title: '퀘스트 완료!',
        message: `${data.quest?.title || '퀘스트'}를 완료했습니다!`,
        timestamp: new Date().toISOString(),
        read: false,
      }));
    });

    this.socket.on('achievement_notification', (data) => {
      this.triggerEvent('achievement_notification', data);
      
      store.dispatch(addNotification({
        id: Date.now().toString(),
        type: 'achievement',
        title: '업적 달성!',
        message: `${data.achievement?.title || '업적'}을 달성했습니다!`,
        timestamp: new Date().toISOString(),
        read: false,
      }));
    });

    this.socket.on('level_up', (data) => {
      this.triggerEvent('level_up', data);
      
      store.dispatch(addNotification({
        id: Date.now().toString(),
        type: 'info',
        title: '레벨 업!',
        message: `레벨 ${data.level?.new_level || 0}에 도달했습니다!`,
        timestamp: new Date().toISOString(),
        read: false,
      }));
    });

    this.socket.on('friend_request', (data) => {
      this.triggerEvent('friend_request', data);
      
      store.dispatch(addNotification({
        id: Date.now().toString(),
        type: 'info',
        title: '친구 요청',
        message: '새로운 친구 요청이 도착했습니다!',
        timestamp: new Date().toISOString(),
        read: false,
      }));
    });

    this.socket.on('multiplayer_invitation', (data) => {
      this.triggerEvent('multiplayer_invitation', data);
      
      store.dispatch(addNotification({
        id: Date.now().toString(),
        type: 'info',
        title: '멀티플레이어 초대',
        message: `${data.inviter_name}님이 게임에 초대했습니다!`,
        timestamp: new Date().toISOString(),
        read: false,
      }));
    });

    this.socket.on('parent_notification', (data) => {
      if (userType === 'parent') {
        this.triggerEvent('parent_notification', data);
        
        store.dispatch(addNotification({
          id: Date.now().toString(),
          type: data.type === 'achievement_unlocked' ? 'achievement' : 'info',
          title: data.title,
          message: data.message,
          timestamp: data.timestamp,
          read: false,
        }));
      }
    });

    this.socket.on('child_progress_update', (data) => {
      if (userType === 'parent') {
        this.triggerEvent('child_progress_update', data);
      }
    });

    this.socket.on('system_announcement', (data) => {
      this.triggerEvent('system_announcement', data);
      
      store.dispatch(addNotification({
        id: Date.now().toString(),
        type: 'warning',
        title: '시스템 공지',
        message: data.message,
        timestamp: data.timestamp,
        read: false,
      }));
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.eventHandlers.clear();
    }
  }

  emit(event: string, data: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected, cannot emit event:', event);
    }
  }

  on(event: string, callback: WebSocketEventCallback) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)?.add(callback);
  }

  off(event: string, callback: WebSocketEventCallback) {
    this.eventHandlers.get(event)?.delete(callback);
  }

  private triggerEvent(event: string, data: any) {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }
  }

  joinRoom(room: string) {
    this.emit('join_room', { room });
  }

  leaveRoom(room: string) {
    this.emit('leave_room', { room });
  }

  updateLearningProgress(progressData: any) {
    this.emit('learning_progress_update', progressData);
  }

  notifyQuestCompletion(questData: any) {
    this.emit('quest_completed', questData);
  }

  notifyAchievementUnlock(achievementData: any) {
    this.emit('achievement_unlocked', achievementData);
  }

  sendMultiplayerInvite(inviteeId: string, inviterName: string, gameType: string, roomId: string) {
    this.emit('multiplayer_invite', {
      invitee_id: inviteeId,
      inviter_name: inviterName,
      game_type: gameType,
      room_id: roomId,
    });
  }

  joinMultiplayerRoom(roomId: string, userName: string) {
    this.emit('multiplayer_join', {
      room_id: roomId,
      user_name: userName,
    });
  }

  sendMultiplayerAction(roomId: string, action: any) {
    this.emit('multiplayer_action', {
      room_id: roomId,
      ...action,
    });
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export const websocketService = new WebSocketService();