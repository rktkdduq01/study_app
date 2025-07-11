import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { questService, Quest } from '../../services/questService';

// Quest interface is now imported from questService

interface QuestState {
  quests: Quest[];
  activeQuests: Quest[];
  completedQuests: Quest[];
  currentQuest: Quest | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: QuestState = {
  quests: [],
  activeQuests: [],
  completedQuests: [],
  currentQuest: null,
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchQuests = createAsyncThunk(
  'quest/fetchQuests',
  async (_, { rejectWithValue }) => {
    try {
      const quests = await questService.getQuests();
      return quests;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch quests');
    }
  }
);

export const startQuest = createAsyncThunk(
  'quest/startQuest',
  async (questId: number, { rejectWithValue }) => {
    try {
      // Mock API call
      const response = await fetch(`/api/quests/${questId}/start`, {
        method: 'POST',
      });
      const data = await response.json();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to start quest');
    }
  }
);

export const updateQuestProgress = createAsyncThunk(
  'quest/updateProgress',
  async (
    { questId, progress }: { questId: string; progress: number },
    { rejectWithValue }
  ) => {
    try {
      const quest = await questService.updateQuestProgress(questId, progress);
      return quest;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update quest progress');
    }
  }
);

export const completeQuest = createAsyncThunk(
  'quest/completeQuest',
  async (questId: string, { rejectWithValue }) => {
    try {
      const result = await questService.completeQuest(questId);
      return result;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to complete quest');
    }
  }
);

export const startQuest = createAsyncThunk(
  'quest/startQuest',
  async (questId: string, { rejectWithValue }) => {
    try {
      const quest = await questService.startQuest(questId);
      return { quest };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to start quest');
    }
  }
);

const questSlice = createSlice({
  name: 'quest',
  initialState,
  reducers: {
    setCurrentQuest: (state, action: PayloadAction<Quest | null>) => {
      state.currentQuest = action.payload;
    },
    updateLocalProgress: (
      state,
      action: PayloadAction<{ questId: string; progress: number }>
    ) => {
      const { questId, progress } = action.payload;
      const quest = state.quests.find(q => q.id === questId);
      if (quest) {
        quest.progress = progress;
      }
      const activeQuest = state.activeQuests.find(q => q.id === questId);
      if (activeQuest) {
        activeQuest.progress = progress;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
    resetQuestState: (state) => {
      state.quests = [];
      state.activeQuests = [];
      state.completedQuests = [];
      state.currentQuest = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch quests
      .addCase(fetchQuests.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchQuests.fulfilled, (state, action) => {
        state.isLoading = false;
        state.quests = action.payload;
        state.activeQuests = action.payload.filter(
          (q: Quest) => q.status === 'active'
        );
        state.completedQuests = action.payload.filter(
          (q: Quest) => q.status === 'completed'
        );
      })
      .addCase(fetchQuests.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Start quest
      .addCase(startQuest.fulfilled, (state, action) => {
        const quest = action.payload.quest;
        const questIndex = state.quests.findIndex(q => q.id === quest.id);
        if (questIndex !== -1) {
          state.quests[questIndex] = quest;
        }
        state.activeQuests.push(quest);
      })
      
      // Update quest progress
      .addCase(updateQuestProgress.fulfilled, (state, action) => {
        const quest = action.payload.quest;
        const questIndex = state.quests.findIndex(q => q.id === quest.id);
        if (questIndex !== -1) {
          state.quests[questIndex] = quest;
        }
        const activeQuestIndex = state.activeQuests.findIndex(q => q.id === quest.id);
        if (activeQuestIndex !== -1) {
          state.activeQuests[activeQuestIndex] = quest;
        }
      })
      
      // Complete quest
      .addCase(completeQuest.fulfilled, (state, action) => {
        const quest = action.payload.quest;
        const questIndex = state.quests.findIndex(q => q.id === quest.id);
        if (questIndex !== -1) {
          state.quests[questIndex] = quest;
        }
        
        // Remove from active quests
        state.activeQuests = state.activeQuests.filter(q => q.id !== quest.id);
        
        // Add to completed quests
        state.completedQuests.push(quest);
      });
  },
});

export const {
  setCurrentQuest,
  updateLocalProgress,
  clearError,
  resetQuestState,
} = questSlice.actions;

export default questSlice.reducer;