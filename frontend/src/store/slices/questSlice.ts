import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import questService from '../../services/questService';
import { Quest, QuestProgress, QuestSubmission, QuestResult, QuestType, QuestDifficulty, QuestStatus } from '../../types/quest';

interface QuestState {
  // All available quests in the system
  quests: Quest[];
  
  // Currently selected/active quest for detailed view
  currentQuest: Quest | null;
  
  // User's progress on all quests (started, completed, failed)
  myProgress: QuestProgress[];
  
  // Daily quest set with completion tracking
  // Resets at midnight UTC
  dailyQuests: {
    date: string;
    quests: Quest[];
    completed_count: number;  // For daily streak tracking
    total_count: number;      // Usually 3-5 based on level
  } | null;
  
  // AI-powered personalized quest recommendations
  recommendations: Quest[];
  
  // Result of most recent quest submission
  // Contains score, rewards, and feedback
  questResult: QuestResult | null;
  
  // UI state management
  isLoading: boolean;
  error: string | null;
}

const initialState: QuestState = {
  quests: [],
  currentQuest: null,
  myProgress: [],
  dailyQuests: null,
  recommendations: [],
  questResult: null,
  isLoading: false,
  error: null,
};

// Async thunks for quest operations

/**
 * Fetch all available quests with optional filtering.
 * Used for quest browser and exploration features.
 * 
 * Filters:
 * - quest_type: DAILY, MAIN, CHALLENGE, TUTORIAL
 * - difficulty: EASY, MEDIUM, HARD, EXPERT
 * - subject: Math, Science, Language, etc.
 */
export const fetchQuests = createAsyncThunk(
  'quest/fetchAll',
  async (filters?: { quest_type?: QuestType; difficulty?: QuestDifficulty; subject?: string }) => {
    return await questService.getQuests(filters);
  }
);

export const fetchQuest = createAsyncThunk(
  'quest/fetchOne',
  async (id: number) => {
    return await questService.getQuest(id);
  }
);

export const fetchQuestById = createAsyncThunk(
  'quest/fetchById',
  async (id: number) => {
    return await questService.getQuest(id);
  }
);

/**
 * Start a new quest attempt.
 * 
 * Process:
 * 1. Validates prerequisites are met
 * 2. Checks energy/stamina requirements
 * 3. Creates QuestProgress record
 * 4. Initializes timer if time-limited
 * 5. Loads first question/objective
 * 
 * Note: characterId included for future multi-character support
 */
export const startQuest = createAsyncThunk(
  'quest/start',
  async ({ questId, characterId }: { questId: number; characterId: number }) => {
    return await questService.startQuest(questId);
  }
);

export const submitQuestAnswer = createAsyncThunk(
  'quest/submitAnswer',
  async ({ questId, questionIndex, answer }: { questId: number; questionIndex: number; answer: string }) => {
    // This would need to be implemented in the service
    return { questId, questionIndex, answer, correct: true };
  }
);

export const completeQuest = createAsyncThunk(
  'quest/complete',
  async ({ questId, timeSpent }: { questId: number; timeSpent: number }) => {
    return await questService.submitQuest({
      quest_id: questId,
      answers: {},
      time_spent: timeSpent,
    });
  }
);

export const fetchMyQuestProgress = createAsyncThunk(
  'quest/fetchProgress',
  async (status?: QuestStatus) => {
    return await questService.getMyQuestProgress(status);
  }
);

/**
 * Submit completed quest for evaluation.
 * 
 * Submission includes:
 * - All answers provided by user
 * - Time spent on quest
 * - Number of hints used
 * - Client-side validation results
 * 
 * Returns:
 * - Score (0-100)
 * - Rewards earned (XP, coins, gems)
 * - Detailed feedback on mistakes
 * - Achievement unlocks
 * - Next quest recommendations
 */
export const submitQuest = createAsyncThunk(
  'quest/submit',
  async (submission: QuestSubmission) => {
    return await questService.submitQuest(submission);
  }
);

/**
 * Fetch user's daily quest set.
 * 
 * Daily Quest System:
 * - 3-5 quests based on user level
 * - Mix of subjects for balanced learning
 * - Bonus rewards for completing all
 * - Contributes to daily streak
 * 
 * Automatically handles timezone conversion
 */
export const fetchDailyQuests = createAsyncThunk(
  'quest/fetchDaily',
  async () => {
    return await questService.getDailyQuests();
  }
);

/**
 * Get AI-powered quest recommendations.
 * 
 * Recommendation algorithm considers:
 * - User's performance history
 * - Learning goals and preferences  
 * - Skill gaps that need addressing
 * - Optimal difficulty progression
 * - Subject variety for engagement
 * 
 * Default limit of 5 for UI display
 */
export const fetchQuestRecommendations = createAsyncThunk(
  'quest/fetchRecommendations',
  async (limit: number = 5) => {
    return await questService.getQuestRecommendations(limit);
  }
);

// Slice
const questSlice = createSlice({
  name: 'quest',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearQuestResult: (state) => {
      state.questResult = null;
    },
    setCurrentQuest: (state, action) => {
      state.currentQuest = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Handle async quest fetching
    // Updates loading state for UI spinners/skeletons
    builder
      .addCase(fetchQuests.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchQuests.fulfilled, (state, action) => {
        state.isLoading = false;
        state.quests = action.payload;
      })
      .addCase(fetchQuests.rejected, (state, action) => {
        state.isLoading = false;
        // Provide user-friendly error messages
        state.error = action.error.message || 'Failed to fetch quests';
      });

    // Fetch single quest
    builder
      .addCase(fetchQuest.fulfilled, (state, action) => {
        state.currentQuest = action.payload;
      });

    // Fetch quest by ID
    builder
      .addCase(fetchQuestById.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchQuestById.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentQuest = action.payload;
      })
      .addCase(fetchQuestById.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch quest';
      });

    // Submit quest answer
    builder
      .addCase(submitQuestAnswer.fulfilled, (state, action) => {
        // Update progress or state as needed
      });

    // Complete quest
    builder
      .addCase(completeQuest.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(completeQuest.fulfilled, (state, action) => {
        state.isLoading = false;
        state.questResult = action.payload;
        // Update progress
        const progressIndex = state.myProgress.findIndex(p => p.quest_id === action.payload.quest_id);
        if (progressIndex >= 0) {
          state.myProgress[progressIndex].status = QuestStatus.COMPLETED;
          state.myProgress[progressIndex].completion_percentage = 100;
        }
      })
      .addCase(completeQuest.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to complete quest';
      });

    // Start quest
    builder
      .addCase(startQuest.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(startQuest.fulfilled, (state, action) => {
        state.isLoading = false;
        // Add to progress if not already there
        const existingIndex = state.myProgress.findIndex(p => p.id === action.payload.id);
        if (existingIndex >= 0) {
          state.myProgress[existingIndex] = action.payload;
        } else {
          state.myProgress.push(action.payload);
        }
      })
      .addCase(startQuest.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to start quest';
      });

    // Fetch progress
    builder
      .addCase(fetchMyQuestProgress.fulfilled, (state, action) => {
        state.myProgress = action.payload;
      });

    // Submit quest
    builder
      .addCase(submitQuest.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(submitQuest.fulfilled, (state, action) => {
        state.isLoading = false;
        state.questResult = action.payload;
      })
      .addCase(submitQuest.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to submit quest';
      });

    // Fetch daily quests
    builder
      .addCase(fetchDailyQuests.fulfilled, (state, action) => {
        state.dailyQuests = action.payload;
      });

    // Fetch recommendations
    builder
      .addCase(fetchQuestRecommendations.fulfilled, (state, action) => {
        state.recommendations = action.payload;
      });
  },
});

export const { clearError, clearQuestResult, setCurrentQuest } = questSlice.actions;
export default questSlice.reducer;