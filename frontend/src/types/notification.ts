export enum NotificationType {
  // Achievement & Progress
  ACHIEVEMENT_UNLOCKED = 'achievement_unlocked',
  LEVEL_UP = 'level_up',
  QUEST_COMPLETED = 'quest_completed',
  STREAK_MILESTONE = 'streak_milestone',
  
  // Social
  FRIEND_REQUEST = 'friend_request',
  FRIEND_ACCEPTED = 'friend_accepted',
  GUILD_INVITATION = 'guild_invitation',
  GUILD_MESSAGE = 'guild_message',
  
  // Competition & Leaderboard
  RANK_CHANGED = 'rank_changed',
  COMPETITION_STARTING = 'competition_starting',
  COMPETITION_RESULT = 'competition_result',
  LEADERBOARD_UPDATE = 'leaderboard_update',
  
  // Shop & Economy
  PURCHASE_CONFIRMED = 'purchase_confirmed',
  ITEM_RECEIVED = 'item_received',
  CURRENCY_RECEIVED = 'currency_received',
  DAILY_SHOP_REFRESH = 'daily_shop_refresh',
  
  // Learning & Education
  NEW_QUEST_AVAILABLE = 'new_quest_available',
  HOMEWORK_REMINDER = 'homework_reminder',
  STUDY_SESSION_REMINDER = 'study_session_reminder',
  AI_TUTOR_MESSAGE = 'ai_tutor_message',
  
  // System & Updates
  SYSTEM_MAINTENANCE = 'system_maintenance',
  APP_UPDATE = 'app_update',
  GENERAL_ANNOUNCEMENT = 'general_announcement',
  
  // Parent Notifications
  CHILD_PROGRESS_UPDATE = 'child_progress_update',
  CHILD_ACHIEVEMENT = 'child_achievement',
  WEEKLY_REPORT = 'weekly_report'
}

export enum NotificationPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum NotificationCategory {
  ACHIEVEMENT = 'achievement',
  SOCIAL = 'social',
  COMPETITION = 'competition',
  SHOP = 'shop',
  LEARNING = 'learning',
  SYSTEM = 'system',
  PARENT = 'parent'
}

export interface NotificationAction {
  id: string;
  label: string;
  action: 'navigate' | 'api_call' | 'dismiss' | 'external_link';
  data?: {
    url?: string;
    path?: string;
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    payload?: any;
  };
  style?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

export interface NotificationData {
  // Core notification data
  user_id?: string;
  character_name?: string;
  achievement_id?: string;
  quest_id?: string;
  competition_id?: string;
  guild_id?: string;
  friend_id?: string;
  item_id?: string;
  
  // Numeric data
  level?: number;
  experience_gained?: number;
  currency_amount?: number;
  currency_type?: string;
  rank_old?: number;
  rank_new?: number;
  streak_days?: number;
  
  // Rich content
  image_url?: string;
  thumbnail_url?: string;
  avatar_url?: string;
  
  // Custom data
  [key: string]: any;
}

export interface Notification {
  id: string;
  type: NotificationType;
  category: NotificationCategory;
  priority: NotificationPriority;
  
  // Content
  title: string;
  message: string;
  icon?: string;
  color?: string;
  
  // Rich content
  data?: NotificationData;
  actions?: NotificationAction[];
  
  // Metadata
  user_id: string;
  is_read: boolean;
  is_dismissed: boolean;
  created_at: string;
  expires_at?: string;
  
  // Display settings
  show_popup?: boolean;
  play_sound?: boolean;
  vibrate?: boolean;
  auto_dismiss_after?: number; // seconds
  
  // Grouping
  group_id?: string;
  group_summary?: string;
}

export interface NotificationSettings {
  user_id: string;
  
  // Global settings
  enabled: boolean;
  sound_enabled: boolean;
  vibration_enabled: boolean;
  popup_enabled: boolean;
  
  // Category-specific settings
  categories: Record<NotificationCategory, {
    enabled: boolean;
    sound_enabled: boolean;
    popup_enabled: boolean;
    priority_filter: NotificationPriority[];
  }>;
  
  // Time-based settings
  quiet_hours: {
    enabled: boolean;
    start_time: string; // HH:mm format
    end_time: string;   // HH:mm format
    timezone: string;
  };
  
  // Push notification settings (for PWA)
  push_enabled: boolean;
  push_subscription?: PushSubscription;
  
  updated_at: string;
}

export interface NotificationGroup {
  id: string;
  type: NotificationType;
  category: NotificationCategory;
  title: string;
  summary: string;
  count: number;
  notifications: Notification[];
  latest_notification: Notification;
  created_at: string;
  updated_at: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'notification' | 'notification_read' | 'notification_dismissed' | 'bulk_action' | 'settings_update';
  data: any;
  timestamp: string;
}

export interface NotificationWebSocketMessage extends WebSocketMessage {
  type: 'notification';
  data: Notification;
}

export interface NotificationReadMessage extends WebSocketMessage {
  type: 'notification_read';
  data: {
    notification_id: string;
    user_id: string;
  };
}

export interface NotificationBulkAction extends WebSocketMessage {
  type: 'bulk_action';
  data: {
    action: 'mark_all_read' | 'clear_all' | 'clear_category';
    category?: NotificationCategory;
    user_id: string;
  };
}

// API Response types
export interface NotificationListResponse {
  notifications: Notification[];
  groups: NotificationGroup[];
  total_count: number;
  unread_count: number;
  has_more: boolean;
  next_cursor?: string;
}

export interface NotificationStatsResponse {
  total_count: number;
  unread_count: number;
  category_counts: Record<NotificationCategory, {
    total: number;
    unread: number;
  }>;
  recent_activity: {
    today: number;
    this_week: number;
    this_month: number;
  };
}

// Template system for dynamic notifications
export interface NotificationTemplate {
  id: string;
  type: NotificationType;
  category: NotificationCategory;
  priority: NotificationPriority;
  
  title_template: string;
  message_template: string;
  
  // Template variables that can be substituted
  variables: string[];
  
  // Default values
  default_icon?: string;
  default_color?: string;
  default_actions?: NotificationAction[];
  
  // Conditions for when to use this template
  conditions?: {
    user_level_min?: number;
    user_level_max?: number;
    required_achievements?: string[];
    time_of_day?: {
      start: string;
      end: string;
    };
  };
}

// Browser notification types (for PWA)
export interface BrowserNotificationOptions {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  image?: string;
  tag?: string;
  data?: any;
  actions?: {
    action: string;
    title: string;
    icon?: string;
  }[];
  requireInteraction?: boolean;
  silent?: boolean;
  vibrate?: number[];
}

// Real-time features
export interface OnlineStatus {
  user_id: string;
  character_name: string;
  is_online: boolean;
  last_seen: string;
  current_activity?: string;
  location?: string; // which page/feature they're using
}

export interface TypingIndicator {
  user_id: string;
  character_name: string;
  location: string; // chat room, guild chat, etc.
  is_typing: boolean;
  timestamp: string;
}

export interface LiveUpdate {
  type: 'leaderboard_change' | 'friend_online' | 'competition_update' | 'guild_activity';
  data: any;
  timestamp: string;
}

// Notification queue for offline support
export interface NotificationQueue {
  pending: Notification[];
  failed: Notification[];
  retry_count: Record<string, number>;
  last_sync: string;
}

// Analytics and tracking
export interface NotificationInteraction {
  notification_id: string;
  user_id: string;
  action: 'viewed' | 'clicked' | 'dismissed' | 'action_taken';
  action_data?: any;
  timestamp: string;
  device_info?: {
    platform: string;
    browser: string;
    is_mobile: boolean;
  };
}