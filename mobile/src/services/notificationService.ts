import PushNotification from 'react-native-push-notification';
import { Platform } from 'react-native';

interface NotificationData {
  title: string;
  body: string;
  data?: any;
}

class NotificationService {
  private isInitialized = false;
  private onNotificationReceivedCallback?: (notification: NotificationData) => void;

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    return new Promise((resolve) => {
      PushNotification.configure({
        onNotification: (notification) => {
          if (this.onNotificationReceivedCallback) {
            this.onNotificationReceivedCallback({
              title: notification.title || '',
              body: notification.message || '',
              data: notification.data,
            });
          }
          
          // Handle notification tap
          if (notification.userInteraction) {
            this.handleNotificationTap(notification);
          }
        },
        
        onAction: (notification) => {
          console.log('Notification action:', notification);
        },
        
        onRegistrationError: (err) => {
          console.error('Push notification registration error:', err);
        },
        
        permissions: {
          alert: true,
          badge: true,
          sound: true,
        },
        
        popInitialNotification: true,
        requestPermissions: Platform.OS === 'ios',
      });

      this.isInitialized = true;
      resolve();
    });
  }

  async requestPermission(): Promise<boolean> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return new Promise((resolve) => {
      PushNotification.requestPermissions().then((permissions) => {
        resolve(permissions.alert && permissions.badge && permissions.sound);
      });
    });
  }

  async scheduleNotification(
    title: string,
    body: string,
    date: Date,
    data?: any
  ): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    PushNotification.localNotificationSchedule({
      title,
      message: body,
      date,
      data,
      allowWhileIdle: true,
    });
  }

  async showNotification(
    title: string,
    body: string,
    data?: any
  ): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    PushNotification.localNotification({
      title,
      message: body,
      data,
      playSound: true,
      soundName: 'default',
      vibrate: true,
    });
  }

  async cancelNotification(id: string): Promise<void> {
    PushNotification.cancelLocalNotifications({ id });
  }

  async cancelAllNotifications(): Promise<void> {
    PushNotification.cancelAllLocalNotifications();
  }

  async setBadgeNumber(number: number): Promise<void> {
    PushNotification.setApplicationIconBadgeNumber(number);
  }

  onNotificationReceived(callback: (notification: NotificationData) => void): void {
    this.onNotificationReceivedCallback = callback;
  }

  private handleNotificationTap(notification: any): void {
    console.log('Notification tapped:', notification);
    // Handle navigation or other actions when notification is tapped
  }
}

export const notificationService = new NotificationService();

export const initializeNotifications = async (): Promise<void> => {
  await notificationService.initialize();
};