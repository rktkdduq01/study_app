import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { achievementService, Achievement } from '../../services/achievementService';

// Achievement interface is now imported from achievementService

interface AchievementState {
  achievements: Achievement[];
  unlockedAchievements: Achievement[];
  recentlyUnlocked: Achievement[];
  isLoading: boolean;
  error: string | null;
}

const initialState: AchievementState = {
  achievements: [],
  unlockedAchievements: [],
  recentlyUnlocked: [],
  isLoading: false,
  error: null,
};

// Async thunks
export const fetchAchievements = createAsyncThunk(
  'achievement/fetchAchievements',
  async (_, { rejectWithValue }) => {
    try {
      const achievements = await achievementService.getAchievements();
      return achievements;
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to fetch achievements');
    }
  }
);

export const unlockAchievement = createAsyncThunk(
  'achievement/unlockAchievement',
  async (achievementId: string, { rejectWithValue }) => {
    try {
      const achievement = await achievementService.unlockAchievement(achievementId);
      return { achievement };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to unlock achievement');
    }
  }
);

export const updateAchievementProgress = createAsyncThunk(
  'achievement/updateProgress',
  async (
    { achievementId, progress }: { achievementId: string; progress: number },
    { rejectWithValue }
  ) => {
    try {
      const achievement = await achievementService.updateAchievementProgress(achievementId, progress);
      return { achievement };
    } catch (error: any) {
      return rejectWithValue(error.message || 'Failed to update achievement progress');
    }
  }
);

const achievementSlice = createSlice({
  name: 'achievement',
  initialState,
  reducers: {
    updateProgress: (
      state,
      action: PayloadAction<{ achievementId: string; progress: number }>
    ) => {
      const { achievementId, progress } = action.payload;
      const achievement = state.achievements.find(a => a.id === achievementId);
      if (achievement) {
        achievement.progress = Math.min(progress, achievement.max_progress || 100);
      }
    },
    markAsRecentlyUnlocked: (state, action: PayloadAction<Achievement>) => {
      state.recentlyUnlocked.push(action.payload);
    },
    clearRecentlyUnlocked: (state) => {
      state.recentlyUnlocked = [];
    },
    clearError: (state) => {
      state.error = null;
    },
    resetAchievementState: (state) => {
      state.achievements = [];
      state.unlockedAchievements = [];
      state.recentlyUnlocked = [];
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch achievements
      .addCase(fetchAchievements.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchAchievements.fulfilled, (state, action) => {
        state.isLoading = false;
        state.achievements = action.payload;
        state.unlockedAchievements = action.payload.filter(
          (a: Achievement) => a.unlocked
        );
      })
      .addCase(fetchAchievements.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Unlock achievement
      .addCase(unlockAchievement.fulfilled, (state, action) => {
        const achievement = action.payload.achievement;
        const achievementIndex = state.achievements.findIndex(a => a.id === achievement.id);
        if (achievementIndex !== -1) {
          state.achievements[achievementIndex] = achievement;
        }
        
        if (achievement.unlocked) {
          state.unlockedAchievements.push(achievement);
          state.recentlyUnlocked.push(achievement);
        }
      })
      
      // Update achievement progress
      .addCase(updateAchievementProgress.fulfilled, (state, action) => {
        const achievement = action.payload.achievement;
        const achievementIndex = state.achievements.findIndex(a => a.id === achievement.id);
        if (achievementIndex !== -1) {
          state.achievements[achievementIndex] = achievement;
          
          // If achievement was unlocked by this progress update
          if (achievement.unlocked && !state.unlockedAchievements.find(a => a.id === achievement.id)) {
            state.unlockedAchievements.push(achievement);
            state.recentlyUnlocked.push(achievement);
          }
        }
      });
  },
});

export const {
  updateProgress,
  markAsRecentlyUnlocked,
  clearRecentlyUnlocked,
  clearError,
  resetAchievementState,
} = achievementSlice.actions;

export default achievementSlice.reducer;