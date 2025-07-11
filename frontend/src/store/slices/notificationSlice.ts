import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import type {
  Notification,
  NotificationSettings,
  NotificationListResponse,
  NotificationStatsResponse,
  OnlineStatus,
  TypingIndicator,
  LiveUpdate,
  NotificationGroup
} from '../../types/notification';
import {
  NotificationCategory,
  NotificationPriority,
  NotificationType
} from '../../types/notification';
import notificationService from '../../services/notificationService';

interface NotificationState {
  // Notifications
  notifications: Notification[];
  groups: NotificationGroup[];
  loading: boolean;
  error: string | null;
  hasMore: boolean;
  nextCursor: string | null;
  
  // Stats
  totalCount: number;
  unreadCount: number;
  categoryStats: Record<NotificationCategory, { total: number; unread: number }>;
  
  // Settings
  settings: NotificationSettings | null;
  settingsLoading: boolean;
  
  // WebSocket connection
  isConnected: boolean;
  connectionError: string | null;
  
  // Real-time features
  onlineUsers: Record<string, OnlineStatus>;
  typingIndicators: Record<string, TypingIndicator[]>;
  
  // UI state
  notificationPanelOpen: boolean;
  selectedCategory: NotificationCategory | null;
  searchQuery: string;
  filterPriority: NotificationPriority | null;
  
  // Sound and vibration preferences
  soundEnabled: boolean;
  vibrationEnabled: boolean;
  
  // Pending actions (for offline support)
  pendingActions: Array<{
    action: string;
    data: any;
    timestamp: string;
  }>;
}

const initialState: NotificationState = {
  notifications: [],
  groups: [],
  loading: false,
  error: null,
  hasMore: true,
  nextCursor: null,
  
  totalCount: 0,
  unreadCount: 0,
  categoryStats: {
    [NotificationCategory.ACHIEVEMENT]: { total: 0, unread: 0 },
    [NotificationCategory.SOCIAL]: { total: 0, unread: 0 },
    [NotificationCategory.COMPETITION]: { total: 0, unread: 0 },
    [NotificationCategory.SHOP]: { total: 0, unread: 0 },
    [NotificationCategory.LEARNING]: { total: 0, unread: 0 },
    [NotificationCategory.SYSTEM]: { total: 0, unread: 0 },
    [NotificationCategory.PARENT]: { total: 0, unread: 0 }
  },
  
  settings: null,
  settingsLoading: false,
  
  isConnected: false,
  connectionError: null,
  
  onlineUsers: {},
  typingIndicators: {},
  
  notificationPanelOpen: false,
  selectedCategory: null,
  searchQuery: '',
  filterPriority: null,
  
  soundEnabled: true,
  vibrationEnabled: true,
  
  pendingActions: []
};

// Async thunks
export const fetchNotifications = createAsyncThunk(
  'notifications/fetchNotifications',
  async ({ cursor, limit = 20 }: { cursor?: string; limit?: number } = {}) => {
    return await notificationService.fetchNotifications(cursor, limit);
  }
);

export const markAsRead = createAsyncThunk(
  'notifications/markAsRead',
  async (notificationId: string) => {
    await notificationService.markAsRead(notificationId);
    return notificationId;
  }
);

export const markAllAsRead = createAsyncThunk(
  'notifications/markAllAsRead',
  async (category?: NotificationCategory) => {
    await notificationService.markAllAsRead(category);
    return category;
  }
);

export const dismissNotification = createAsyncThunk(
  'notifications/dismissNotification',
  async (notificationId: string) => {
    await notificationService.dismissNotification(notificationId);
    return notificationId;
  }
);

export const clearAllNotifications = createAsyncThunk(
  'notifications/clearAll',
  async (category?: NotificationCategory) => {
    await notificationService.clearAll(category);
    return category;
  }
);

export const fetchNotificationStats = createAsyncThunk(
  'notifications/fetchStats',
  async () => {
    return await notificationService.getNotificationStats();
  }
);

export const updateNotificationSettings = createAsyncThunk(
  'notifications/updateSettings',
  async (settings: Partial<NotificationSettings>) => {
    await notificationService.updateSettings(settings);
    return settings;
  }
);

export const fetchNotificationSettings = createAsyncThunk(
  'notifications/fetchSettings',
  async () => {
    return await notificationService.getSettings();
  }
);

export const connectNotificationWebSocket = createAsyncThunk(
  'notifications/connectWebSocket',
  async ({ userId, token }: { userId: string; token: string }) => {
    await notificationService.connect(userId, token);
    return { userId, connected: true };
  }
);

const notificationSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    // Real-time notification handling
    addNotification: (state, action: PayloadAction<Notification>) => {
      const notification = action.payload;
      
      // Check if notification already exists
      const existingIndex = state.notifications.findIndex(n => n.id === notification.id);
      if (existingIndex === -1) {
        state.notifications.unshift(notification);
        state.totalCount += 1;
        
        if (!notification.is_read) {
          state.unreadCount += 1;
          state.categoryStats[notification.category].unread += 1;
        }
        state.categoryStats[notification.category].total += 1;
      }
    },
    
    // Mark notification as read
    markNotificationAsRead: (state, action: PayloadAction<string>) => {
      const notificationId = action.payload;
      const notification = state.notifications.find(n => n.id === notificationId);
      
      if (notification && !notification.is_read) {
        notification.is_read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
        state.categoryStats[notification.category].unread = Math.max(0, 
          state.categoryStats[notification.category].unread - 1
        );
      }
    },
    
    // Dismiss notification
    dismissNotificationById: (state, action: PayloadAction<string>) => {
      const notificationId = action.payload;
      const index = state.notifications.findIndex(n => n.id === notificationId);
      
      if (index !== -1) {
        const notification = state.notifications[index];
        if (!notification.is_read) {
          state.unreadCount = Math.max(0, state.unreadCount - 1);
          state.categoryStats[notification.category].unread = Math.max(0,
            state.categoryStats[notification.category].unread - 1
          );
        }
        
        state.notifications.splice(index, 1);
        state.totalCount = Math.max(0, state.totalCount - 1);
        state.categoryStats[notification.category].total = Math.max(0,
          state.categoryStats[notification.category].total - 1
        );
      }
    },
    
    // WebSocket connection status
    setConnectionStatus: (state, action: PayloadAction<{ connected: boolean; error?: string }>) => {
      state.isConnected = action.payload.connected;
      state.connectionError = action.payload.error || null;
    },
    
    // Online users management
    updateOnlineUser: (state, action: PayloadAction<OnlineStatus>) => {
      const user = action.payload;
      if (user.is_online) {
        state.onlineUsers[user.user_id] = user;
      } else {
        delete state.onlineUsers[user.user_id];
      }
    },
    
    // Typing indicators
    updateTypingIndicator: (state, action: PayloadAction<TypingIndicator>) => {
      const typing = action.payload;
      const location = typing.location;
      
      if (!state.typingIndicators[location]) {
        state.typingIndicators[location] = [];
      }
      
      const existingIndex = state.typingIndicators[location].findIndex(
        t => t.user_id === typing.user_id
      );
      
      if (typing.is_typing) {
        if (existingIndex === -1) {
          state.typingIndicators[location].push(typing);
        } else {
          state.typingIndicators[location][existingIndex] = typing;
        }
      } else {
        if (existingIndex !== -1) {
          state.typingIndicators[location].splice(existingIndex, 1);
        }
      }
      
      // Clean up empty locations
      if (state.typingIndicators[location].length === 0) {
        delete state.typingIndicators[location];
      }
    },
    
    // UI state management
    toggleNotificationPanel: (state) => {
      state.notificationPanelOpen = !state.notificationPanelOpen;
    },
    
    setNotificationPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.notificationPanelOpen = action.payload;
    },
    
    setSelectedCategory: (state, action: PayloadAction<NotificationCategory | null>) => {
      state.selectedCategory = action.payload;
    },
    
    setSearchQuery: (state, action: PayloadAction<string>) => {
      state.searchQuery = action.payload;
    },
    
    setFilterPriority: (state, action: PayloadAction<NotificationPriority | null>) => {
      state.filterPriority = action.payload;
    },
    
    // Settings
    setSoundEnabled: (state, action: PayloadAction<boolean>) => {
      state.soundEnabled = action.payload;
    },
    
    setVibrationEnabled: (state, action: PayloadAction<boolean>) => {
      state.vibrationEnabled = action.payload;
    },
    
    // Bulk actions
    markAllInCategoryAsRead: (state, action: PayloadAction<NotificationCategory | undefined>) => {
      const category = action.payload;
      
      state.notifications.forEach(notification => {
        if ((!category || notification.category === category) && !notification.is_read) {
          notification.is_read = true;
        }
      });
      
      if (category) {
        state.unreadCount -= state.categoryStats[category].unread;
        state.categoryStats[category].unread = 0;
      } else {
        state.unreadCount = 0;
        Object.keys(state.categoryStats).forEach(cat => {
          state.categoryStats[cat as NotificationCategory].unread = 0;
        });
      }
    },
    
    clearAllInCategory: (state, action: PayloadAction<NotificationCategory | undefined>) => {
      const category = action.payload;
      
      if (category) {
        const categoryNotifications = state.notifications.filter(n => n.category === category);
        const unreadInCategory = categoryNotifications.filter(n => !n.is_read).length;
        
        state.notifications = state.notifications.filter(n => n.category !== category);
        state.totalCount -= categoryNotifications.length;
        state.unreadCount -= unreadInCategory;
        state.categoryStats[category] = { total: 0, unread: 0 };
      } else {
        state.notifications = [];
        state.totalCount = 0;
        state.unreadCount = 0;
        Object.keys(state.categoryStats).forEach(cat => {
          state.categoryStats[cat as NotificationCategory] = { total: 0, unread: 0 };
        });
      }
    },
    
    // Load pending notifications from localStorage
    loadPendingNotifications: (state) => {
      const pending = notificationService.getPendingNotifications();
      pending.forEach(notification => {
        const existingIndex = state.notifications.findIndex(n => n.id === notification.id);
        if (existingIndex === -1) {
          state.notifications.unshift(notification);
          if (!notification.is_read) {
            state.unreadCount += 1;
            state.categoryStats[notification.category].unread += 1;
          }
          state.totalCount += 1;
          state.categoryStats[notification.category].total += 1;
        }
      });
    },
    
    // Add pending action for offline support
    addPendingAction: (state, action: PayloadAction<{ action: string; data: any }>) => {
      state.pendingActions.push({
        ...action.payload,
        timestamp: new Date().toISOString()
      });
    },
    
    // Clear pending actions
    clearPendingActions: (state) => {
      state.pendingActions = [];
    },
    
    // Reset state
    resetNotifications: (state) => {
      return { ...initialState, settings: state.settings };
    }
  },
  
  extraReducers: (builder) => {
    // Fetch notifications
    builder.addCase(fetchNotifications.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    
    builder.addCase(fetchNotifications.fulfilled, (state, action) => {
      state.loading = false;
      const response = action.payload;
      
      if (state.nextCursor) {
        // Append to existing notifications (pagination)
        state.notifications.push(...response.notifications);
      } else {
        // Replace notifications (initial load)
        state.notifications = response.notifications;
      }
      
      state.groups = response.groups;
      state.totalCount = response.total_count;
      state.unreadCount = response.unread_count;
      state.hasMore = response.has_more;
      state.nextCursor = response.next_cursor || null;
    });
    
    builder.addCase(fetchNotifications.rejected, (state, action) => {
      state.loading = false;
      state.error = action.error.message || 'Failed to fetch notifications';
    });
    
    // Mark as read
    builder.addCase(markAsRead.fulfilled, (state, action) => {
      const notificationId = action.payload;
      const notification = state.notifications.find(n => n.id === notificationId);
      
      if (notification && !notification.is_read) {
        notification.is_read = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
        state.categoryStats[notification.category].unread = Math.max(0,
          state.categoryStats[notification.category].unread - 1
        );
      }
    });
    
    // Mark all as read
    builder.addCase(markAllAsRead.fulfilled, (state, action) => {
      const category = action.payload;
      
      state.notifications.forEach(notification => {
        if ((!category || notification.category === category) && !notification.is_read) {
          notification.is_read = true;
        }
      });
      
      if (category) {
        state.unreadCount -= state.categoryStats[category].unread;
        state.categoryStats[category].unread = 0;
      } else {
        state.unreadCount = 0;
        Object.keys(state.categoryStats).forEach(cat => {
          state.categoryStats[cat as NotificationCategory].unread = 0;
        });
      }
    });
    
    // Dismiss notification
    builder.addCase(dismissNotification.fulfilled, (state, action) => {
      const notificationId = action.payload;
      const index = state.notifications.findIndex(n => n.id === notificationId);
      
      if (index !== -1) {
        const notification = state.notifications[index];
        if (!notification.is_read) {
          state.unreadCount = Math.max(0, state.unreadCount - 1);
          state.categoryStats[notification.category].unread = Math.max(0,
            state.categoryStats[notification.category].unread - 1
          );
        }
        
        state.notifications.splice(index, 1);
        state.totalCount = Math.max(0, state.totalCount - 1);
        state.categoryStats[notification.category].total = Math.max(0,
          state.categoryStats[notification.category].total - 1
        );
      }
    });
    
    // Clear all notifications
    builder.addCase(clearAllNotifications.fulfilled, (state, action) => {
      const category = action.payload;
      
      if (category) {
        const categoryNotifications = state.notifications.filter(n => n.category === category);
        const unreadInCategory = categoryNotifications.filter(n => !n.is_read).length;
        
        state.notifications = state.notifications.filter(n => n.category !== category);
        state.totalCount -= categoryNotifications.length;
        state.unreadCount -= unreadInCategory;
        state.categoryStats[category] = { total: 0, unread: 0 };
      } else {
        state.notifications = [];
        state.totalCount = 0;
        state.unreadCount = 0;
        Object.keys(state.categoryStats).forEach(cat => {
          state.categoryStats[cat as NotificationCategory] = { total: 0, unread: 0 };
        });
      }
    });
    
    // Fetch notification stats
    builder.addCase(fetchNotificationStats.fulfilled, (state, action) => {
      const stats = action.payload;
      state.totalCount = stats.total_count;
      state.unreadCount = stats.unread_count;
      state.categoryStats = stats.category_counts;
    });
    
    // Fetch settings
    builder.addCase(fetchNotificationSettings.pending, (state) => {
      state.settingsLoading = true;
    });
    
    builder.addCase(fetchNotificationSettings.fulfilled, (state, action) => {
      state.settingsLoading = false;
      state.settings = action.payload;
      state.soundEnabled = action.payload.sound_enabled;
      state.vibrationEnabled = action.payload.vibration_enabled;
    });
    
    builder.addCase(fetchNotificationSettings.rejected, (state) => {
      state.settingsLoading = false;
    });
    
    // Update settings
    builder.addCase(updateNotificationSettings.fulfilled, (state, action) => {
      if (state.settings) {
        state.settings = { ...state.settings, ...action.payload };
      }
      
      if (action.payload.sound_enabled !== undefined) {
        state.soundEnabled = action.payload.sound_enabled;
      }
      if (action.payload.vibration_enabled !== undefined) {
        state.vibrationEnabled = action.payload.vibration_enabled;
      }
    });
    
    // Connect WebSocket
    builder.addCase(connectNotificationWebSocket.fulfilled, (state, action) => {
      state.isConnected = true;
      state.connectionError = null;
    });
    
    builder.addCase(connectNotificationWebSocket.rejected, (state, action) => {
      state.isConnected = false;
      state.connectionError = action.error.message || 'Failed to connect to notification service';
    });
  }
});

export const {
  addNotification,
  markNotificationAsRead,
  dismissNotificationById,
  setConnectionStatus,
  updateOnlineUser,
  updateTypingIndicator,
  toggleNotificationPanel,
  setNotificationPanelOpen,
  setSelectedCategory,
  setSearchQuery,
  setFilterPriority,
  setSoundEnabled,
  setVibrationEnabled,
  markAllInCategoryAsRead,
  clearAllInCategory,
  loadPendingNotifications,
  addPendingAction,
  clearPendingActions,
  resetNotifications
} = notificationSlice.actions;

export default notificationSlice.reducer;