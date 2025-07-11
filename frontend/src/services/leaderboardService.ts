import api from './api';
import {
  LeaderboardType,
  LeaderboardResponse,
  LeaderboardEntry,
  LeaderboardFilters,
  UserRankingHistory,
  CompetitionEvent,
  LeaderboardStats,
  Guild,
  FriendsLeaderboard,
  RankTier,
  SeasonInfo,
  CompetitionPrize
} from '../types/leaderboard';

class LeaderboardService {
  // Core Leaderboard Methods
  async getLeaderboard(type: LeaderboardType, filters?: LeaderboardFilters): Promise<LeaderboardResponse> {
    const response = await api.get(`/leaderboard/${type}`, { params: filters });
    return response.data;
  }

  async getUserRanking(userId: string, type: LeaderboardType): Promise<LeaderboardEntry> {
    const response = await api.get(`/leaderboard/${type}/user/${userId}`);
    return response.data;
  }

  async getUserRankingHistory(userId: string, type: LeaderboardType): Promise<UserRankingHistory> {
    const response = await api.get(`/leaderboard/${type}/user/${userId}/history`);
    return response.data;
  }

  async getLeaderboardStats(userId: string): Promise<LeaderboardStats> {
    const response = await api.get(`/leaderboard/stats/${userId}`);
    return response.data;
  }

  // Competition Methods
  async getActiveCompetitions(): Promise<CompetitionEvent[]> {
    const response = await api.get('/competitions/active');
    return response.data;
  }

  async registerForCompetition(competitionId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/competitions/${competitionId}/register`);
    return response.data;
  }

  async getCompetitionLeaderboard(competitionId: string): Promise<LeaderboardResponse> {
    const response = await api.get(`/competitions/${competitionId}/leaderboard`);
    return response.data;
  }

  // Guild Methods
  async searchGuilds(query: string): Promise<Guild[]> {
    const response = await api.get('/guilds/search', { params: { q: query } });
    return response.data;
  }

  async joinGuild(guildId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/guilds/${guildId}/join`);
    return response.data;
  }

  async getGuildLeaderboard(): Promise<Guild[]> {
    const response = await api.get('/guilds/leaderboard');
    return response.data;
  }

  // Friends Methods
  async getFriendsLeaderboard(): Promise<FriendsLeaderboard> {
    const response = await api.get('/leaderboard/friends');
    return response.data;
  }

  // Mock Methods for Development
  async mockGetLeaderboard(type: LeaderboardType): Promise<LeaderboardResponse> {
    await new Promise(resolve => setTimeout(resolve, 600));

    const mockEntries: LeaderboardEntry[] = [
      {
        id: '1',
        user_id: 'user1',
        character_name: 'Alex the Great',
        avatar_url: '/avatars/alex.png',
        rank: 1,
        score: 25000,
        level: 45,
        tier: RankTier.GRANDMASTER,
        streak_days: 89,
        achievements_count: 47,
        quests_completed: 234,
        experience_points: 50000,
        coins_earned: 12500,
        gems_earned: 890,
        badge_icon: '👑',
        title: 'The Enlightened',
        title_color: '#FFD700',
        prestige_level: 5,
        last_active: new Date().toISOString(),
        created_at: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'stable',
        position_change: 0
      },
      {
        id: '2',
        user_id: 'user2',
        character_name: 'Emma Scholar',
        avatar_url: '/avatars/emma.png',
        rank: 2,
        score: 23500,
        level: 42,
        tier: RankTier.MASTER,
        streak_days: 56,
        achievements_count: 41,
        quests_completed: 198,
        experience_points: 45000,
        coins_earned: 11200,
        gems_earned: 756,
        badge_icon: '🏆',
        title: 'Math Wizard',
        title_color: '#9C27B0',
        prestige_level: 4,
        last_active: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 120 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'up',
        position_change: 1
      },
      {
        id: '3',
        user_id: 'user3',
        character_name: 'Science Sam',
        avatar_url: '/avatars/sam.png',
        rank: 3,
        score: 22100,
        level: 38,
        tier: RankTier.MASTER,
        streak_days: 34,
        achievements_count: 35,
        quests_completed: 187,
        experience_points: 42000,
        coins_earned: 10800,
        gems_earned: 623,
        badge_icon: '🔬',
        title: 'Lab Master',
        title_color: '#4CAF50',
        prestige_level: 3,
        last_active: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'down',
        position_change: -1
      },
      {
        id: '4',
        user_id: 'user4',
        character_name: 'History Hunter',
        avatar_url: '/avatars/hunter.png',
        rank: 4,
        score: 20800,
        level: 36,
        tier: RankTier.DIAMOND,
        streak_days: 28,
        achievements_count: 32,
        quests_completed: 165,
        experience_points: 38000,
        coins_earned: 9500,
        gems_earned: 567,
        badge_icon: '📜',
        title: 'Time Traveler',
        title_color: '#FF9800',
        prestige_level: 3,
        last_active: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 75 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'up',
        position_change: 2
      },
      {
        id: '5',
        user_id: 'user5',
        character_name: 'Code Crusader',
        avatar_url: '/avatars/crusader.png',
        rank: 5,
        score: 19200,
        level: 33,
        tier: RankTier.DIAMOND,
        streak_days: 21,
        achievements_count: 29,
        quests_completed: 145,
        experience_points: 35000,
        coins_earned: 8900,
        gems_earned: 445,
        badge_icon: '💻',
        title: 'Digital Warrior',
        title_color: '#2196F3',
        prestige_level: 2,
        last_active: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'stable',
        position_change: 0
      },
      {
        id: '6',
        user_id: 'user6',
        character_name: 'Language Legend',
        avatar_url: '/avatars/legend.png',
        rank: 6,
        score: 18500,
        level: 31,
        tier: RankTier.PLATINUM,
        streak_days: 19,
        achievements_count: 26,
        quests_completed: 134,
        experience_points: 32000,
        coins_earned: 8200,
        gems_earned: 389,
        badge_icon: '🗣️',
        title: 'Word Smith',
        title_color: '#E91E63',
        prestige_level: 2,
        last_active: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'up',
        position_change: 3
      },
      {
        id: '7',
        user_id: 'user7',
        character_name: 'Art Adventurer',
        avatar_url: '/avatars/artist.png',
        rank: 7,
        score: 17800,
        level: 29,
        tier: RankTier.PLATINUM,
        streak_days: 16,
        achievements_count: 23,
        quests_completed: 126,
        experience_points: 29000,
        coins_earned: 7800,
        gems_earned: 334,
        badge_icon: '🎨',
        title: 'Creative Mind',
        title_color: '#9C27B0',
        prestige_level: 2,
        last_active: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 38 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'down',
        position_change: -2
      },
      {
        id: '8',
        user_id: 'user8',
        character_name: 'Music Maestro',
        avatar_url: '/avatars/maestro.png',
        rank: 8,
        score: 16900,
        level: 27,
        tier: RankTier.PLATINUM,
        streak_days: 14,
        achievements_count: 21,
        quests_completed: 118,
        experience_points: 26500,
        coins_earned: 7200,
        gems_earned: 298,
        badge_icon: '🎵',
        title: 'Rhythm Master',
        title_color: '#FF5722',
        prestige_level: 1,
        last_active: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'up',
        position_change: 1
      }
    ];

    const currentUserEntry = mockEntries.find(entry => entry.user_id === 'user2'); // Emma Scholar

    return {
      type,
      entries: mockEntries,
      total_participants: 1247,
      current_user_rank: currentUserEntry?.rank,
      current_user_entry: currentUserEntry,
      last_updated: new Date().toISOString(),
      season_info: {
        id: 'season_2024_1',
        name: 'Spring Learning Championship',
        start_date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
        end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        is_active: true,
        rewards: [
          {
            rank_range: { min: 1, max: 1 },
            rewards: {
              coins: 5000,
              gems: 500,
              exclusive_title: 'Champion of Learning',
              exclusive_badge: 'Golden Crown',
              equipment_item: 'Legendary Scholar Crown'
            },
            description: 'Ultimate champion rewards'
          },
          {
            rank_range: { min: 2, max: 10 },
            rewards: {
              coins: 2500,
              gems: 250,
              exclusive_title: 'Elite Scholar',
              exclusive_badge: 'Silver Medallion'
            },
            description: 'Top 10 elite rewards'
          },
          {
            rank_range: { min: 11, max: 50 },
            rewards: {
              coins: 1000,
              gems: 100,
              exclusive_badge: 'Bronze Star'
            },
            description: 'Top 50 participation rewards'
          }
        ]
      }
    };
  }

  async mockGetActiveCompetitions(): Promise<CompetitionEvent[]> {
    await new Promise(resolve => setTimeout(resolve, 400));

    return [
      {
        id: 'speed_math_2024',
        name: 'Speed Math Challenge',
        description: 'Solve as many math problems as possible in 10 minutes',
        type: 'speed_challenge',
        start_time: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000 + 10 * 60 * 1000).toISOString(),
        registration_deadline: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
        is_active: true,
        is_registered: false,
        participants_count: 156,
        max_participants: 500,
        entry_requirements: {
          min_level: 10,
          entry_fee: {
            coins: 100
          }
        },
        prizes: [
          {
            position_range: { min: 1, max: 1 },
            rewards: {
              coins: 2000,
              gems: 200,
              exclusive_items: ['Speed Crown'],
              titles: ['Math Speed Demon']
            },
            description: 'First place winner'
          },
          {
            position_range: { min: 2, max: 5 },
            rewards: {
              coins: 1000,
              gems: 100,
              exclusive_items: ['Speed Badge']
            },
            description: 'Top 5 finishers'
          }
        ]
      },
      {
        id: 'science_accuracy_2024',
        name: 'Science Accuracy Championship',
        description: 'Achieve the highest accuracy in science questions',
        type: 'accuracy_challenge',
        start_time: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        registration_deadline: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString(),
        is_active: true,
        is_registered: true,
        participants_count: 234,
        entry_requirements: {
          min_level: 15,
          required_achievements: ['science_master'],
          entry_fee: {
            gems: 50
          }
        },
        prizes: [
          {
            position_range: { min: 1, max: 3 },
            rewards: {
              coins: 1500,
              gems: 150,
              exclusive_items: ['Precision Goggles'],
              titles: ['Science Precision Master']
            },
            description: 'Top 3 most accurate'
          }
        ]
      },
      {
        id: 'team_collaboration_2024',
        name: 'Guild Collaboration Event',
        description: 'Work together with your guild to solve complex challenges',
        type: 'collaboration',
        start_time: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(),
        end_time: new Date(Date.now() + 17 * 24 * 60 * 60 * 1000).toISOString(),
        registration_deadline: new Date(Date.now() + 8 * 24 * 60 * 60 * 1000).toISOString(),
        is_active: true,
        is_registered: false,
        participants_count: 45, // Guild count
        entry_requirements: {
          min_level: 20
        },
        prizes: [
          {
            position_range: { min: 1, max: 1 },
            rewards: {
              coins: 3000,
              gems: 300,
              exclusive_items: ['Guild Champion Banner'],
              titles: ['Team Leader']
            },
            description: 'Winning guild members'
          }
        ]
      }
    ];
  }

  async mockGetLeaderboardStats(): Promise<LeaderboardStats> {
    await new Promise(resolve => setTimeout(resolve, 300));

    return {
      user_best_ranks: {
        [LeaderboardType.OVERALL]: 2,
        [LeaderboardType.WEEKLY]: 1,
        [LeaderboardType.MONTHLY]: 3,
        [LeaderboardType.SUBJECT_MATH]: 1,
        [LeaderboardType.SUBJECT_SCIENCE]: 4,
        [LeaderboardType.SUBJECT_ENGLISH]: 7,
        [LeaderboardType.SUBJECT_HISTORY]: 12,
        [LeaderboardType.STREAK]: 2,
        [LeaderboardType.ACHIEVEMENTS]: 5,
        [LeaderboardType.QUESTS_COMPLETED]: 3
      },
      user_current_ranks: {
        [LeaderboardType.OVERALL]: 2,
        [LeaderboardType.WEEKLY]: 1,
        [LeaderboardType.MONTHLY]: 2,
        [LeaderboardType.SUBJECT_MATH]: 1,
        [LeaderboardType.SUBJECT_SCIENCE]: 6,
        [LeaderboardType.SUBJECT_ENGLISH]: 8,
        [LeaderboardType.SUBJECT_HISTORY]: 15,
        [LeaderboardType.STREAK]: 3,
        [LeaderboardType.ACHIEVEMENTS]: 6,
        [LeaderboardType.QUESTS_COMPLETED]: 4
      },
      total_competitions_entered: 12,
      competitions_won: 3,
      highest_streak: 89,
      total_experience_earned: 45000,
      rank_up_notifications: [
        {
          id: 'notif_1',
          type: 'tier_promotion',
          title: 'Tier Promotion!',
          message: 'Congratulations! You have been promoted to Master tier!',
          new_tier: RankTier.MASTER,
          old_tier: RankTier.DIAMOND,
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          is_read: false
        },
        {
          id: 'notif_2',
          type: 'leaderboard_climb',
          title: 'Leaderboard Climb!',
          message: 'You climbed 3 positions in the Math leaderboard!',
          leaderboard_type: LeaderboardType.SUBJECT_MATH,
          created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          is_read: true
        }
      ]
    };
  }

  async mockGetGuilds(): Promise<Guild[]> {
    await new Promise(resolve => setTimeout(resolve, 500));

    return [
      {
        id: 'guild_1',
        name: 'Study Masters',
        description: 'Elite learners united for academic excellence',
        member_count: 47,
        max_members: 50,
        guild_level: 25,
        total_experience: 1250000,
        rank: 1,
        leader: {
          character_name: 'Alex the Great',
          avatar_url: '/avatars/alex.png'
        },
        members: [
          {
            user_id: 'user1',
            character_name: 'Alex the Great',
            avatar_url: '/avatars/alex.png',
            role: 'leader',
            level: 45,
            contribution_points: 15000,
            joined_at: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString(),
            last_active: new Date().toISOString()
          },
          {
            user_id: 'user2',
            character_name: 'Emma Scholar',
            avatar_url: '/avatars/emma.png',
            role: 'officer',
            level: 42,
            contribution_points: 12500,
            joined_at: new Date(Date.now() - 120 * 24 * 60 * 60 * 1000).toISOString(),
            last_active: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
          }
        ],
        join_requirements: {
          min_level: 25,
          min_achievements: 20,
          application_required: true
        },
        perks: [
          'Daily bonus XP for all members',
          'Exclusive guild quests',
          'Priority event registration',
          'Guild achievement rewards'
        ],
        created_at: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString()
      },
      {
        id: 'guild_2',
        name: 'Knowledge Seekers',
        description: 'Curious minds exploring the world of learning together',
        member_count: 38,
        max_members: 45,
        guild_level: 18,
        total_experience: 890000,
        rank: 2,
        leader: {
          character_name: 'Science Sam',
          avatar_url: '/avatars/sam.png'
        },
        members: [],
        join_requirements: {
          min_level: 15,
          min_achievements: 10
        },
        perks: [
          'Weekly study group sessions',
          'Shared resource library',
          'Peer tutoring network'
        ],
        created_at: new Date(Date.now() - 200 * 24 * 60 * 60 * 1000).toISOString()
      }
    ];
  }

  async mockGetFriendsLeaderboard(): Promise<FriendsLeaderboard> {
    await new Promise(resolve => setTimeout(resolve, 300));

    const friends: LeaderboardEntry[] = [
      {
        id: '1',
        user_id: 'friend1',
        character_name: 'Study Buddy',
        avatar_url: '/avatars/buddy.png',
        rank: 1,
        score: 18500,
        level: 35,
        tier: RankTier.PLATINUM,
        experience_points: 37000,
        last_active: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'up'
      },
      {
        id: '2',
        user_id: 'user2',
        character_name: 'Emma Scholar', // Current user
        avatar_url: '/avatars/emma.png',
        rank: 2,
        score: 17800,
        level: 42,
        tier: RankTier.MASTER,
        experience_points: 45000,
        last_active: new Date().toISOString(),
        created_at: new Date(Date.now() - 120 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'up'
      },
      {
        id: '3',
        user_id: 'friend3',
        character_name: 'Quiz Master',
        avatar_url: '/avatars/quizmaster.png',
        rank: 3,
        score: 16200,
        level: 28,
        tier: RankTier.GOLD,
        experience_points: 28000,
        last_active: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
        trend: 'stable'
      }
    ];

    return {
      friends,
      user_position: 2,
      comparison_stats: {
        ahead_of_user: 1,
        behind_user: 1,
        same_level: 0
      }
    };
  }
}

const leaderboardService = new LeaderboardService();
export default leaderboardService;