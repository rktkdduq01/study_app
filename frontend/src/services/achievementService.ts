import api from './api';
import { 
  Achievement, 
  UserAchievement, 
  AchievementStats, 
  AchievementCategory, 
  AchievementRarity,
  AchievementChallenge 
} from '../types/achievement';

interface AchievementFilters {
  category?: AchievementCategory;
  rarity?: AchievementRarity;
  skip?: number;
  limit?: number;
}

class AchievementService {
  async getAchievements(filters?: AchievementFilters): Promise<Achievement[]> {
    const response = await api.get<Achievement[]>('/achievements/', { params: filters });
    return response.data;
  }

  async getAchievement(id: number): Promise<Achievement> {
    const response = await api.get<Achievement>(`/achievements/${id}`);
    return response.data;
  }

  async getMyAchievements(completedOnly: boolean = false): Promise<UserAchievement[]> {
    const response = await api.get<UserAchievement[]>('/achievements/me', {
      params: { completed_only: completedOnly }
    });
    return response.data;
  }

  async updateAchievementProgress(achievementId: number, progress: number): Promise<UserAchievement> {
    const response = await api.put<UserAchievement>(`/achievements/${achievementId}/progress`, {
      progress
    });
    return response.data;
  }

  async getAchievementStats(): Promise<AchievementStats> {
    const response = await api.get<AchievementStats>('/achievements/stats');
    return response.data;
  }

  async getLeaderboard(limit: number = 100): Promise<any[]> {
    const response = await api.get<any[]>('/achievements/leaderboard', {
      params: { limit }
    });
    return response.data;
  }

  // Get daily/weekly challenges
  async getChallenges(type?: 'daily' | 'weekly' | 'special'): Promise<AchievementChallenge[]> {
    const response = await api.get('/achievements/challenges', { params: { type } });
    return response.data;
  }

  // Claim achievement reward
  async claimReward(achievementId: number): Promise<{
    reward_type: string;
    reward_value: number | string;
  }> {
    const response = await api.post(`/achievements/${achievementId}/claim`);
    return response.data;
  }

  // Get leaderboard for a challenge
  async getChallengeLeaderboard(challengeId: string): Promise<{
    user_rank: number;
    total_participants: number;
    top_players: Array<{
      id: string;
      name: string;
      avatar: string;
      progress: number;
      completed_at?: string;
    }>;
  }> {
    const response = await api.get(`/achievements/challenges/${challengeId}/leaderboard`);
    return response.data;
  }

  // Check for new unlocked achievements
  async checkUnlockedAchievements(): Promise<Achievement[]> {
    const response = await api.get('/achievements/check-unlocked');
    return response.data;
  }

  // Get recommended achievements based on user progress
  async getRecommendedAchievements(): Promise<Achievement[]> {
    const response = await api.get('/achievements/recommended');
    return response.data;
  }

  // Mock methods for development
  async mockGetAchievements(): Promise<Achievement[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    return [
      // Time Challenge Achievements
      {
        id: 1,
        name: 'Speed Demon',
        description: 'Complete 5 quests in under 10 minutes each',
        category: AchievementCategory.TIME_CHALLENGE,
        rarity: AchievementRarity.RARE,
        points: 100,
        max_progress: 5,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'gems',
        reward_value: 25,
        time_limit: 600,
      },
      {
        id: 2,
        name: 'Lightning Scholar',
        description: 'Answer 20 questions correctly in 60 seconds',
        category: AchievementCategory.TIME_CHALLENGE,
        rarity: AchievementRarity.EPIC,
        points: 200,
        max_progress: 20,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'title',
        reward_value: 'The Swift',
        time_limit: 60,
      },
      // Mastery Achievements
      {
        id: 3,
        name: 'Math Master',
        description: 'Achieve 100% accuracy in 10 consecutive math quests',
        category: AchievementCategory.MASTERY,
        rarity: AchievementRarity.EPIC,
        points: 300,
        max_progress: 10,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'badge',
        reward_value: 'math_master_badge',
        difficulty_multiplier: 2.0,
      },
      {
        id: 4,
        name: 'Science Savant',
        description: 'Master all science topics with at least 90% proficiency',
        category: AchievementCategory.MASTERY,
        rarity: AchievementRarity.LEGENDARY,
        points: 500,
        max_progress: 20,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'character_skin',
        reward_value: 'scientist_outfit',
      },
      // Streak Achievements
      {
        id: 5,
        name: 'Week Warrior',
        description: 'Maintain a 7-day learning streak',
        category: AchievementCategory.STREAK,
        rarity: AchievementRarity.COMMON,
        points: 50,
        max_progress: 7,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'coins',
        reward_value: 100,
      },
      {
        id: 6,
        name: 'Unstoppable Force',
        description: 'Maintain a 30-day learning streak',
        category: AchievementCategory.STREAK,
        rarity: AchievementRarity.LEGENDARY,
        points: 500,
        max_progress: 30,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'character_skin',
        reward_value: 'legendary_aura',
      },
      // Social Achievements
      {
        id: 7,
        name: 'Team Player',
        description: 'Complete 10 collaborative quests with friends',
        category: AchievementCategory.SOCIAL,
        rarity: AchievementRarity.RARE,
        points: 150,
        max_progress: 10,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'title',
        reward_value: 'The Collaborator',
      },
      // Special Event Achievement
      {
        id: 8,
        name: 'Winter Wonder',
        description: 'Complete all winter-themed quests before the season ends',
        category: AchievementCategory.SPECIAL,
        rarity: AchievementRarity.RARE,
        points: 150,
        max_progress: 5,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        seasonal: true,
        reward_type: 'item',
        reward_value: 'snowflake_charm',
      },
      // Exploration Achievements
      {
        id: 9,
        name: 'Knowledge Explorer',
        description: 'Try quests from 5 different subjects',
        category: AchievementCategory.EXPLORATION,
        rarity: AchievementRarity.COMMON,
        points: 75,
        max_progress: 5,
        is_hidden: false,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'gems',
        reward_value: 15,
      },
      // Hidden Achievement
      {
        id: 10,
        name: 'Secret Scholar',
        description: '???',
        category: AchievementCategory.SPECIAL,
        rarity: AchievementRarity.LEGENDARY,
        points: 1000,
        max_progress: 1,
        is_hidden: true,
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        reward_type: 'title',
        reward_value: 'The Enigma',
      },
    ];
  }

  async mockGetUserAchievements(): Promise<UserAchievement[]> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const achievements = await this.mockGetAchievements();
    
    return [
      {
        id: 1,
        user_id: 1,
        achievement_id: 1,
        progress: 3,
        is_completed: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        achievement: achievements[0],
      },
      {
        id: 2,
        user_id: 1,
        achievement_id: 3,
        progress: 7,
        is_completed: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        achievement: achievements[2],
      },
      {
        id: 3,
        user_id: 1,
        achievement_id: 5,
        progress: 7,
        is_completed: true,
        completed_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        achievement: achievements[4],
      },
      {
        id: 4,
        user_id: 1,
        achievement_id: 9,
        progress: 3,
        is_completed: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        achievement: achievements[8],
      },
    ];
  }

  async mockGetStats(): Promise<AchievementStats> {
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return {
      total_achievements: 150,
      completed_achievements: 45,
      total_points: 15000,
      earned_points: 4500,
      completion_percentage: 30,
      achievements_by_category: {
        learning: { total: 30, completed: 12 },
        quest: { total: 25, completed: 10 },
        streak: { total: 20, completed: 8 },
        social: { total: 15, completed: 5 },
        collection: { total: 20, completed: 3 },
        special: { total: 10, completed: 2 },
        time_challenge: { total: 15, completed: 3 },
        mastery: { total: 10, completed: 2 },
        exploration: { total: 5, completed: 0 },
      },
      achievements_by_rarity: {
        common: { total: 60, completed: 30 },
        rare: { total: 50, completed: 10 },
        epic: { total: 30, completed: 4 },
        legendary: { total: 10, completed: 1 },
      },
      recent_unlocks: [],
      next_achievable: [],
      daily_progress: 75,
      weekly_streak: 7,
    };
  }

  async mockGetChallenges(): Promise<AchievementChallenge[]> {
    await new Promise(resolve => setTimeout(resolve, 300));
    
    return [
      {
        id: 'daily-1',
        title: "Today's Speed Learning Challenge",
        description: 'Complete 3 quests in under 30 minutes total',
        type: 'daily',
        achievements: [],
        end_time: new Date(Date.now() + 8 * 60 * 60 * 1000),
        bonus_reward: {
          type: 'gems',
          value: 50,
        },
        participants: 1234,
        leaderboard: {
          user_rank: 42,
          top_players: [
            { name: 'Alex', avatar: '👑', progress: 100 },
            { name: 'Sarah', avatar: '🌟', progress: 95 },
            { name: 'Mike', avatar: '🔥', progress: 90 },
          ],
        },
      },
      {
        id: 'weekly-1',
        title: 'Master of All Subjects',
        description: 'Complete at least one quest in each subject this week',
        type: 'weekly',
        achievements: [],
        end_time: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
        bonus_reward: {
          type: 'character_skin',
          value: 'rainbow_aura',
        },
        participants: 5678,
      },
    ];
  }
}

export default new AchievementService();