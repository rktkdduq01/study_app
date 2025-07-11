// Parent Dashboard Types

export interface ParentDashboard {
  parentId: string;
  connectedChildren: ChildConnection[];
  childrenStatistics: ChildStatistics[];
  progressSummaries: ProgressSummary[];
  recentActivities: RecentActivity[];
  achievementTracking: AchievementTracking;
  aiInsights: AIInsight[];
  lastUpdated: Date;
}

export interface ChildConnection {
  childId: string;
  childName: string;
  avatar: string;
  grade: string;
  age: number;
  connectionDate: Date;
  isActive: boolean;
  lastActiveAt: Date;
}

export interface ChildStatistics {
  childId: string;
  totalLearningTime: number; // in minutes
  questsCompleted: number;
  totalXP: number;
  currentStreak: number;
  longestStreak: number;
  averageSessionTime: number; // in minutes
  subjectDistribution: SubjectDistribution[];
  weeklyProgress: WeeklyProgress[];
}

export interface SubjectDistribution {
  subject: Subject;
  percentage: number;
  timeSpent: number; // in minutes
  questsCompleted: number;
}

export interface WeeklyProgress {
  week: string; // ISO week format
  xpEarned: number;
  questsCompleted: number;
  timeSpent: number; // in minutes
  subjects: Subject[];
}

export interface ProgressSummary {
  childId: string;
  period: 'daily' | 'weekly' | 'monthly';
  startDate: Date;
  endDate: Date;
  totalXP: number;
  questsCompleted: number;
  learningTime: number; // in minutes
  achievementsUnlocked: number;
  skillsImproved: SkillImprovement[];
  comparisonToPrevious: {
    xpChange: number; // percentage
    questsChange: number; // percentage
    timeChange: number; // percentage
  };
}

export interface SkillImprovement {
  skillName: string;
  previousLevel: number;
  currentLevel: number;
  improvement: number; // percentage
}

export interface RecentActivity {
  id: string;
  childId: string;
  childName: string;
  activityType: ActivityType;
  title: string;
  description: string;
  subject?: Subject;
  xpEarned?: number;
  timestamp: Date;
  duration?: number; // in minutes
  achievement?: {
    name: string;
    icon: string;
    rarity: 'common' | 'rare' | 'epic' | 'legendary';
  };
}

export type ActivityType = 
  | 'quest_completed'
  | 'achievement_unlocked'
  | 'level_up'
  | 'streak_milestone'
  | 'skill_improved'
  | 'challenge_completed'
  | 'quiz_taken'
  | 'story_completed';

export interface AchievementTracking {
  totalAchievements: number;
  unlockedAchievements: number;
  recentAchievements: Achievement[];
  upcomingMilestones: Milestone[];
  achievementsByCategory: AchievementCategory[];
}

export interface Achievement {
  id: string;
  childId: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  unlockedAt: Date;
  xpReward: number;
  criteria: string;
}

export interface Milestone {
  id: string;
  childId: string;
  title: string;
  description: string;
  currentProgress: number;
  targetProgress: number;
  progressPercentage: number;
  estimatedCompletion: Date;
  reward: {
    xp: number;
    badge?: string;
    title?: string;
  };
}

export interface AchievementCategory {
  category: string;
  total: number;
  unlocked: number;
  percentage: number;
}

export interface AIInsight {
  id: string;
  childId: string;
  childName: string;
  type: InsightType;
  priority: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  recommendation: string;
  actionItems: string[];
  relatedData: {
    metric?: string;
    value?: number;
    trend?: 'improving' | 'stable' | 'declining';
  };
  generatedAt: Date;
  isRead: boolean;
}

export type InsightType = 
  | 'learning_pattern'
  | 'strength_identified'
  | 'improvement_area'
  | 'engagement_trend'
  | 'skill_recommendation'
  | 'challenge_suggestion'
  | 'achievement_prediction'
  | 'motivational';

// Child Profile Types

export interface ChildProfile {
  id: string;
  basicInfo: ChildBasicInfo;
  learningMetrics: LearningMetrics;
  strengthsAndWeaknesses: StrengthsWeaknesses;
  recentQuests: QuestSummary[];
  recentAchievements: Achievement[];
  aiRecommendations: AIRecommendation[];
  learningPreferences: LearningPreferences;
  parentalControls: ParentalControls;
}

export interface ChildBasicInfo {
  name: string;
  username: string;
  avatar: string;
  age: number;
  grade: string;
  school?: string;
  favoriteSubjects: Subject[];
  interests: string[];
  accountCreated: Date;
  lastActive: Date;
}

export interface LearningMetrics {
  overallProgress: {
    level: number;
    currentXP: number;
    nextLevelXP: number;
    percentageToNextLevel: number;
  };
  timeMetrics: {
    totalLearningTime: number; // in minutes
    averageDailyTime: number; // in minutes
    mostActiveTime: string; // e.g., "3:00 PM - 4:00 PM"
    mostActiveDay: string; // e.g., "Saturday"
  };
  performanceMetrics: {
    averageQuizScore: number; // percentage
    questCompletionRate: number; // percentage
    challengeSuccessRate: number; // percentage
    improvementRate: number; // percentage over last month
  };
  engagementMetrics: {
    currentStreak: number;
    longestStreak: number;
    consistency: number; // percentage of days active in last month
    questsPerWeek: number;
  };
}

export interface StrengthsWeaknesses {
  strengths: SkillAssessment[];
  weaknesses: SkillAssessment[];
  emergingSkills: SkillAssessment[];
  recommendations: string[];
}

export interface SkillAssessment {
  skill: string;
  subject: Subject;
  level: number; // 1-10
  confidence: number; // percentage
  lastAssessed: Date;
  trend: 'improving' | 'stable' | 'declining';
  relatedQuests: number;
}

export interface QuestSummary {
  id: string;
  title: string;
  subject: Subject;
  difficulty: 'easy' | 'medium' | 'hard';
  completedAt: Date;
  timeSpent: number; // in minutes
  xpEarned: number;
  score?: number; // percentage
  skillsUsed: string[];
  feedback?: string;
}

export interface AIRecommendation {
  id: string;
  type: RecommendationType;
  title: string;
  description: string;
  reason: string;
  suggestedActions: SuggestedAction[];
  priority: 'low' | 'medium' | 'high';
  expiresAt?: Date;
  createdAt: Date;
}

export type RecommendationType = 
  | 'quest_suggestion'
  | 'skill_focus'
  | 'challenge_recommendation'
  | 'learning_path'
  | 'time_management'
  | 'subject_balance'
  | 'difficulty_adjustment';

export interface SuggestedAction {
  action: string;
  expectedBenefit: string;
  estimatedTime?: number; // in minutes
  relatedContent?: {
    type: 'quest' | 'challenge' | 'topic';
    id: string;
    title: string;
  };
}

export interface LearningPreferences {
  preferredDifficulty: 'adaptive' | 'easy' | 'medium' | 'hard';
  preferredSessionLength: number; // in minutes
  preferredSubjects: Subject[];
  learningStyle: LearningStyle[];
  motivators: Motivator[];
}

export type LearningStyle = 
  | 'visual'
  | 'auditory'
  | 'kinesthetic'
  | 'reading_writing';

export type Motivator = 
  | 'achievements'
  | 'leaderboard'
  | 'story_progression'
  | 'rewards'
  | 'challenges'
  | 'social_interaction';

export interface ParentalControls {
  dailyTimeLimit?: number; // in minutes
  allowedHours?: {
    start: string; // e.g., "09:00"
    end: string; // e.g., "21:00"
  };
  contentFilters: ContentFilter[];
  communicationSettings: {
    allowFriendRequests: boolean;
    allowMessages: boolean;
    requireParentApproval: boolean;
  };
  privacySettings: {
    shareProgress: boolean;
    appearInLeaderboards: boolean;
    profileVisibility: 'private' | 'friends' | 'public';
  };
}

export interface ContentFilter {
  filterType: 'subject' | 'difficulty' | 'content_type';
  allowedValues: string[];
}

// Parent Notification Types

export interface ParentNotification {
  id: string;
  type: NotificationType;
  priority: NotificationPriority;
  childId: string;
  childName: string;
  title: string;
  message: string;
  data: NotificationData;
  createdAt: Date;
  readAt?: Date;
  actionRequired: boolean;
  actions?: NotificationAction[];
}

export type NotificationType = 
  | 'achievement_unlocked'
  | 'milestone_reached'
  | 'streak_milestone'
  | 'ai_insight'
  | 'recommendation'
  | 'weekly_summary'
  | 'skill_improvement'
  | 'challenge_completed'
  | 'time_limit_reached'
  | 'inactivity_alert'
  | 'friend_request'
  | 'report_generated';

export type NotificationPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface NotificationData {
  achievement?: {
    name: string;
    description: string;
    icon: string;
    rarity: 'common' | 'rare' | 'epic' | 'legendary';
    xpReward: number;
  };
  milestone?: {
    type: string;
    value: number;
    previousValue?: number;
  };
  insight?: {
    category: InsightType;
    summary: string;
    trend?: 'positive' | 'neutral' | 'negative';
  };
  recommendation?: {
    type: RecommendationType;
    summary: string;
    actionCount: number;
  };
  summary?: {
    period: 'daily' | 'weekly' | 'monthly';
    highlights: string[];
    metrics: {
      [key: string]: number | string;
    };
  };
}

export interface NotificationAction {
  label: string;
  action: 'view' | 'dismiss' | 'approve' | 'deny' | 'configure';
  href?: string;
  data?: any;
}

// Common Types

export type Subject = 
  | 'math'
  | 'science'
  | 'english'
  | 'history'
  | 'geography'
  | 'art'
  | 'music'
  | 'coding'
  | 'critical_thinking'
  | 'problem_solving';

// Utility Types

export interface DateRange {
  start: Date;
  end: Date;
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
}

export interface FilterOptions {
  childIds?: string[];
  subjects?: Subject[];
  dateRange?: DateRange;
  activityTypes?: ActivityType[];
  notificationTypes?: NotificationType[];
}

export interface SortOptions {
  field: string;
  order: 'asc' | 'desc';
}