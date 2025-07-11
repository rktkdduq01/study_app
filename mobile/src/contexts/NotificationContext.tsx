import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store/store';
import { notificationService } from '../services/notificationService';
import { addNotification } from '../store/slices/notificationSlice';

interface NotificationContextType {
  requestPermission: () => Promise<boolean>;
  scheduleNotification: (title: string, body: string, date: Date) => Promise<void>;
  cancelNotification: (id: string) => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    // Set up notification listeners
    const setupNotifications = async () => {
      try {
        await notificationService.initialize();
        
        // Listen for notification events
        notificationService.onNotificationReceived((notification) => {
          dispatch(addNotification({
            id: Date.now().toString(),
            title: notification.title,
            body: notification.body,
            type: 'info',
            timestamp: new Date().toISOString(),
            read: false,
          }));
        });
      } catch (error) {
        console.error('Failed to setup notifications:', error);
      }
    };

    setupNotifications();
  }, [dispatch]);

  const requestPermission = async (): Promise<boolean> => {
    try {
      return await notificationService.requestPermission();
    } catch (error) {
      console.error('Failed to request notification permission:', error);
      return false;
    }
  };

  const scheduleNotification = async (title: string, body: string, date: Date): Promise<void> => {
    try {
      await notificationService.scheduleNotification(title, body, date);
    } catch (error) {
      console.error('Failed to schedule notification:', error);
    }
  };

  const cancelNotification = async (id: string): Promise<void> => {
    try {
      await notificationService.cancelNotification(id);
    } catch (error) {
      console.error('Failed to cancel notification:', error);
    }
  };

  const value: NotificationContextType = {
    requestPermission,
    scheduleNotification,
    cancelNotification,
  };

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};