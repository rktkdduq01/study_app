// Friend System Types

export enum FriendStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  BLOCKED = 'blocked',
  DECLINED = 'declined'
}

export enum OnlineStatus {
  ONLINE = 'online',
  AWAY = 'away',
  BUSY = 'busy',
  OFFLINE = 'offline',
  INVISIBLE = 'invisible'
}

export enum ActivityType {
  STUDYING = 'studying',
  QUEST = 'quest',
  SHOPPING = 'shopping',
  ACHIEVEMENT = 'achievement',
  IDLE = 'idle',
  GAMING = 'gaming'
}

export interface Friend {
  id: string;
  user_id: string;
  friend_user_id: string;
  status: FriendStatus;
  created_at: string;
  updated_at: string;
  
  // Friend's character info
  friend_character: {
    id: string;
    name: string;
    avatar_url?: string;
    total_level: number;
    class: string;
    title?: string;
    badge?: string;
  };
  
  // Online status
  online_status: OnlineStatus;
  last_seen: string;
  current_activity?: ActivityType;
  activity_details?: string;
  location?: string; // Current page/feature
  
  // Privacy settings
  show_activity: boolean;
  show_online_status: boolean;
  allow_messages: boolean;
  
  // Friendship stats
  friendship_points: number;
  interactions_count: number;
  last_interaction: string;
  
  // Mutual data
  mutual_friends_count: number;
  mutual_achievements_count: number;
  mutual_guilds: string[];
}

export interface FriendRequest {
  id: string;
  from_user_id: string;
  to_user_id: string;
  message?: string;
  status: FriendStatus;
  created_at: string;
  expires_at: string;
  
  // Requester's character info
  from_character: {
    id: string;
    name: string;
    avatar_url?: string;
    total_level: number;
    class: string;
    title?: string;
  };
  
  // Additional context
  mutual_friends_count: number;
  suggested_reason?: string; // Why this friend was suggested
}

export interface FriendSuggestion {
  id: string;
  suggested_user_id: string;
  reason: 'mutual_friends' | 'same_school' | 'similar_interests' | 'nearby' | 'algorithm';
  score: number; // Recommendation confidence
  
  // Suggested friend's character info
  character: {
    id: string;
    name: string;
    avatar_url?: string;
    total_level: number;
    class: string;
    title?: string;
    interests: string[];
  };
  
  // Context for suggestion
  mutual_friends_count: number;
  mutual_achievements: string[];
  similarity_score: number;
  school_name?: string;
  distance?: number; // In km if location-based
  
  created_at: string;
  dismissed: boolean;
}

export interface FriendActivity {
  id: string;
  user_id: string;
  friend_user_id: string;
  activity_type: ActivityType;
  activity_data: {
    title: string;
    description: string;
    achievement_id?: string;
    quest_id?: string;
    level_gained?: number;
    experience_gained?: number;
    item_purchased?: string;
    location?: string;
    image_url?: string;
  };
  created_at: string;
  is_public: boolean;
  likes_count: number;
  comments_count: number;
  user_liked: boolean;
}

export interface FriendInteraction {
  id: string;
  user_id: string;
  friend_user_id: string;
  interaction_type: 'like' | 'comment' | 'help' | 'gift' | 'challenge' | 'study_together';
  interaction_data?: any;
  points_earned: number;
  created_at: string;
}

// Chat System Types
export interface ChatRoom {
  id: string;
  type: 'direct' | 'group' | 'guild';
  name?: string; // For group chats
  description?: string;
  avatar_url?: string;
  
  // Participants
  participants: ChatParticipant[];
  created_by: string;
  created_at: string;
  updated_at: string;
  
  // Latest message
  last_message?: ChatMessage;
  last_activity: string;
  
  // Settings
  is_active: boolean;
  is_muted: boolean;
  notification_level: 'all' | 'mentions' | 'none';
  
  // Stats
  total_messages: number;
  unread_count: number;
}

export interface ChatParticipant {
  user_id: string;
  character_name: string;
  avatar_url?: string;
  role: 'admin' | 'moderator' | 'member';
  joined_at: string;
  last_read_at: string;
  is_online: boolean;
  is_typing: boolean;
  permissions: {
    can_send_messages: boolean;
    can_add_members: boolean;
    can_remove_members: boolean;
    can_edit_room: boolean;
  };
}

export interface ChatMessage {
  id: string;
  room_id: string;
  sender_id: string;
  sender_name: string;
  sender_avatar?: string;
  
  // Message content
  content: string;
  message_type: 'text' | 'image' | 'file' | 'achievement_share' | 'quest_invitation' | 'study_session' | 'system';
  metadata?: {
    achievement_id?: string;
    quest_id?: string;
    file_url?: string;
    file_name?: string;
    file_size?: number;
    image_url?: string;
    study_session_id?: string;
  };
  
  // Message status
  created_at: string;
  edited_at?: string;
  deleted_at?: string;
  is_edited: boolean;
  is_deleted: boolean;
  
  // Reactions and replies
  reactions: MessageReaction[];
  reply_to?: string; // Message ID being replied to
  thread_count?: number;
  
  // Read status
  read_by: string[]; // User IDs who have read this message
  delivered_to: string[]; // User IDs to whom message was delivered
}

export interface MessageReaction {
  emoji: string;
  count: number;
  users: string[]; // User IDs who reacted
  user_reacted: boolean; // If current user reacted
}

export interface TypingIndicator {
  room_id: string;
  user_id: string;
  character_name: string;
  started_at: string;
}

// Guild System Types
export interface Guild {
  id: string;
  name: string;
  description: string;
  avatar_url?: string;
  banner_url?: string;
  
  // Guild settings
  type: 'public' | 'private' | 'invite_only';
  max_members: number;
  level: number;
  experience: number;
  
  // Guild stats
  members_count: number;
  active_members_count: number;
  total_achievements: number;
  total_quests_completed: number;
  
  // Leadership
  leader_id: string;
  moderators: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
  
  // Features
  features: {
    guild_chat: boolean;
    group_quests: boolean;
    competitions: boolean;
    study_sessions: boolean;
    resource_sharing: boolean;
  };
  
  // Requirements
  requirements: {
    min_level: number;
    min_achievements: number;
    application_required: boolean;
    invite_only: boolean;
  };
  
  // Activity
  last_activity: string;
  activity_score: number; // Based on member activity
  
  // Tags and categories
  tags: string[];
  category: string;
  school_affiliated: boolean;
  school_name?: string;
}

export interface GuildMember {
  id: string;
  guild_id: string;
  user_id: string;
  character_name: string;
  avatar_url?: string;
  
  // Member status
  role: 'leader' | 'moderator' | 'senior' | 'member' | 'initiate';
  status: 'active' | 'inactive' | 'banned' | 'left';
  joined_at: string;
  last_active: string;
  
  // Contributions
  contribution_points: number;
  quests_completed: number;
  achievements_earned: number;
  study_hours: number;
  
  // Permissions
  permissions: {
    can_invite: boolean;
    can_kick: boolean;
    can_manage_events: boolean;
    can_manage_resources: boolean;
    can_moderate_chat: boolean;
  };
  
  // Recognition
  badges: string[];
  title?: string;
  recognition_level: number;
}

export interface GuildEvent {
  id: string;
  guild_id: string;
  title: string;
  description: string;
  type: 'quest' | 'study_session' | 'competition' | 'social' | 'meeting';
  
  // Scheduling
  start_time: string;
  end_time: string;
  timezone: string;
  location?: string; // Physical or virtual
  
  // Participation
  max_participants?: number;
  participants: string[];
  organizer_id: string;
  requires_signup: boolean;
  
  // Requirements
  level_requirement?: number;
  achievement_requirements?: string[];
  
  // Rewards
  rewards: {
    experience: number;
    guild_points: number;
    items?: string[];
    badges?: string[];
  };
  
  // Status
  status: 'scheduled' | 'active' | 'completed' | 'cancelled';
  created_at: string;
  updated_at: string;
}

// Study Groups
export interface StudyGroup {
  id: string;
  name: string;
  description: string;
  subject: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  
  // Members
  members: StudyGroupMember[];
  max_members: number;
  leader_id: string;
  
  // Schedule
  schedule: {
    days: string[]; // ['monday', 'wednesday', 'friday']
    start_time: string;
    end_time: string;
    timezone: string;
    duration_weeks: number;
  };
  
  // Content
  topics: string[];
  resources: StudyResource[];
  progress: {
    current_topic: number;
    topics_completed: number;
    total_study_hours: number;
  };
  
  // Settings
  is_private: boolean;
  requires_approval: boolean;
  study_method: 'collaborative' | 'competitive' | 'structured';
  
  // Status
  status: 'recruiting' | 'active' | 'completed' | 'paused';
  created_at: string;
  updated_at: string;
}

export interface StudyGroupMember {
  user_id: string;
  character_name: string;
  avatar_url?: string;
  role: 'leader' | 'moderator' | 'member';
  joined_at: string;
  
  // Progress tracking
  attendance_rate: number;
  study_hours: number;
  topics_mastered: number;
  contribution_score: number;
  
  // Status
  is_active: boolean;
  last_activity: string;
}

export interface StudyResource {
  id: string;
  title: string;
  description: string;
  type: 'document' | 'video' | 'quiz' | 'exercise' | 'link';
  url: string;
  uploaded_by: string;
  uploaded_at: string;
  
  // Metadata
  file_size?: number;
  duration?: number; // For videos
  difficulty_level: number;
  tags: string[];
  
  // Usage stats
  views_count: number;
  downloads_count: number;
  rating: number;
  reviews_count: number;
}

// API Response Types
export interface FriendsListResponse {
  friends: Friend[];
  total_count: number;
  online_count: number;
  has_more: boolean;
  next_cursor?: string;
}

export interface FriendRequestsResponse {
  sent_requests: FriendRequest[];
  received_requests: FriendRequest[];
  total_sent: number;
  total_received: number;
}

export interface FriendSuggestionsResponse {
  suggestions: FriendSuggestion[];
  total_count: number;
  algorithm_version: string;
}

export interface FriendActivitiesResponse {
  activities: FriendActivity[];
  total_count: number;
  has_more: boolean;
  next_cursor?: string;
}

export interface ChatRoomsResponse {
  rooms: ChatRoom[];
  total_count: number;
  unread_total: number;
}

export interface ChatMessagesResponse {
  messages: ChatMessage[];
  total_count: number;
  has_more: boolean;
  next_cursor?: string;
  participants: ChatParticipant[];
}

export interface GuildsResponse {
  guilds: Guild[];
  total_count: number;
  my_guilds: Guild[];
  recommended_guilds: Guild[];
}

export interface StudyGroupsResponse {
  study_groups: StudyGroup[];
  my_groups: StudyGroup[];
  recommended_groups: StudyGroup[];
  total_count: number;
}

// Search and Filter Types
export interface FriendSearchFilters {
  query?: string;
  status?: FriendStatus;
  online_status?: OnlineStatus;
  activity_type?: ActivityType;
  level_range?: { min: number; max: number };
  last_seen_days?: number;
  mutual_friends_min?: number;
  school?: string;
  interests?: string[];
}

export interface GuildSearchFilters {
  query?: string;
  category?: string;
  type?: 'public' | 'private' | 'invite_only';
  level_range?: { min: number; max: number };
  members_range?: { min: number; max: number };
  school_affiliated?: boolean;
  features?: string[];
  tags?: string[];
}

// Settings
export interface SocialSettings {
  user_id: string;
  
  // Privacy
  profile_visibility: 'public' | 'friends' | 'private';
  show_online_status: boolean;
  show_activity: boolean;
  show_achievements: boolean;
  show_location: boolean;
  
  // Friend requests
  accept_friend_requests: 'everyone' | 'friends_of_friends' | 'nobody';
  require_friend_request_message: boolean;
  auto_accept_mutual_friends: boolean;
  
  // Notifications
  notify_friend_requests: boolean;
  notify_friend_online: boolean;
  notify_friend_achievements: boolean;
  notify_guild_invites: boolean;
  notify_study_group_invites: boolean;
  
  // Chat
  allow_messages_from: 'everyone' | 'friends' | 'nobody';
  auto_mark_messages_read: boolean;
  show_typing_indicators: boolean;
  
  // Guild and Groups
  allow_guild_invites: boolean;
  allow_study_group_invites: boolean;
  auto_join_school_groups: boolean;
  
  updated_at: string;
}

export interface FriendshipStats {
  total_friends: number;
  online_friends: number;
  mutual_friends_avg: number;
  friendship_duration_avg: number; // days
  total_interactions: number;
  friendship_points_total: number;
  
  // Activity breakdown
  activities_by_type: Record<ActivityType, number>;
  interactions_by_type: Record<string, number>;
  
  // Timeline
  friends_added_this_week: number;
  friends_added_this_month: number;
  interactions_this_week: number;
  
  // Achievements
  social_achievements_unlocked: number;
  collaboration_achievements: number;
  mentorship_achievements: number;
}