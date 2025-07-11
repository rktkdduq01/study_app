import { initializeNotifications } from '../services/notificationService';
import { initializeNetworkListener } from '../services/networkService';
import { initializeOfflineSync } from '../services/offlineService';
import { logger } from './logger';

export const initializeApp = async (): Promise<void> => {
  try {
    // Initialize all required services
    await Promise.all([
      initializeNotifications(),
      initializeNetworkListener(),
      initializeOfflineSync(),
    ]);
    
    logger.info('App initialized successfully');
  } catch (error) {
    logger.error('Failed to initialize app', error);
    throw error;
  }
};