export enum QuestType {
  DAILY = 'daily',
  WEEKLY = 'weekly',
  SPECIAL = 'special',
  STORY = 'story',
  CHALLENGE = 'challenge',
  LESSON = 'lesson',
  QUIZ = 'quiz',
  PROJECT = 'project'
}

export enum QuestDifficulty {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard',
  EXPERT = 'expert'
}

export enum QuestStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  EXPIRED = 'expired'
}

export interface Quest {
  id: number;
  title: string;
  description: string;
  long_description?: string;
  type: QuestType;
  quest_type?: QuestType; // For backward compatibility
  difficulty: QuestDifficulty;
  subject: string;
  objectives: string[];
  content?: {
    questions?: Array<{
      question: string;
      type: 'multiple_choice' | 'short_answer';
      options?: string[];
      correct_answer?: string;
    }>;
    lesson?: string;
  };
  exp_reward: number;
  coin_reward: number;
  gem_reward: number;
  achievement_points: number;
  estimated_duration: number;
  time_limit_minutes?: number;
  min_level: number;
  max_attempts?: number;
  prerequisites?: string[];
  is_repeatable: boolean;
  cooldown_hours?: number;
  is_active: boolean;
  completion_rate?: number;
  average_completion_time?: number;
  total_attempts?: number;
  user_progress?: QuestProgress[];
  achievement_unlocks?: Array<{
    id: number;
    name: string;
    description: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface QuestProgress {
  id: number;
  user_id: number;
  quest_id: number;
  status: QuestStatus;
  progress: Record<string, any>;
  completion_percentage: number;
  attempts: number;
  started_at?: string;
  completed_at?: string;
  last_attempt_at?: string;
  created_at: string;
  updated_at: string;
  quest?: Quest;
}

export interface QuestSubmission {
  quest_id: number;
  quest_progress_id?: number;
  answers: Record<string, any>;
  time_spent?: number;
  time_spent_seconds?: number;
}

export interface QuestResult {
  quest_id: number;
  quest_progress_id: number;
  is_correct: boolean;
  score: number;
  feedback?: string;
  exp_earned: number;
  coins_earned: number;
  gems_earned: number;
  achievement_points_earned: number;
  objectives_completed: string[];
  new_achievements: number[];
}