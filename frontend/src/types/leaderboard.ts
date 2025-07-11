export enum LeaderboardType {
  OVERALL = 'overall',
  WEEKLY = 'weekly',
  MONTHLY = 'monthly',
  SUBJECT_MATH = 'subject_math',
  SUBJECT_SCIENCE = 'subject_science',
  SUBJECT_ENGLISH = 'subject_english',
  SUBJECT_HISTORY = 'subject_history',
  STREAK = 'streak',
  ACHIEVEMENTS = 'achievements',
  QUESTS_COMPLETED = 'quests_completed'
}

export enum RankTier {
  BRONZE = 'bronze',
  SILVER = 'silver',
  GOLD = 'gold',
  PLATINUM = 'platinum',
  DIAMOND = 'diamond',
  MASTER = 'master',
  GRANDMASTER = 'grandmaster'
}

export interface LeaderboardEntry {
  id: string;
  user_id: string;
  character_name: string;
  avatar_url?: string;
  rank: number;
  score: number;
  level: number;
  tier: RankTier;
  streak_days?: number;
  achievements_count?: number;
  quests_completed?: number;
  subject_level?: number;
  experience_points: number;
  coins_earned?: number;
  gems_earned?: number;
  badge_icon?: string;
  title?: string;
  title_color?: string;
  prestige_level?: number;
  last_active: string;
  created_at: string;
  trend?: 'up' | 'down' | 'stable';
  position_change?: number; // +5 means moved up 5 positions
}

export interface LeaderboardResponse {
  type: LeaderboardType;
  entries: LeaderboardEntry[];
  total_participants: number;
  current_user_rank?: number;
  current_user_entry?: LeaderboardEntry;
  last_updated: string;
  season_info?: SeasonInfo;
}

export interface SeasonInfo {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  rewards: SeasonReward[];
}

export interface SeasonReward {
  rank_range: {
    min: number;
    max: number;
  };
  rewards: {
    coins?: number;
    gems?: number;
    exclusive_title?: string;
    exclusive_badge?: string;
    equipment_item?: string;
  };
  description: string;
}

export interface UserRankingHistory {
  user_id: string;
  leaderboard_type: LeaderboardType;
  entries: RankingHistoryEntry[];
}

export interface RankingHistoryEntry {
  date: string;
  rank: number;
  score: number;
  tier: RankTier;
}

export interface LeaderboardFilters {
  type?: LeaderboardType;
  time_period?: 'daily' | 'weekly' | 'monthly' | 'all_time';
  tier_filter?: RankTier;
  friends_only?: boolean;
  guild_only?: boolean;
  age_group?: '6-9' | '10-12' | '13-15' | '16-18';
  country?: string;
}

export interface CompetitionEvent {
  id: string;
  name: string;
  description: string;
  type: 'speed_challenge' | 'accuracy_challenge' | 'streak_challenge' | 'collaboration';
  start_time: string;
  end_time: string;
  registration_deadline: string;
  is_active: boolean;
  is_registered: boolean;
  participants_count: number;
  max_participants?: number;
  entry_requirements?: {
    min_level?: number;
    required_achievements?: string[];
    entry_fee?: {
      coins?: number;
      gems?: number;
    };
  };
  prizes: CompetitionPrize[];
  leaderboard_id?: string;
}

export interface CompetitionPrize {
  position_range: {
    min: number;
    max: number;
  };
  rewards: {
    coins?: number;
    gems?: number;
    exclusive_items?: string[];
    titles?: string[];
    badges?: string[];
  };
  description: string;
}

export interface LeaderboardStats {
  user_best_ranks: Record<LeaderboardType, number>;
  user_current_ranks: Record<LeaderboardType, number>;
  total_competitions_entered: number;
  competitions_won: number;
  highest_streak: number;
  total_experience_earned: number;
  rank_up_notifications: RankUpNotification[];
}

export interface RankUpNotification {
  id: string;
  type: 'tier_promotion' | 'leaderboard_climb' | 'achievement_unlock';
  title: string;
  message: string;
  new_tier?: RankTier;
  old_tier?: RankTier;
  leaderboard_type?: LeaderboardType;
  created_at: string;
  is_read: boolean;
}

export interface Guild {
  id: string;
  name: string;
  description: string;
  member_count: number;
  max_members: number;
  guild_level: number;
  total_experience: number;
  rank: number;
  leader: {
    character_name: string;
    avatar_url?: string;
  };
  members: GuildMember[];
  join_requirements?: {
    min_level?: number;
    min_achievements?: number;
    application_required?: boolean;
  };
  perks: string[];
  created_at: string;
}

export interface GuildMember {
  user_id: string;
  character_name: string;
  avatar_url?: string;
  role: 'leader' | 'officer' | 'member';
  level: number;
  contribution_points: number;
  joined_at: string;
  last_active: string;
}

export interface FriendsLeaderboard {
  friends: LeaderboardEntry[];
  user_position: number;
  comparison_stats: {
    ahead_of_user: number;
    behind_user: number;
    same_level: number;
  };
}