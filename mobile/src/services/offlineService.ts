import AsyncStorage from '@react-native-async-storage/async-storage';
import { characterService } from './characterService';
import type { Character, CharacterStats } from '../types/Character';
import NetInfo from '@react-native-community/netinfo';
import { logger } from '../utils/logger';

interface OfflineAction {
  id: string;
  type: string;
  payload: any;
  timestamp: number;
}

class OfflineService {
  private queueKey = 'offline_actions_queue';
  private isProcessing = false;

  async addToQueue(action: Omit<OfflineAction, 'id' | 'timestamp'>): Promise<void> {
    try {
      const queue = await this.getQueue();
      const newAction: OfflineAction = {
        ...action,
        id: Date.now().toString(),
        timestamp: Date.now(),
      };
      
      queue.push(newAction);
      await AsyncStorage.setItem(this.queueKey, JSON.stringify(queue));
    } catch (error) {
      logger.error('Failed to add action to offline queue', error);
    }
  }

  async getQueue(): Promise<OfflineAction[]> {
    try {
      const queueString = await AsyncStorage.getItem(this.queueKey);
      return queueString ? JSON.parse(queueString) : [];
    } catch (error) {
      logger.error('Failed to get offline queue', error);
      return [];
    }
  }

  async clearQueue(): Promise<void> {
    try {
      await AsyncStorage.removeItem(this.queueKey);
    } catch (error) {
      logger.error('Failed to clear offline queue', error);
    }
  }

  async removeFromQueue(actionId: string): Promise<void> {
    try {
      const queue = await this.getQueue();
      const filteredQueue = queue.filter(action => action.id !== actionId);
      await AsyncStorage.setItem(this.queueKey, JSON.stringify(filteredQueue));
    } catch (error) {
      logger.error('Failed to remove action from offline queue', error);
    }
  }

  async processQueue(): Promise<void> {
    if (this.isProcessing) return;
    
    this.isProcessing = true;
    
    try {
      const queue = await this.getQueue();
      
      for (const action of queue) {
        try {
          await this.processAction(action);
          await this.removeFromQueue(action.id);
        } catch (error) {
          logger.error('Failed to process offline action', error, { action });
          // Keep action in queue for retry
        }
      }
    } catch (error) {
      logger.error('Failed to process offline queue', error);
    } finally {
      this.isProcessing = false;
    }
  }

  private async processAction(action: OfflineAction): Promise<void> {
    // Process different types of offline actions
    switch (action.type) {
      case 'SYNC_CHARACTER':
        await this.syncCharacter(action.payload);
        break;
      case 'SYNC_QUEST_PROGRESS':
        await this.syncQuestProgress(action.payload);
        break;
      case 'SYNC_ACHIEVEMENT':
        await this.syncAchievement(action.payload);
        break;
      default:
        logger.warn('Unknown offline action type', { type: action.type });
    }
  }

  private async syncCharacter(payload: any): Promise<void> {
    try {
      // Check network connectivity
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        throw new Error('No network connection');
      }

      // Extract character data from payload
      const { characterId, updates } = payload;
      
      if (updates.stats) {
        // Sync character stats
        await characterService.updateStats(updates.stats);
      }
      
      if (updates.experience) {
        // Sync experience gain
        await characterService.gainExperience(updates.experience);
      }
      
      if (updates.level) {
        // Sync level up
        await characterService.levelUp();
      }
      
      if (updates.equipment) {
        // Sync equipment changes
        for (const item of updates.equipment.equip || []) {
          await characterService.equipItem(item.itemId);
        }
        for (const item of updates.equipment.unequip || []) {
          await characterService.unequipItem(item.itemId);
        }
      }
      
      if (updates.appearance) {
        // Sync appearance changes
        await characterService.updateAppearance(updates.appearance);
      }
      
      // Clear local cached character data after successful sync
      await this.removeOfflineData(`character_${characterId}`);
      
    } catch (error) {
      logger.error('Failed to sync character', error, { characterId: payload.characterId });
      throw error; // Re-throw to keep in queue for retry
    }
  }

  private async syncQuestProgress(payload: any): Promise<void> {
    try {
      // Check network connectivity
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        throw new Error('No network connection');
      }

      const { questId, updates } = payload;
      const baseUrl = 'http://localhost:8000/api';
      
      // Get stored auth token
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        throw new Error('No authentication token');
      }
      
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      };
      
      if (updates.start) {
        // Start quest
        const response = await fetch(`${baseUrl}/quests/${questId}/start`, {
          method: 'POST',
          headers,
        });
        
        if (!response.ok) {
          throw new Error(`Failed to start quest: ${response.statusText}`);
        }
      }
      
      if (updates.progress !== undefined) {
        // Update quest progress
        const response = await fetch(`${baseUrl}/quests/${questId}/progress`, {
          method: 'PUT',
          headers,
          body: JSON.stringify({ progress: updates.progress }),
        });
        
        if (!response.ok) {
          throw new Error(`Failed to update quest progress: ${response.statusText}`);
        }
      }
      
      if (updates.complete) {
        // Complete quest
        const response = await fetch(`${baseUrl}/quests/${questId}/complete`, {
          method: 'POST',
          headers,
        });
        
        if (!response.ok) {
          throw new Error(`Failed to complete quest: ${response.statusText}`);
        }
      }
      
      // Clear local cached quest data after successful sync
      await this.removeOfflineData(`quest_${questId}`);
      
    } catch (error) {
      logger.error('Failed to sync quest progress', error, { questId: payload.questId });
      throw error; // Re-throw to keep in queue for retry
    }
  }

  private async syncAchievement(payload: any): Promise<void> {
    try {
      // Check network connectivity
      const netInfo = await NetInfo.fetch();
      if (!netInfo.isConnected) {
        throw new Error('No network connection');
      }

      const { achievementId, updates } = payload;
      const baseUrl = 'http://localhost:8000/api';
      
      // Get stored auth token
      const token = await AsyncStorage.getItem('userToken');
      if (!token) {
        throw new Error('No authentication token');
      }
      
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      };
      
      if (updates.unlock) {
        // Unlock achievement
        const response = await fetch(`${baseUrl}/achievements/${achievementId}/unlock`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            unlockedAt: updates.unlockedAt || new Date().toISOString(),
            progress: updates.progress || 100,
          }),
        });
        
        if (!response.ok) {
          throw new Error(`Failed to unlock achievement: ${response.statusText}`);
        }
      }
      
      if (updates.progress !== undefined && !updates.unlock) {
        // Update achievement progress (for progressive achievements)
        const response = await fetch(`${baseUrl}/achievements/${achievementId}/progress`, {
          method: 'PUT',
          headers,
          body: JSON.stringify({ progress: updates.progress }),
        });
        
        if (!response.ok) {
          throw new Error(`Failed to update achievement progress: ${response.statusText}`);
        }
      }
      
      // Clear local cached achievement data after successful sync
      await this.removeOfflineData(`achievement_${achievementId}`);
      
    } catch (error) {
      logger.error('Failed to sync achievement', error, { achievementId: payload.achievementId });
      throw error; // Re-throw to keep in queue for retry
    }
  }

  async getOfflineData(key: string): Promise<any> {
    try {
      const data = await AsyncStorage.getItem(`offline_${key}`);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      logger.error('Failed to get offline data', error, { key });
      return null;
    }
  }

  async setOfflineData(key: string, data: any): Promise<void> {
    try {
      await AsyncStorage.setItem(`offline_${key}`, JSON.stringify(data));
    } catch (error) {
      logger.error('Failed to set offline data', error, { key });
    }
  }

  async removeOfflineData(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(`offline_${key}`);
    } catch (error) {
      logger.error('Failed to remove offline data', error, { key });
    }
  }
}

export const offlineService = new OfflineService();

export const initializeOfflineSync = async (): Promise<void> => {
  logger.info('Offline sync service initialized');
  
  // Set up network state listener
  NetInfo.addEventListener(state => {
    if (state.isConnected && state.isInternetReachable) {
      logger.info('Network restored, processing offline queue');
      // Process pending actions when network is available
      offlineService.processQueue().catch(error => {
        logger.error('Failed to process offline queue on network reconnect', error);
      });
    }
  });
  
  // Process any pending offline actions
  await offlineService.processQueue();
};

// Helper functions for offline data management
export const saveCharacterOffline = async (characterId: string, updates: any): Promise<void> => {
  const existingData = await offlineService.getOfflineData(`character_${characterId}`) || {};
  const mergedData = {
    ...existingData,
    ...updates,
    lastUpdated: Date.now(),
  };
  
  await offlineService.setOfflineData(`character_${characterId}`, mergedData);
  await offlineService.addToQueue({
    type: 'SYNC_CHARACTER',
    payload: { characterId, updates: mergedData },
  });
};

export const saveQuestProgressOffline = async (questId: string, updates: any): Promise<void> => {
  const existingData = await offlineService.getOfflineData(`quest_${questId}`) || {};
  const mergedData = {
    ...existingData,
    ...updates,
    lastUpdated: Date.now(),
  };
  
  await offlineService.setOfflineData(`quest_${questId}`, mergedData);
  await offlineService.addToQueue({
    type: 'SYNC_QUEST_PROGRESS',
    payload: { questId, updates: mergedData },
  });
};

export const saveAchievementOffline = async (achievementId: string, updates: any): Promise<void> => {
  const existingData = await offlineService.getOfflineData(`achievement_${achievementId}`) || {};
  const mergedData = {
    ...existingData,
    ...updates,
    lastUpdated: Date.now(),
  };
  
  await offlineService.setOfflineData(`achievement_${achievementId}`, mergedData);
  await offlineService.addToQueue({
    type: 'SYNC_ACHIEVEMENT',
    payload: { achievementId, updates: mergedData },
  });
};

// Function to check if device is offline
export const isOffline = async (): Promise<boolean> => {
  const netInfo = await NetInfo.fetch();
  return !netInfo.isConnected || !netInfo.isInternetReachable;
};