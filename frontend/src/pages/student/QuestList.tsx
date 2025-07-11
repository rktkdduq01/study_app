import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../../components/layout';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  
  Paper,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { 
  fetchQuests, 
  fetchMyQuestProgress, 
  startQuest,
  clearError,
} from '../../store/slices/questSlice';
import { useQuestFilters } from '../../hooks/useQuestFilters';
import { usePagination } from '../../hooks/usePagination';
import QuestFilters from '../../components/quest/QuestFilters';
import QuestCard from '../../components/quest/QuestCard';
import QuestListSkeleton from '../../components/quest/QuestListSkeleton';
import EmptyQuestList from '../../components/quest/EmptyQuestList';
import Pagination from '../../components/common/Pagination';
import { QUESTS_PER_PAGE } from '../../constants/quest';
import { QuestStatus } from '../../types/quest';

type TabValue = 'all' | 'available' | 'in_progress' | 'completed';

const QuestListPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  
  // Redux state
  const { quests, myProgress, isLoading, error } = useAppSelector((state) => state.quest);
  const { character } = useAppSelector((state) => state.character);
  
  // Local state
  const [tabValue, setTabValue] = useState<TabValue>('all');
  
  // Get filtered quests based on tab
  const tabFilteredQuests = useMemo(() => {
    switch (tabValue) {
      case 'available':
        const inProgressIds = myProgress
          .filter(p => p.status === QuestStatus.IN_PROGRESS)
          .map(p => p.quest_id);
        const completedIds = myProgress
          .filter(p => p.status === QuestStatus.COMPLETED)
          .map(p => p.quest_id);
        return quests.filter(q => 
          !inProgressIds.includes(q.id) && 
          !completedIds.includes(q.id)
        );
      
      case 'in_progress':
        const inProgressQuestIds = myProgress
          .filter(p => p.status === QuestStatus.IN_PROGRESS)
          .map(p => p.quest_id);
        return quests.filter(q => inProgressQuestIds.includes(q.id));
      
      case 'completed':
        const completedQuestIds = myProgress
          .filter(p => p.status === QuestStatus.COMPLETED)
          .map(p => p.quest_id);
        return quests.filter(q => completedQuestIds.includes(q.id));
      
      default:
        return quests;
    }
  }, [quests, myProgress, tabValue]);
  
  // Custom hooks
  const {
    filters,
    filteredQuests,
    activeFilterCount,
    updateFilter,
    resetFilters,
  } = useQuestFilters(tabFilteredQuests);
  
  const {
    currentPage,
    totalPages,
    startIndex,
    endIndex,
    goToPage,
    resetPage,
  } = usePagination({
    totalItems: filteredQuests.length,
    itemsPerPage: QUESTS_PER_PAGE,
  });
  
  // Get current page quests
  const currentQuests = useMemo(() => 
    filteredQuests.slice(startIndex, endIndex),
    [filteredQuests, startIndex, endIndex]
  );
  
  // Effects
  useEffect(() => {
    dispatch(fetchQuests());
    dispatch(fetchMyQuestProgress());
    
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);
  
  useEffect(() => {
    // Reset to first page when filters change
    resetPage();
  }, [filters, tabValue, resetPage]);
  
  // Handlers
  const handleTabChange = (_event: React.SyntheticEvent, newValue: TabValue) => {
    setTabValue(newValue);
  };
  
  const handleStartQuest = useCallback(async (questId: number) => {
    try {
      const characterId = character?.id;
      if (!characterId) {
        console.error('No character ID available');
        return;
      }
      const result = await dispatch(startQuest({ questId, characterId }));
      if (startQuest.fulfilled.match(result)) {
        navigate(`/student/quests/${questId}`);
      }
    } catch (error) {
      console.error('Failed to start quest:', error);
    }
  }, [dispatch, navigate, character]);
  
  const handleViewDetails = useCallback((questId: number) => {
    navigate(`/student/quests/${questId}`);
  }, [navigate]);
  
  // Helper function to get progress for a quest
  const getQuestProgress = (questId: number) => {
    return myProgress.find(p => p.quest_id === questId);
  };
  
  // Tab counts
  const tabCounts = useMemo(() => {
    const inProgressCount = myProgress.filter(p => p.status === QuestStatus.IN_PROGRESS).length;
    const completedCount = myProgress.filter(p => p.status === QuestStatus.COMPLETED).length;
    const availableCount = quests.length - inProgressCount - completedCount;
    
    return {
      all: quests.length,
      available: availableCount,
      in_progress: inProgressCount,
      completed: completedCount,
    };
  }, [quests, myProgress]);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Quest Library
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Choose your next learning adventure
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange}
          variant="fullWidth"
        >
          <Tab 
            label={`All Quests (${tabCounts.all})`} 
            value="all" 
          />
          <Tab 
            label={`Available (${tabCounts.available})`} 
            value="available" 
          />
          <Tab 
            label={`In Progress (${tabCounts.in_progress})`} 
            value="in_progress" 
          />
          <Tab 
            label={`Completed (${tabCounts.completed})`} 
            value="completed" 
          />
        </Tabs>
      </Paper>

      {/* Filters */}
      <QuestFilters
        filters={filters}
        activeFilterCount={activeFilterCount}
        onFilterChange={updateFilter}
        onResetFilters={resetFilters}
      />

      {/* Quest List */}
      {isLoading ? (
        <QuestListSkeleton count={QUESTS_PER_PAGE} />
      ) : filteredQuests.length === 0 ? (
        <EmptyQuestList
          hasFilters={activeFilterCount > 0 || tabValue !== 'all'}
          onResetFilters={() => {
            resetFilters();
            setTabValue('all');
          }}
        />
      ) : (
        <>
          <GridContainer spacing={3}>
            {currentQuests.map((quest) => (
              <Box 
                key={quest.id} 
                sx={{ 
                  width: { xs: '100%', sm: '50%', md: '33.333%' },
                  px: 1.5,
                  pb: 3
                }}
              >
                <QuestCard
                  quest={quest}
                  userLevel={character?.total_level || 1}
                  progress={getQuestProgress(quest.id)}
                  onStartQuest={handleStartQuest}
                  onViewDetails={handleViewDetails}
                />
              </Box>
            ))}
          </GridContainer>

          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalItems={filteredQuests.length}
            itemsPerPage={QUESTS_PER_PAGE}
            startIndex={startIndex}
            endIndex={endIndex}
            onPageChange={goToPage}
          />
        </>
      )}
    </Container>
  );
};

export default QuestListPage;
