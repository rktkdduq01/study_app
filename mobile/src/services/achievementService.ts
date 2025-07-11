import AsyncStorage from '@react-native-async-storage/async-storage';
import { isOffline, saveAchievementOffline } from './offlineService';

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  type: string;
  rarity: string;
  xp_reward: number;
  unlocked: boolean;
  unlocked_at?: string;
  progress?: number;
  max_progress?: number;
  category: string;
  requirements?: any;
}

const API_BASE_URL = 'http://localhost:8000/api';

class AchievementService {
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

  async getAchievements(): Promise<Achievement[]> {
    const offline = await isOffline();
    
    if (offline) {
      const cachedAchievements = await AsyncStorage.getItem('cached_achievements');
      if (cachedAchievements) {
        return JSON.parse(cachedAchievements);
      }
      return [];
    }
    
    const response = await this.makeRequest('/achievements');
    const achievements = await response.json();
    
    // Cache for offline use
    await AsyncStorage.setItem('cached_achievements', JSON.stringify(achievements));
    
    return achievements;
  }

  async unlockAchievement(achievementId: string): Promise<Achievement> {
    const offline = await isOffline();
    
    if (offline) {
      await saveAchievementOffline(achievementId, {
        unlock: true,
        unlockedAt: new Date().toISOString(),
        progress: 100,
      });
      
      // Update local cache
      const cachedAchievements = await AsyncStorage.getItem('cached_achievements');
      if (cachedAchievements) {
        const achievements = JSON.parse(cachedAchievements);
        const achievementIndex = achievements.findIndex((a: Achievement) => a.id === achievementId);
        if (achievementIndex !== -1) {
          achievements[achievementIndex].unlocked = true;
          achievements[achievementIndex].unlocked_at = new Date().toISOString();
          achievements[achievementIndex].progress = achievements[achievementIndex].max_progress || 100;
          await AsyncStorage.setItem('cached_achievements', JSON.stringify(achievements));
          return achievements[achievementIndex];
        }
      }
      throw new Error('Achievement not found offline');
    }
    
    const response = await this.makeRequest(`/achievements/${achievementId}/unlock`, {
      method: 'POST',
      body: JSON.stringify({
        unlockedAt: new Date().toISOString(),
        progress: 100,
      }),
    });
    return await response.json();
  }

  async updateAchievementProgress(achievementId: string, progress: number): Promise<Achievement> {
    const offline = await isOffline();
    
    if (offline) {
      await saveAchievementOffline(achievementId, { progress });
      
      // Update local cache
      const cachedAchievements = await AsyncStorage.getItem('cached_achievements');
      if (cachedAchievements) {
        const achievements = JSON.parse(cachedAchievements);
        const achievementIndex = achievements.findIndex((a: Achievement) => a.id === achievementId);
        if (achievementIndex !== -1) {
          achievements[achievementIndex].progress = progress;
          
          // Auto-unlock if progress reaches max
          if (achievements[achievementIndex].max_progress && 
              progress >= achievements[achievementIndex].max_progress) {
            achievements[achievementIndex].unlocked = true;
            achievements[achievementIndex].unlocked_at = new Date().toISOString();
            
            // Also save the unlock to offline queue
            await saveAchievementOffline(achievementId, {
              unlock: true,
              unlockedAt: new Date().toISOString(),
              progress,
            });
          }
          
          await AsyncStorage.setItem('cached_achievements', JSON.stringify(achievements));
          return achievements[achievementIndex];
        }
      }
      throw new Error('Achievement not found offline');
    }
    
    const response = await this.makeRequest(`/achievements/${achievementId}/progress`, {
      method: 'PUT',
      body: JSON.stringify({ progress }),
    });
    return await response.json();
  }

  async getUnlockedAchievements(): Promise<Achievement[]> {
    const achievements = await this.getAchievements();
    return achievements.filter(achievement => achievement.unlocked);
  }

  async getLockedAchievements(): Promise<Achievement[]> {
    const achievements = await this.getAchievements();
    return achievements.filter(achievement => !achievement.unlocked);
  }

  async getAchievementsByCategory(category: string): Promise<Achievement[]> {
    const achievements = await this.getAchievements();
    return achievements.filter(achievement => achievement.category === category);
  }

  async getAchievementProgress(): Promise<{
    total: number;
    unlocked: number;
    percentage: number;
  }> {
    const achievements = await this.getAchievements();
    const unlockedCount = achievements.filter(a => a.unlocked).length;
    
    return {
      total: achievements.length,
      unlocked: unlockedCount,
      percentage: achievements.length > 0 ? (unlockedCount / achievements.length) * 100 : 0,
    };
  }
}

export const achievementService = new AchievementService();