import api from './api';
import { apiWrapper } from '../utils/apiWrapper';

export interface LevelInfo {
  current: number;
  experience: number;
  progress: number;
  title: string;
}

export interface UserStats {
  gold: number;
  gems: number;
  total_quests: number;
  badges_earned: number;
  items_collected: number;
}

export interface DailyRewardStatus {
  can_claim: boolean;
  current_streak: number;
  longest_streak: number;
  last_claim_date: string | null;
  total_claims: number;
}

export interface Badge {
  id: number;
  name: string;
  description: string;
  category: string;
  icon_url: string;
  rarity: string;
  earned: boolean;
  earned_at: string | null;
  progress: number;
  is_secret: boolean;
}

export interface InventoryItem {
  id: number;
  name: string;
  description: string;
  type: string;
  rarity: string;
  icon_url: string;
  quantity: number;
  equipped: boolean;
  acquired_at: string;
  effects: any;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  [key: string]: any;
}

export interface QuestReward {
  type: string;
  amount?: number;
  leveled_up?: boolean;
  badges?: Array<{ id: number; name: string }>;
}

class GamificationService {
  private baseURL = '/gamification';

  async getProfile() {
    return apiWrapper(
      () => api.get(`${this.baseURL}/profile`),
      'Error fetching gamification profile'
    );
  }

  async addExperience(amount: number, source: string) {
    return apiWrapper(
      () => api.post(`${this.baseURL}/experience/add`, {
        amount,
        source
      }),
      'Error adding experience'
    );
  }

  async claimDailyReward() {
    return apiWrapper(
      () => api.post(`${this.baseURL}/daily-reward/claim`),
      'Error claiming daily reward'
    );
  }

  async getDailyRewardStatus(): Promise<DailyRewardStatus> {
    return apiWrapper<DailyRewardStatus>(
      () => api.get(`${this.baseURL}/daily-reward/status`),
      'Error fetching daily reward status'
    );
  }

  async getBadges(category?: string): Promise<{ total_badges: number; earned_badges: number; badges: Badge[] }> {
    const params = category ? { category } : {};
    return apiWrapper<{ total_badges: number; earned_badges: number; badges: Badge[] }>(
      () => api.get(`${this.baseURL}/badges`, { params }),
      'Error fetching badges'
    );
  }

  async checkAndAwardBadges() {
    return apiWrapper(
      () => api.post(`${this.baseURL}/badges/check`),
      'Error checking badges'
    );
  }

  async getInventory(itemType?: string) {
    const params = itemType ? { item_type: itemType } : {};
    return apiWrapper(
      () => api.get(`${this.baseURL}/inventory`, { params }),
      'Error fetching inventory'
    );
  }

  async useItem(itemId: number) {
    return apiWrapper(
      () => api.post(`${this.baseURL}/items/${itemId}/use`),
      'Error using item'
    );
  }

  async getLeaderboard(type: 'level' | 'gold' | 'badges' | 'quests', limit: number = 10) {
    return apiWrapper(
      () => api.get(`${this.baseURL}/leaderboard`, {
        params: { type, limit }
      }),
      'Error fetching leaderboard'
    );
  }

  async getUserStats() {
    return apiWrapper(
      () => api.get(`${this.baseURL}/stats`),
      'Error fetching user stats'
    );
  }

  async completeQuestRewards(questId: number, score: number, timeTaken: number) {
    return apiWrapper(
      () => api.post(`${this.baseURL}/quest/${questId}/complete`, {
        score,
        time_taken: timeTaken
      }),
      'Error completing quest rewards'
    );
  }
}

export const gamificationService = new GamificationService();