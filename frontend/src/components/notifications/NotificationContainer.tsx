import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import {
  addNotification,
  setConnectionStatus,
  updateOnlineUser,
  updateTypingIndicator,
  connectNotificationWebSocket,
  fetchNotificationSettings,
  loadPendingNotifications,
} from '../../store/slices/notificationSlice';
import notificationService from '../../services/notificationService';
import type { Notification, OnlineStatus, TypingIndicator, LiveUpdate } from '../../types/notification';
import NotificationPanel from './NotificationPanel';
import NotificationPopup from './NotificationPopup';

const NotificationContainer: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);
  const { soundEnabled, vibrationEnabled } = useAppSelector((state) => state.notifications);
  const [currentPopupNotification, setCurrentPopupNotification] = useState<Notification | null>(null);

  // Initialize notification system
  useEffect(() => {
    if (!isAuthenticated || !user) return;

    // Load settings and pending notifications
    dispatch(fetchNotificationSettings());
    dispatch(loadPendingNotifications());

    // Connect WebSocket for real-time notifications
    const token = localStorage.getItem('token');
    if (token) {
      dispatch(connectNotificationWebSocket({ userId: String(user.id), token }));
    }

    // Set up WebSocket event handlers
    const setupEventHandlers = () => {
      // Connection status
      notificationService.on('connection_status', (data: { connected: boolean; error?: string }) => {
        dispatch(setConnectionStatus(data));
      });

      // New notification
      notificationService.on('new_notification', (notification: Notification) => {
        dispatch(addNotification(notification));
        
        // Show popup if enabled
        if (notification.show_popup) {
          setCurrentPopupNotification(notification);
        }
      });

      // Notification read status
      notificationService.on('notification_read', (data: { notification_id: string; user_id: string }) => {
        // Handle read status update if needed
        console.log('Notification read:', data);
      });

      // Bulk actions
      notificationService.on('bulk_action', (data: { action: string; category?: string; user_id: string }) => {
        // Handle bulk actions if needed
        console.log('Bulk action:', data);
      });

      // Online status updates
      notificationService.on('online_status', (status: OnlineStatus) => {
        dispatch(updateOnlineUser(status));
      });

      // Typing indicators
      notificationService.on('typing_indicator', (typing: TypingIndicator) => {
        dispatch(updateTypingIndicator(typing));
      });

      // Live updates
      notificationService.on('live_update', (update: LiveUpdate) => {
        console.log('Live update:', update);
        // Handle live updates (leaderboard changes, etc.)
      });
    };

    setupEventHandlers();

    // Request browser notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      notificationService.requestNotificationPermission().catch(console.warn);
    }

    // Cleanup on unmount
    return () => {
      notificationService.disconnect();
    };
  }, [isAuthenticated, user, dispatch]);

  // Update online status periodically
  useEffect(() => {
    if (!isAuthenticated || !notificationService.isSocketConnected()) return;

    const updateInterval = setInterval(() => {
      notificationService.updateOnlineStatus(
        'browsing', // current activity
        window.location.pathname // current location
      );
    }, 30000); // every 30 seconds

    return () => clearInterval(updateInterval);
  }, [isAuthenticated]);

  // Handle page visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!isAuthenticated || !notificationService.isSocketConnected()) return;

      if (document.hidden) {
        notificationService.updateOnlineStatus('away');
      } else {
        notificationService.updateOnlineStatus('browsing', window.location.pathname);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [isAuthenticated]);

  // Handle beforeunload to update status
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (notificationService.isSocketConnected()) {
        notificationService.updateOnlineStatus('offline');
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, []);

  const handlePopupClose = () => {
    setCurrentPopupNotification(null);
  };

  return (
    <>
      {/* Notification Panel */}
      <NotificationPanel />
      
      {/* Notification Popup */}
      <NotificationPopup
        notification={currentPopupNotification}
        onClose={handlePopupClose}
        autoHideDuration={5000}
        position={{ vertical: 'top', horizontal: 'right' }}
      />
    </>
  );
};

export default NotificationContainer;