import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Notification {
  id: string;
  title: string;
  body: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'achievement';
  timestamp: string;
  read: boolean;
  data?: any;
}

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  pushEnabled: boolean;
  soundEnabled: boolean;
  vibrationEnabled: boolean;
}

const initialState: NotificationState = {
  notifications: [],
  unreadCount: 0,
  pushEnabled: true,
  soundEnabled: true,
  vibrationEnabled: true,
};

const notificationSlice = createSlice({
  name: 'notification',
  initialState,
  reducers: {
    addNotification: (state, action: PayloadAction<Notification>) => {
      state.notifications.unshift(action.payload);
      if (!action.payload.read) {
        state.unreadCount += 1;
      }
      
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },
    markAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification && !notification.read) {
        notification.read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
    },
    markAllAsRead: (state) => {
      state.notifications.forEach(notification => {
        notification.read = true;
      });
      state.unreadCount = 0;
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      const index = state.notifications.findIndex(n => n.id === action.payload);
      if (index !== -1) {
        const notification = state.notifications[index];
        if (!notification.read) {
          state.unreadCount = Math.max(0, state.unreadCount - 1);
        }
        state.notifications.splice(index, 1);
      }
    },
    clearAllNotifications: (state) => {
      state.notifications = [];
      state.unreadCount = 0;
    },
    setPushEnabled: (state, action: PayloadAction<boolean>) => {
      state.pushEnabled = action.payload;
    },
    setSoundEnabled: (state, action: PayloadAction<boolean>) => {
      state.soundEnabled = action.payload;
    },
    setVibrationEnabled: (state, action: PayloadAction<boolean>) => {
      state.vibrationEnabled = action.payload;
    },
    updateNotificationSettings: (
      state,
      action: PayloadAction<Partial<{
        pushEnabled: boolean;
        soundEnabled: boolean;
        vibrationEnabled: boolean;
      }>>
    ) => {
      if (action.payload.pushEnabled !== undefined) {
        state.pushEnabled = action.payload.pushEnabled;
      }
      if (action.payload.soundEnabled !== undefined) {
        state.soundEnabled = action.payload.soundEnabled;
      }
      if (action.payload.vibrationEnabled !== undefined) {
        state.vibrationEnabled = action.payload.vibrationEnabled;
      }
    },
  },
});

export const {
  addNotification,
  markAsRead,
  markAllAsRead,
  removeNotification,
  clearAllNotifications,
  setPushEnabled,
  setSoundEnabled,
  setVibrationEnabled,
  updateNotificationSettings,
} = notificationSlice.actions;

export default notificationSlice.reducer;