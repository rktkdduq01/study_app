import { Quest, QuestDifficulty } from '../types/quest';
import { QUEST_DIFFICULTY_COLORS } from '../constants/quest';

export const getDifficultyColor = (difficulty: QuestDifficulty) => {
  return QUEST_DIFFICULTY_COLORS[difficulty] || 'default';
};

export const calculateQuestDuration = (minutes?: number): string => {
  if (!minutes) return 'No time limit';
  
  if (minutes < 60) {
    return `${minutes} min`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  if (remainingMinutes === 0) {
    return `${hours} hr${hours > 1 ? 's' : ''}`;
  }
  
  return `${hours} hr ${remainingMinutes} min`;
};

export const getRewardSummary = (quest: Quest): string[] => {
  const rewards: string[] = [];
  
  if (quest.exp_reward > 0) {
    rewards.push(`${quest.exp_reward} XP`);
  }
  
  if (quest.coin_reward > 0) {
    rewards.push(`${quest.coin_reward} Coins`);
  }
  
  if (quest.gem_reward > 0) {
    rewards.push(`${quest.gem_reward} Gems`);
  }
  
  return rewards;
};

export const canStartQuest = (quest: Quest, userLevel: number): boolean => {
  return userLevel >= quest.min_level;
};

export const isQuestNew = (quest: Quest): boolean => {
  const createdDate = new Date(quest.created_at);
  const daysSinceCreation = (Date.now() - createdDate.getTime()) / (1000 * 60 * 60 * 24);
  return daysSinceCreation <= 3; // Consider new if created within 3 days
};