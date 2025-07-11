// Mentoring System Types

export enum MentorshipStatus {
  PENDING = 'pending',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  PAUSED = 'paused'
}

export enum MentorshipType {
  ACADEMIC = 'academic',        // 학업 멘토링
  CAREER = 'career',           // 진로 멘토링
  SKILL = 'skill',             // 특정 기술 멘토링
  PERSONAL = 'personal',       // 개인 성장 멘토링
  PROJECT = 'project',         // 프로젝트 기반 멘토링
  PEER = 'peer'               // 동료 멘토링
}

export enum SessionStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show',
  RESCHEDULED = 'rescheduled'
}

export enum SessionType {
  ONE_ON_ONE = 'one_on_one',
  GROUP = 'group',
  WORKSHOP = 'workshop',
  REVIEW = 'review',
  GOAL_SETTING = 'goal_setting',
  PROGRESS_CHECK = 'progress_check'
}

export enum MentorLevel {
  JUNIOR = 'junior',           // 주니어 멘토 (경험 1년 미만)
  INTERMEDIATE = 'intermediate', // 중급 멘토 (1-3년)
  SENIOR = 'senior',           // 시니어 멘토 (3-5년)
  EXPERT = 'expert',           // 전문가 멘토 (5년 이상)
  MASTER = 'master'            // 마스터 멘토 (10년 이상 + 인증)
}

export enum MatchingCriteria {
  SUBJECT_EXPERTISE = 'subject_expertise',
  LEARNING_STYLE = 'learning_style',
  PERSONALITY = 'personality',
  AVAILABILITY = 'availability',
  GOALS_ALIGNMENT = 'goals_alignment',
  COMMUNICATION_STYLE = 'communication_style',
  EXPERIENCE_LEVEL = 'experience_level'
}

// Core Entities
export interface MentorProfile {
  id: string;
  user_id: string;
  character_id: string;
  
  // Basic Info
  character_name: string;
  avatar_url?: string;
  bio: string;
  tagline: string; // 한 줄 소개
  
  // Expertise
  subjects: string[];           // 전문 과목
  skills: string[];            // 보유 기술
  certifications: string[];    // 자격증/인증
  achievements: string[];      // 주요 성취
  
  // Mentoring Info
  mentor_level: MentorLevel;
  mentoring_types: MentorshipType[];
  total_mentees: number;
  active_mentees: number;
  max_mentees: number;
  
  // Experience
  mentoring_experience_years: number;
  total_sessions_completed: number;
  success_rate: number;        // 성공 완료율
  
  // Ratings & Reviews
  average_rating: number;
  total_reviews: number;
  response_rate: number;       // 응답률
  response_time_hours: number; // 평균 응답 시간
  
  // Availability
  available_days: string[];    // ['monday', 'tuesday', ...]
  available_hours: {
    start: string;             // "09:00"
    end: string;              // "18:00"
  };
  timezone: string;
  preferred_session_duration: number; // minutes
  
  // Preferences
  preferred_communication: string[]; // ['chat', 'video', 'voice']
  languages: string[];
  teaching_style: string;
  learning_styles_supported: string[];
  
  // Pricing (if paid mentoring)
  is_paid: boolean;
  hourly_rate?: number;
  free_consultation_minutes: number;
  
  // Status
  is_available: boolean;
  is_verified: boolean;
  is_featured: boolean;
  last_active: string;
  
  // Social Proof
  recommendation_count: number;
  badge_earned: string[];
  
  created_at: string;
  updated_at: string;
}

export interface MenteeProfile {
  id: string;
  user_id: string;
  character_id: string;
  
  // Basic Info
  character_name: string;
  avatar_url?: string;
  grade_level: string;         // "초등학교 6학년", "중학교 2학년"
  school_name?: string;
  
  // Learning Info
  subjects_of_interest: string[];
  current_subjects: string[];
  struggling_subjects: string[];
  strong_subjects: string[];
  
  // Goals
  short_term_goals: string[];  // 단기 목표
  long_term_goals: string[];   // 장기 목표
  specific_challenges: string[]; // 구체적인 어려움
  
  // Preferences
  preferred_mentoring_types: MentorshipType[];
  preferred_communication: string[];
  preferred_session_times: string[];
  learning_style: string;      // 'visual', 'auditory', 'kinesthetic', 'reading'
  
  // Current Status
  current_mentor_id?: string;
  previous_mentors: string[];
  total_sessions_attended: number;
  
  // Matching Preferences
  mentor_gender_preference?: 'male' | 'female' | 'no_preference';
  mentor_age_preference?: {
    min: number;
    max: number;
  };
  mentor_experience_preference: MentorLevel[];
  
  created_at: string;
  updated_at: string;
}

export interface MentorshipRelationship {
  id: string;
  mentor_id: string;
  mentee_id: string;
  
  // Relationship Info
  type: MentorshipType;
  status: MentorshipStatus;
  start_date: string;
  end_date?: string;
  expected_duration_weeks: number;
  
  // Goals & Progress
  goals: MentorshipGoal[];
  progress_milestones: ProgressMilestone[];
  overall_progress_percentage: number;
  
  // Session Info
  total_sessions_planned: number;
  sessions_completed: number;
  sessions_remaining: number;
  last_session_date?: string;
  next_session_date?: string;
  
  // Agreement
  meeting_frequency: 'weekly' | 'biweekly' | 'monthly' | 'as_needed';
  session_duration_minutes: number;
  communication_preferences: string[];
  ground_rules: string[];
  
  // Evaluation
  mentor_satisfaction: number;  // 1-5
  mentee_satisfaction: number;  // 1-5
  mentor_feedback?: string;
  mentee_feedback?: string;
  
  // Financial (if paid)
  is_paid: boolean;
  total_cost?: number;
  payment_status?: 'pending' | 'paid' | 'overdue' | 'refunded';
  
  created_at: string;
  updated_at: string;
}

export interface MentorshipGoal {
  id: string;
  mentorship_id: string;
  title: string;
  description: string;
  category: string;            // 'academic', 'skill', 'personal', 'career'
  priority: 'low' | 'medium' | 'high' | 'urgent';
  
  // Timeline
  target_date: string;
  created_date: string;
  
  // Progress
  is_completed: boolean;
  completion_date?: string;
  progress_percentage: number;
  
  // Measurement
  success_criteria: string[];
  measurement_method: string;
  
  // Tracking
  milestones: string[];
  resources_needed: string[];
  obstacles: string[];
  
  // Evaluation
  mentor_notes?: string;
  mentee_notes?: string;
  reflection?: string;
}

export interface ProgressMilestone {
  id: string;
  mentorship_id: string;
  goal_id?: string;
  
  title: string;
  description: string;
  due_date: string;
  completed_date?: string;
  is_completed: boolean;
  
  // Evidence
  evidence_type: 'assignment' | 'test_score' | 'project' | 'reflection' | 'observation';
  evidence_data?: any;
  
  // Feedback
  mentor_feedback?: string;
  mentee_reflection?: string;
  
  created_at: string;
}

export interface MentorshipSession {
  id: string;
  mentorship_id: string;
  mentor_id: string;
  mentee_id: string;
  
  // Session Details
  title: string;
  description?: string;
  type: SessionType;
  status: SessionStatus;
  
  // Scheduling
  scheduled_start: string;
  scheduled_end: string;
  actual_start?: string;
  actual_end?: string;
  duration_minutes: number;
  
  // Location/Platform
  meeting_type: 'in_person' | 'video_call' | 'phone_call' | 'chat';
  meeting_link?: string;
  meeting_location?: string;
  meeting_room_id?: string;
  
  // Content
  agenda: string[];
  topics_covered: string[];
  resources_shared: string[];
  homework_assigned: string[];
  
  // Outcomes
  session_summary?: string;
  mentor_notes?: string;
  mentee_notes?: string;
  action_items: ActionItem[];
  
  // Evaluation
  mentor_rating?: number;       // 1-5
  mentee_rating?: number;       // 1-5
  mentor_feedback?: string;
  mentee_feedback?: string;
  
  // Attendance
  mentor_attended: boolean;
  mentee_attended: boolean;
  late_start_minutes?: number;
  early_end_minutes?: number;
  
  // Follow-up
  follow_up_required: boolean;
  follow_up_date?: string;
  next_session_topics?: string[];
  
  created_at: string;
  updated_at: string;
}

export interface ActionItem {
  id: string;
  session_id: string;
  assigned_to: 'mentor' | 'mentee' | 'both';
  
  title: string;
  description: string;
  due_date: string;
  priority: 'low' | 'medium' | 'high';
  
  is_completed: boolean;
  completion_date?: string;
  completion_notes?: string;
  
  resources: string[];
  
  created_at: string;
}

export interface MentorshipMatch {
  id: string;
  mentor_id: string;
  mentee_id: string;
  
  // Matching Info
  compatibility_score: number; // 0-100
  match_criteria: MatchingCriteria[];
  match_reasons: string[];
  algorithm_version: string;
  
  // Status
  status: 'suggested' | 'pending_mentor' | 'pending_mentee' | 'accepted' | 'declined' | 'expired';
  suggested_date: string;
  response_deadline: string;
  accepted_date?: string;
  declined_date?: string;
  decline_reason?: string;
  
  // Details
  mentor_message?: string;      // 멘토의 매칭 제안 메시지
  mentee_message?: string;      // 멘티의 매칭 요청 메시지
  
  // Compatibility Analysis
  subject_match_score: number;
  schedule_match_score: number;
  personality_match_score: number;
  communication_match_score: number;
  experience_match_score: number;
  
  // Recommendations
  suggested_session_frequency: string;
  suggested_duration_weeks: number;
  suggested_focus_areas: string[];
  
  created_at: string;
  updated_at: string;
}

export interface MentorshipReview {
  id: string;
  mentorship_id: string;
  reviewer_id: string;
  reviewer_type: 'mentor' | 'mentee';
  
  // Ratings
  overall_rating: number;       // 1-5
  communication_rating: number;
  expertise_rating: number;
  reliability_rating: number;
  helpfulness_rating: number;
  
  // Review Content
  title: string;
  review_text: string;
  pros: string[];
  cons: string[];
  recommendations: string[];
  
  // Context
  relationship_duration_weeks: number;
  sessions_attended: number;
  goals_achieved: number;
  
  // Moderation
  is_verified: boolean;
  is_featured: boolean;
  helpful_votes: number;
  reported_count: number;
  
  created_at: string;
  updated_at: string;
}

// Search and Filtering
export interface MentorSearchFilters {
  subjects?: string[];
  mentoring_types?: MentorshipType[];
  mentor_levels?: MentorLevel[];
  availability?: {
    days: string[];
    time_range: {
      start: string;
      end: string;
    };
  };
  rating_min?: number;
  max_hourly_rate?: number;
  languages?: string[];
  is_verified_only?: boolean;
  response_time_max_hours?: number;
  teaching_styles?: string[];
  has_free_consultation?: boolean;
}

export interface MenteeSearchFilters {
  subjects?: string[];
  grade_levels?: string[];
  goals?: string[];
  learning_styles?: string[];
  preferred_mentoring_types?: MentorshipType[];
  availability?: {
    days: string[];
    time_range: {
      start: string;
      end: string;
    };
  };
}

// Analytics and Statistics
export interface MentorshipStats {
  // Overall Stats
  total_mentorships: number;
  active_mentorships: number;
  completed_mentorships: number;
  success_rate: number;
  
  // Session Stats
  total_sessions: number;
  average_session_duration: number;
  most_popular_session_types: { type: SessionType; count: number }[];
  
  // Goal Achievement
  goals_set: number;
  goals_achieved: number;
  goal_achievement_rate: number;
  
  // Satisfaction
  average_mentor_satisfaction: number;
  average_mentee_satisfaction: number;
  net_promoter_score: number;
  
  // Growth
  new_mentorships_this_month: number;
  growth_rate_percentage: number;
  
  // Popular Categories
  popular_subjects: { subject: string; count: number }[];
  popular_mentoring_types: { type: MentorshipType; count: number }[];
  
  // Performance Metrics
  average_response_time_hours: number;
  mentor_retention_rate: number;
  mentee_retention_rate: number;
}

export interface PersonalMentorshipStats {
  // As Mentor
  total_mentees: number;
  active_mentees: number;
  completed_mentorships: number;
  total_sessions_given: number;
  average_mentee_rating: number;
  
  // As Mentee
  current_mentor?: string;
  total_mentors: number;
  total_sessions_attended: number;
  goals_achieved: number;
  average_mentor_rating: number;
  
  // Progress
  current_goals: number;
  completed_goals: number;
  goal_completion_rate: number;
  
  // Recognition
  badges_earned: string[];
  certifications_earned: string[];
  recommendations_received: number;
  
  // Time Investment
  total_hours_mentored: number;
  total_hours_received: number;
  average_session_length: number;
  
  // Engagement
  last_session_date?: string;
  upcoming_sessions: number;
  response_rate: number;
  
  // Growth
  skill_improvements: { skill: string; before: number; after: number }[];
  subject_progress: { subject: string; improvement_percentage: number }[];
}

// API Response Types
export interface MentorListResponse {
  mentors: MentorProfile[];
  total_count: number;
  page: number;
  per_page: number;
  has_more: boolean;
  filters_applied: MentorSearchFilters;
}

export interface MenteeListResponse {
  mentees: MenteeProfile[];
  total_count: number;
  page: number;
  per_page: number;
  has_more: boolean;
  filters_applied: MenteeSearchFilters;
}

export interface MatchSuggestionsResponse {
  matches: MentorshipMatch[];
  total_suggestions: number;
  algorithm_explanation: string;
  refresh_recommendations_in_hours: number;
}

export interface SessionScheduleResponse {
  upcoming_sessions: MentorshipSession[];
  past_sessions: MentorshipSession[];
  session_conflicts: {
    session_id: string;
    conflict_type: string;
    description: string;
  }[];
}

// Notification Types
export interface MentorshipNotification {
  id: string;
  type: 'match_suggestion' | 'session_reminder' | 'goal_deadline' | 'review_request' | 'milestone_achieved';
  mentorship_id?: string;
  session_id?: string;
  match_id?: string;
  
  title: string;
  message: string;
  action_required: boolean;
  action_url?: string;
  
  created_at: string;
  expires_at?: string;
  is_read: boolean;
}

// Communication Templates
export interface MessageTemplate {
  id: string;
  category: 'introduction' | 'session_reminder' | 'goal_setting' | 'progress_update' | 'completion';
  title: string;
  content: string;
  variables: string[];        // ['mentee_name', 'session_date', etc.]
  is_default: boolean;
  usage_count: number;
}

export interface MentorshipSettings {
  user_id: string;
  
  // Matching Preferences
  auto_accept_matches: boolean;
  match_notification_frequency: 'immediate' | 'daily' | 'weekly';
  max_simultaneous_relationships: number;
  
  // Communication
  default_response_time_hours: number;
  allow_weekend_communication: boolean;
  preferred_communication_channels: string[];
  
  // Session Preferences
  default_session_duration: number;
  advance_notice_required_hours: number;
  allow_last_minute_booking: boolean;
  
  // Privacy
  profile_visibility: 'public' | 'registered_users' | 'verified_only';
  show_real_name: boolean;
  show_contact_info: boolean;
  
  // Notifications
  email_notifications: boolean;
  push_notifications: boolean;
  sms_notifications: boolean;
  
  updated_at: string;
}

// Matching Algorithm Data
export interface MatchingAlgorithmData {
  user_id: string;
  
  // Behavioral Data
  login_frequency: number;
  session_attendance_rate: number;
  response_rate: number;
  goal_completion_rate: number;
  
  // Preference Learning
  preferred_mentor_characteristics: string[];
  successful_relationship_patterns: string[];
  communication_style_analysis: string;
  
  // Performance Metrics
  learning_speed: number;
  engagement_level: number;
  feedback_quality: number;
  
  last_updated: string;
}