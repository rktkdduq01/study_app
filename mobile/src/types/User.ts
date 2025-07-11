export interface User {
  id: number;
  username: string;
  email: string;
  role: 'student' | 'teacher' | 'admin';
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  profile?: {
    full_name?: string;
    avatar?: string;
    bio?: string;
    date_of_birth?: string;
    location?: string;
    education_level?: string;
    interests?: string[];
  };
  settings?: {
    notifications_enabled: boolean;
    email_notifications: boolean;
    sound_enabled: boolean;
    vibration_enabled: boolean;
    theme: 'light' | 'dark' | 'auto';
    language: string;
  };
  statistics?: {
    total_study_time: number;
    lessons_completed: number;
    quests_completed: number;
    achievements_unlocked: number;
    current_streak: number;
    longest_streak: number;
    total_xp: number;
    level: number;
  };
}