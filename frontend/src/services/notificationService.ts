import { io, Socket } from 'socket.io-client';
import { apiWrapper } from '../utils/apiWrapper';
import api from './api';
import type {
  Notification,
  NotificationSettings,
  NotificationListResponse,
  NotificationStatsResponse,
  WebSocketMessage,
  NotificationWebSocketMessage,
  NotificationReadMessage,
  NotificationBulkAction,
  OnlineStatus,
  TypingIndicator,
  LiveUpdate,
  BrowserNotificationOptions
} from '../types/notification';
import {
  NotificationType,
  NotificationCategory,
  NotificationPriority
} from '../types/notification';

class NotificationService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnected = false;
  private eventHandlers: Map<string, Function[]> = new Map();

  // Initialize WebSocket connection
  connect(userId: string, token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(import.meta.env.VITE_WS_URL || 'ws://localhost:8000', {
          auth: {
            token,
            userId
          },
          transports: ['websocket'],
          timeout: 10000,
          reconnection: true,
          reconnectionAttempts: this.maxReconnectAttempts,
          reconnectionDelay: this.reconnectDelay
        });

        this.socket.on('connect', () => {
          console.log('✅ WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.emit('connection_status', { connected: true });
          resolve();
        });

        this.socket.on('disconnect', (reason) => {
          console.log('❌ WebSocket disconnected:', reason);
          this.isConnected = false;
          this.emit('connection_status', { connected: false, reason });
        });

        this.socket.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          this.isConnected = false;
          this.emit('connection_status', { connected: false, error: error.message });
          
          if (this.reconnectAttempts === 0) {
            reject(error);
          }
        });

        this.socket.on('reconnect', (attemptNumber) => {
          console.log(`🔄 WebSocket reconnected after ${attemptNumber} attempts`);
          this.isConnected = true;
          this.emit('connection_status', { connected: true, reconnected: true });
        });

        this.socket.on('reconnect_failed', () => {
          console.error('❌ WebSocket reconnection failed after maximum attempts');
          this.isConnected = false;
          this.emit('connection_status', { connected: false, failed: true });
        });

        // Real-time notification handlers
        this.socket.on('notification', (data: Notification) => {
          this.handleNewNotification(data);
        });

        this.socket.on('notification_read', (data: { notification_id: string; user_id: string }) => {
          this.emit('notification_read', data);
        });

        this.socket.on('bulk_action', (data: { action: string; category?: string; user_id: string }) => {
          this.emit('bulk_action', data);
        });

        this.socket.on('online_status', (data: OnlineStatus) => {
          this.emit('online_status', data);
        });

        this.socket.on('typing_indicator', (data: TypingIndicator) => {
          this.emit('typing_indicator', data);
        });

        this.socket.on('live_update', (data: LiveUpdate) => {
          this.emit('live_update', data);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  // Disconnect WebSocket
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      this.eventHandlers.clear();
    }
  }

  // Event handler management
  on(event: string, handler: Function): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event)!.push(handler);
  }

  off(event: string, handler?: Function): void {
    if (!handler) {
      this.eventHandlers.delete(event);
      return;
    }

    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  // Handle new notification
  private async handleNewNotification(notification: Notification): Promise<void> {
    // Store notification locally for offline support
    this.storeNotificationLocally(notification);

    // Emit to listeners
    this.emit('new_notification', notification);

    // Show browser notification if enabled
    if (notification.show_popup) {
      await this.showBrowserNotification(notification);
    }

    // Play sound if enabled
    if (notification.play_sound) {
      this.playNotificationSound();
    }

    // Vibrate if enabled
    if (notification.vibrate && 'vibrate' in navigator) {
      navigator.vibrate([200, 100, 200]);
    }
  }

  // API Methods for notifications
  async fetchNotifications(cursor?: string, limit: number = 20): Promise<NotificationListResponse> {
    const params: any = { limit };
    if (cursor) params.cursor = cursor;
    
    return apiWrapper<NotificationListResponse>(
      () => api.get('/notifications', { params }),
      'Error fetching notifications'
    );
  }

  async markAsRead(notificationId: string): Promise<void> {
    await apiWrapper<void>(
      () => api.post(`/notifications/${notificationId}/read`),
      'Error marking notification as read'
    );

    // Emit via WebSocket for real-time updates
    if (this.socket && this.isConnected) {
      this.socket.emit('notification_read', { notification_id: notificationId });
    }
  }

  async markAllAsRead(category?: NotificationCategory): Promise<void> {
    const params = category ? { category } : {};
    
    await apiWrapper<void>(
      () => api.post('/notifications/mark-all-read', null, { params }),
      'Error marking all notifications as read'
    );

    // Emit via WebSocket
    if (this.socket && this.isConnected) {
      this.socket.emit('bulk_action', {
        action: 'mark_all_read',
        category
      });
    }
  }

  async dismissNotification(notificationId: string): Promise<void> {
    return apiWrapper<void>(
      () => api.post(`/notifications/${notificationId}/dismiss`),
      'Error dismissing notification'
    );
  }

  async clearAll(category?: NotificationCategory): Promise<void> {
    const params = category ? { category } : {};
    
    await apiWrapper<void>(
      () => api.delete('/notifications/clear', { params }),
      'Error clearing notifications'
    );

    // Emit via WebSocket
    if (this.socket && this.isConnected) {
      this.socket.emit('bulk_action', {
        action: 'clear_all',
        category
      });
    }
  }

  async getNotificationStats(): Promise<NotificationStatsResponse> {
    return apiWrapper<NotificationStatsResponse>(
      () => api.get('/notifications/stats'),
      'Error fetching notification stats'
    );
  }

  async updateSettings(settings: Partial<NotificationSettings>): Promise<void> {
    await apiWrapper<void>(
      () => api.put('/notifications/settings', settings),
      'Error updating notification settings'
    );

    // Emit via WebSocket
    if (this.socket && this.isConnected) {
      this.socket.emit('settings_update', settings);
    }
  }

  async getSettings(): Promise<NotificationSettings> {
    return apiWrapper<NotificationSettings>(
      () => api.get('/notifications/settings'),
      'Error fetching notification settings'
    );
  }

  // Browser notification methods
  async requestNotificationPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      throw new Error('This browser does not support notifications');
    }

    const permission = await Notification.requestPermission();
    return permission;
  }

  private async showBrowserNotification(notification: Notification): Promise<void> {
    if (!('Notification' in window) || Notification.permission !== 'granted') {
      return;
    }

    const options: BrowserNotificationOptions = {
      title: notification.title,
      body: notification.message,
      icon: notification.icon || '/notification-icon.png',
      badge: '/notification-badge.png',
      tag: notification.id,
      data: notification.data,
      requireInteraction: notification.priority === NotificationPriority.URGENT,
      silent: !notification.play_sound
    };

    if (notification.actions && notification.actions.length > 0) {
      options.actions = notification.actions.slice(0, 2).map(action => ({
        action: action.id,
        title: action.label,
        icon: undefined
      }));
    }

    const browserNotification = new Notification(options.title, options);

    browserNotification.onclick = () => {
      window.focus();
      if (notification.actions && notification.actions[0]) {
        this.handleNotificationAction(notification.id, notification.actions[0].id);
      }
      browserNotification.close();
    };

    // Auto-dismiss after specified time
    if (notification.auto_dismiss_after) {
      setTimeout(() => {
        browserNotification.close();
      }, notification.auto_dismiss_after * 1000);
    }
  }

  private playNotificationSound(): void {
    try {
      const audio = new Audio('/notification-sound.mp3');
      audio.volume = 0.5;
      audio.play().catch(error => {
        console.warn('Could not play notification sound:', error);
      });
    } catch (error) {
      console.warn('Error playing notification sound:', error);
    }
  }

  private handleNotificationAction(notificationId: string, actionId: string): void {
    this.emit('notification_action', { notificationId, actionId });
  }

  // Local storage for offline support
  private storeNotificationLocally(notification: Notification): void {
    try {
      const stored = localStorage.getItem('pending_notifications');
      const notifications: Notification[] = stored ? JSON.parse(stored) : [];
      
      notifications.unshift(notification);
      
      // Keep only last 50 notifications
      if (notifications.length > 50) {
        notifications.splice(50);
      }
      
      localStorage.setItem('pending_notifications', JSON.stringify(notifications));
    } catch (error) {
      console.warn('Could not store notification locally:', error);
    }
  }

  getPendingNotifications(): Notification[] {
    try {
      const stored = localStorage.getItem('pending_notifications');
      return stored ? JSON.parse(stored) : [];
    } catch (error) {
      console.warn('Could not retrieve pending notifications:', error);
      return [];
    }
  }

  clearPendingNotifications(): void {
    localStorage.removeItem('pending_notifications');
  }

  // Connection status
  isSocketConnected(): boolean {
    return this.isConnected && this.socket?.connected === true;
  }

  // Send typing indicator
  sendTypingIndicator(location: string, isTyping: boolean): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('typing_indicator', {
        location,
        is_typing: isTyping,
        timestamp: new Date().toISOString()
      });
    }
  }

  // Update online status
  updateOnlineStatus(activity?: string, location?: string): void {
    if (this.socket && this.isConnected) {
      this.socket.emit('online_status', {
        is_online: true,
        current_activity: activity,
        location,
        last_seen: new Date().toISOString()
      });
    }
  }

  // Mock data for development
  getMockNotifications(): Notification[] {
    return [
      {
        id: '1',
        type: NotificationType.ACHIEVEMENT_UNLOCKED,
        category: NotificationCategory.ACHIEVEMENT,
        priority: NotificationPriority.HIGH,
        title: '🏆 Achievement Unlocked!',
        message: 'You completed your first quest!',
        icon: '🏆',
        color: '#FFD700',
        data: {
          achievement_id: 'first_quest',
          experience_gained: 100,
          image_url: '/achievements/first_quest.png'
        },
        user_id: 'user1',
        is_read: false,
        is_dismissed: false,
        created_at: new Date().toISOString(),
        show_popup: true,
        play_sound: true,
        actions: [
          {
            id: 'view_achievement',
            label: 'View Achievement',
            action: 'navigate',
            data: { path: '/student/achievements' },
            style: 'primary'
          }
        ]
      },
      {
        id: '2',
        type: NotificationType.LEVEL_UP,
        category: NotificationCategory.ACHIEVEMENT,
        priority: NotificationPriority.HIGH,
        title: '⬆️ Level Up!',
        message: 'Congratulations! You reached level 5!',
        icon: '⬆️',
        color: '#4CAF50',
        data: {
          level: 5,
          experience_gained: 500,
          character_name: 'Alex'
        },
        user_id: 'user1',
        is_read: false,
        is_dismissed: false,
        created_at: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
        show_popup: true,
        play_sound: true
      },
      {
        id: '3',
        type: NotificationType.FRIEND_REQUEST,
        category: NotificationCategory.SOCIAL,
        priority: NotificationPriority.MEDIUM,
        title: '👥 Friend Request',
        message: 'Emma wants to be your friend!',
        icon: '👥',
        color: '#2196F3',
        data: {
          friend_id: 'friend1',
          character_name: 'Emma',
          avatar_url: '/avatars/emma.png'
        },
        user_id: 'user1',
        is_read: false,
        is_dismissed: false,
        created_at: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        show_popup: false,
        actions: [
          {
            id: 'accept_friend',
            label: 'Accept',
            action: 'api_call',
            data: { method: 'POST', url: '/api/friends/accept' },
            style: 'success'
          },
          {
            id: 'decline_friend',
            label: 'Decline',
            action: 'api_call',
            data: { method: 'POST', url: '/api/friends/decline' },
            style: 'secondary'
          }
        ]
      }
    ];
  }
}

export const notificationService = new NotificationService();
export default notificationService;