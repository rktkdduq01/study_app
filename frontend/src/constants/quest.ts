import { QuestType, QuestDifficulty } from '../types/quest';

export const QUEST_TYPE_LABELS: Record<QuestType, string> = {
  [QuestType.DAILY]: 'Daily',
  [QuestType.WEEKLY]: 'Weekly',
  [QuestType.SPECIAL]: 'Special',
  [QuestType.STORY]: 'Story',
  [QuestType.CHALLENGE]: 'Challenge',
  [QuestType.LESSON]: 'Lesson',
  [QuestType.QUIZ]: 'Quiz',
  [QuestType.PROJECT]: 'Project',
};

export const QUEST_DIFFICULTY_LABELS: Record<QuestDifficulty, string> = {
  [QuestDifficulty.EASY]: 'Easy',
  [QuestDifficulty.MEDIUM]: 'Medium',
  [QuestDifficulty.HARD]: 'Hard',
  [QuestDifficulty.EXPERT]: 'Expert',
};

export const QUEST_DIFFICULTY_COLORS: Record<QuestDifficulty, 'success' | 'warning' | 'error' | 'secondary'> = {
  [QuestDifficulty.EASY]: 'success',
  [QuestDifficulty.MEDIUM]: 'warning',
  [QuestDifficulty.HARD]: 'error',
  [QuestDifficulty.EXPERT]: 'secondary',
};

export const SUBJECT_LABELS: Record<string, string> = {
  math: 'Mathematics',
  korean: 'Korean',
  english: 'English',
  science: 'Science',
  social: 'Social Studies',
  history: 'History',
};

export const QUESTS_PER_PAGE = 12;