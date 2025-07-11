import api from './api';
import { Quest, QuestProgress, QuestSubmission, QuestResult, QuestType, QuestDifficulty, QuestStatus } from '../types/quest';

interface QuestFilters {
  quest_type?: QuestType;
  difficulty?: QuestDifficulty;
  subject?: string;
  skip?: number;
  limit?: number;
}

interface DailyQuestSet {
  date: string;
  quests: Quest[];
  completed_count: number;
  total_count: number;
}

interface QuestStats {
  total_quests_available: number;
  quests_completed: number;
  quests_in_progress: number;
  total_exp_earned: number;
  total_coins_earned: number;
  total_gems_earned: number;
  completion_rate: number;
  average_score: number;
  quests_by_type: Record<string, { total: number; completed: number }>;
  quests_by_difficulty: Record<string, { total: number; completed: number }>;
}

class QuestService {
  async getQuests(filters?: QuestFilters): Promise<Quest[]> {
    const response = await api.get<Quest[]>('/quests/', { params: filters });
    return response.data;
  }

  async getQuest(id: number): Promise<Quest> {
    const response = await api.get<Quest>(`/quests/${id}`);
    return response.data;
  }

  async startQuest(questId: number): Promise<QuestProgress> {
    const response = await api.post<QuestProgress>(`/quests/${questId}/start`);
    return response.data;
  }

  async getMyQuestProgress(status?: QuestStatus): Promise<QuestProgress[]> {
    const response = await api.get<QuestProgress[]>('/quests/progress', {
      params: status ? { status } : undefined
    });
    return response.data;
  }

  async updateQuestProgress(questId: number, progress: Record<string, any>): Promise<QuestProgress> {
    const response = await api.put<QuestProgress>(`/quests/${questId}/progress`, { progress });
    return response.data;
  }

  async submitQuest(submission: QuestSubmission): Promise<QuestResult> {
    const response = await api.post<QuestResult>('/quests/submit', submission);
    return response.data;
  }

  async getDailyQuests(): Promise<DailyQuestSet> {
    const response = await api.get<DailyQuestSet>('/quests/daily');
    return response.data;
  }

  async getQuestRecommendations(limit: number = 5): Promise<Quest[]> {
    const response = await api.get<Quest[]>('/quests/recommendations', {
      params: { limit }
    });
    return response.data;
  }

  async getQuestStats(): Promise<QuestStats> {
    const response = await api.get<QuestStats>('/quests/stats');
    return response.data;
  }
}

export default new QuestService();