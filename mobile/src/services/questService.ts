import AsyncStorage from '@react-native-async-storage/async-storage';
import { isOffline, saveQuestProgressOffline } from './offlineService';

export interface Quest {
  id: string;
  title: string;
  description: string;
  type: string;
  subject: string;
  difficulty: string;
  xp_reward: number;
  status: 'available' | 'active' | 'completed';
  progress: number;
  max_progress: number;
  prerequisites: string[];
  rewards: any[];
}

const API_BASE_URL = 'http://localhost:8000/api';

class QuestService {
  private async makeRequest(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<Response> {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = await AsyncStorage.getItem('userToken');
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return response;
  }

  async getQuests(): Promise<Quest[]> {
    const offline = await isOffline();
    
    if (offline) {
      const cachedQuests = await AsyncStorage.getItem('cached_quests');
      if (cachedQuests) {
        return JSON.parse(cachedQuests);
      }
      return [];
    }
    
    const response = await this.makeRequest('/quests');
    const quests = await response.json();
    
    // Cache for offline use
    await AsyncStorage.setItem('cached_quests', JSON.stringify(quests));
    
    return quests;
  }

  async startQuest(questId: string): Promise<Quest> {
    const offline = await isOffline();
    
    if (offline) {
      await saveQuestProgressOffline(questId, { start: true, startedAt: Date.now() });
      
      // Update local cache
      const cachedQuests = await AsyncStorage.getItem('cached_quests');
      if (cachedQuests) {
        const quests = JSON.parse(cachedQuests);
        const questIndex = quests.findIndex((q: Quest) => q.id === questId);
        if (questIndex !== -1) {
          quests[questIndex].status = 'active';
          await AsyncStorage.setItem('cached_quests', JSON.stringify(quests));
          return quests[questIndex];
        }
      }
      throw new Error('Quest not found offline');
    }
    
    const response = await this.makeRequest(`/quests/${questId}/start`, {
      method: 'POST',
    });
    return await response.json();
  }

  async updateQuestProgress(questId: string, progress: number): Promise<Quest> {
    const offline = await isOffline();
    
    if (offline) {
      await saveQuestProgressOffline(questId, { progress, updatedAt: Date.now() });
      
      // Update local cache
      const cachedQuests = await AsyncStorage.getItem('cached_quests');
      if (cachedQuests) {
        const quests = JSON.parse(cachedQuests);
        const questIndex = quests.findIndex((q: Quest) => q.id === questId);
        if (questIndex !== -1) {
          quests[questIndex].progress = progress;
          await AsyncStorage.setItem('cached_quests', JSON.stringify(quests));
          return quests[questIndex];
        }
      }
      throw new Error('Quest not found offline');
    }
    
    const response = await this.makeRequest(`/quests/${questId}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ progress }),
    });
    return await response.json();
  }

  async completeQuest(questId: string): Promise<{
    quest: Quest;
    rewards: any[];
    experience_gained: number;
  }> {
    const offline = await isOffline();
    
    if (offline) {
      await saveQuestProgressOffline(questId, { complete: true, completedAt: Date.now() });
      
      // Update local cache
      const cachedQuests = await AsyncStorage.getItem('cached_quests');
      if (cachedQuests) {
        const quests = JSON.parse(cachedQuests);
        const questIndex = quests.findIndex((q: Quest) => q.id === questId);
        if (questIndex !== -1) {
          quests[questIndex].status = 'completed';
          quests[questIndex].progress = quests[questIndex].max_progress;
          await AsyncStorage.setItem('cached_quests', JSON.stringify(quests));
          
          return {
            quest: quests[questIndex],
            rewards: quests[questIndex].rewards || [],
            experience_gained: quests[questIndex].xp_reward || 0,
          };
        }
      }
      throw new Error('Quest not found offline');
    }
    
    const response = await this.makeRequest(`/quests/${questId}/complete`, {
      method: 'POST',
    });
    return await response.json();
  }

  async getActiveQuests(): Promise<Quest[]> {
    const quests = await this.getQuests();
    return quests.filter(quest => quest.status === 'active');
  }

  async getCompletedQuests(): Promise<Quest[]> {
    const quests = await this.getQuests();
    return quests.filter(quest => quest.status === 'completed');
  }

  async getAvailableQuests(): Promise<Quest[]> {
    const quests = await this.getQuests();
    return quests.filter(quest => quest.status === 'available');
  }
}

export const questService = new QuestService();