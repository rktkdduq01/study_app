export enum AchievementCategory {
  LEARNING = 'learning',
  QUEST = 'quest',
  STREAK = 'streak',
  SOCIAL = 'social',
  COLLECTION = 'collection',
  SPECIAL = 'special',
  TIME_CHALLENGE = 'time_challenge',
  MASTERY = 'mastery',
  EXPLORATION = 'exploration'
}

export enum AchievementRarity {
  COMMON = 'common',
  RARE = 'rare',
  EPIC = 'epic',
  LEGENDARY = 'legendary'
}

export interface Achievement {
  id: number;
  name: string;
  description: string;
  category: AchievementCategory;
  rarity: AchievementRarity;
  icon_url?: string;
  points: number;
  max_progress: number;
  is_hidden: boolean;
  requirements?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // New fields for enhanced engagement
  reward_type?: 'coins' | 'gems' | 'item' | 'title' | 'badge' | 'character_skin';
  reward_value?: number | string;
  time_limit?: number; // in seconds for time-based challenges
  difficulty_multiplier?: number; // bonus points for harder achievements
  unlock_condition?: string; // prerequisite achievement or level
  seasonal?: boolean; // limited-time seasonal achievements
}

export interface UserAchievement {
  id: number;
  user_id: number;
  achievement_id: number;
  progress: number;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  achievement: Achievement;
}

export interface AchievementStats {
  total_achievements: number;
  completed_achievements: number;
  total_points: number;
  earned_points: number;
  completion_percentage: number;
  achievements_by_category: Record<string, { total: number; completed: number }>;
  achievements_by_rarity: Record<string, { total: number; completed: number }>;
  recent_unlocks: UserAchievement[];
  next_achievable: Achievement[];
  daily_progress: number;
  weekly_streak: number;
}

export interface AchievementChallenge {
  id: string;
  title: string;
  description: string;
  type: 'daily' | 'weekly' | 'special';
  achievements: Achievement[];
  end_time: Date;
  bonus_reward?: {
    type: string;
    value: number | string;
  };
  participants?: number;
  leaderboard?: {
    user_rank: number;
    top_players: Array<{
      name: string;
      avatar: string;
      progress: number;
    }>;
  };
}

export interface AchievementNotification {
  achievement: Achievement;
  unlockedAt: Date;
  isNew: boolean;
  celebrationType: 'normal' | 'epic' | 'legendary';
}