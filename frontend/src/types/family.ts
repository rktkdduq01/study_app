// Family Dashboard API Types

export type FamilyRole = 'parent' | 'child' | 'guardian';
export type NotificationChannel = 'in_app' | 'email' | 'sms' | 'push';
export type AlertType = 'low_activity' | 'high_error_rate' | 'achievement_unlocked' | 'quest_completed' | 'daily_summary' | 'weekly_report';
export type AlertSeverity = 'info' | 'warning' | 'error' | 'success';
export type ActivityStatus = 'active' | 'idle' | 'offline';
export type QuestRequirementType = 'study_time' | 'problems_solved' | 'chapters_read' | 'quests_completed' | 'score_threshold';
export type RewardType = 'xp' | 'coins' | 'badges' | 'real_world' | 'custom';
export type ReportType = 'daily' | 'weekly' | 'monthly' | 'custom';

// Family Management
export interface FamilyResponse {
  id: number;
  name: string;
  description?: string;
  created_by: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  member_count?: number;
}

export interface FamilyMemberResponse {
  id: number;
  family_id: number;
  user_id: number;
  role: FamilyRole;
  joined_at: string;
  is_active: boolean;
  user_name?: string;
  user_email?: string;
  user_avatar?: string;
}

// Quest Management
export interface QuestRequirement {
  type: QuestRequirementType;
  value: number;
  description?: string;
}

export interface QuestReward {
  type: RewardType;
  value: any;
  description?: string;
}

export interface ParentQuestResponse {
  id: number;
  title: string;
  description: string;
  requirements: QuestRequirement[];
  rewards: QuestReward[];
  child_id: number;
  created_by: number;
  family_id: number;
  due_date?: string;
  is_recurring: boolean;
  recurrence_pattern?: any;
  is_active: boolean;
  is_completed: boolean;
  completed_at?: string;
  created_at: string;
  updated_at?: string;
  progress?: any;
}

// Activity Monitoring
export interface ActivityMonitoringResponse {
  id: number;
  family_id: number;
  child_id: number;
  activity_type: string;
  activity_data: any;
  duration_minutes?: number;
  created_at: string;
  child_name?: string;
}

// Dashboard Data
export interface ChildActivitySummary {
  child_id: number;
  child_name: string;
  avatar_url?: string;
  status: ActivityStatus;
  last_active?: string;
  today_stats: any;
  weekly_stats: any;
  current_level: number;
  current_streak: number;
  active_quests: number;
  completed_quests_today: number;
}

export interface DashboardData {
  family_id: number;
  family_name: string;
  children: ChildActivitySummary[];
  recent_activities: ActivityMonitoringResponse[];
  pending_quests: ParentQuestResponse[];
  recent_achievements: any[];
  alerts: any[];
}

// Reports
export interface FamilyReportResponse {
  id: number;
  family_id: number;
  report_type: ReportType;
  report_data: any;
  ai_insights?: any;
  generated_at: string;
  generated_by: number;
  file_url?: string;
}

// Notifications
export interface ParentNotificationResponse {
  id: number;
  family_id: number;
  parent_id: number;
  alert_type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  child_id?: number;
  action_url?: string;
  data?: any;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}

// Settings
export interface NotificationPreferences {
  channels: NotificationChannel[];
  alert_types: Record<AlertType, boolean>;
  quiet_hours_start?: number;
  quiet_hours_end?: number;
}

export interface AlertThresholds {
  low_activity_hours: number;
  high_error_rate_percentage: number;
  min_daily_study_minutes: number;
}

export interface FamilySettings {
  notification_preferences: NotificationPreferences;
  alert_thresholds: AlertThresholds;
  dashboard_refresh_interval: number;
  report_generation_day: number;
  timezone: string;
}

// Request Types
export interface CreateFamilyRequest {
  name: string;
  description?: string;
}

export interface InviteFamilyMemberRequest {
  user_id: number;
  role: FamilyRole;
}

export interface CreateParentQuestRequest {
  title: string;
  description: string;
  requirements: QuestRequirement[];
  rewards: QuestReward[];
  child_id: number;
  due_date?: string;
  is_recurring?: boolean;
  recurrence_pattern?: any;
}

export interface UpdateParentQuestRequest {
  title?: string;
  description?: string;
  requirements?: QuestRequirement[];
  rewards?: QuestReward[];
  due_date?: string;
  is_active?: boolean;
}

export interface GenerateReportRequest {
  report_type: ReportType;
  child_id?: number;
  start_date?: string;
  end_date?: string;
  include_ai_insights?: boolean;
}

export interface UpdateSettingsRequest {
  notification_preferences?: NotificationPreferences;
  alert_thresholds?: AlertThresholds;
  dashboard_refresh_interval?: number;
  report_generation_day?: number;
  timezone?: string;
}