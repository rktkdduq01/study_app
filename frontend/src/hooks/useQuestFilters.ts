import { useState, useCallback, useMemo } from 'react';
import { QuestType, QuestDifficulty, Quest } from '../types/quest';

export interface QuestFilters {
  type: QuestType | 'all';
  difficulty: QuestDifficulty | 'all';
  subject: string | 'all';
  searchQuery: string;
}

const initialFilters: QuestFilters = {
  type: 'all',
  difficulty: 'all',
  subject: 'all',
  searchQuery: '',
};

export const useQuestFilters = (quests: Quest[]) => {
  const [filters, setFilters] = useState<QuestFilters>(initialFilters);

  const updateFilter = useCallback(<K extends keyof QuestFilters>(
    key: K,
    value: QuestFilters[K]
  ) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(initialFilters);
  }, []);

  const filteredQuests = useMemo(() => {
    return quests.filter(quest => {
      // Type filter
      if (filters.type !== 'all' && quest.quest_type !== filters.type) {
        return false;
      }

      // Difficulty filter
      if (filters.difficulty !== 'all' && quest.difficulty !== filters.difficulty) {
        return false;
      }

      // Subject filter
      if (filters.subject !== 'all' && quest.subject !== filters.subject) {
        return false;
      }

      // Search query filter
      if (filters.searchQuery) {
        const query = filters.searchQuery.toLowerCase();
        const matchesTitle = quest.title.toLowerCase().includes(query);
        const matchesDescription = quest.description.toLowerCase().includes(query);
        return matchesTitle || matchesDescription;
      }

      return true;
    });
  }, [quests, filters]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.type !== 'all') count++;
    if (filters.difficulty !== 'all') count++;
    if (filters.subject !== 'all') count++;
    if (filters.searchQuery) count++;
    return count;
  }, [filters]);

  return {
    filters,
    filteredQuests,
    activeFilterCount,
    updateFilter,
    resetFilters,
  };
};