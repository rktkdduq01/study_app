import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User } from '../../types/User';

interface UserState {
  profile: User | null;
  preferences: {
    notifications: boolean;
    soundEnabled: boolean;
    vibrationEnabled: boolean;
    theme: 'light' | 'dark' | 'auto';
    language: string;
  };
  statistics: {
    totalStudyTime: number;
    lessonsCompleted: number;
    questsCompleted: number;
    achievementsUnlocked: number;
    currentStreak: number;
    longestStreak: number;
  };
  isLoading: boolean;
  error: string | null;
}

const initialState: UserState = {
  profile: null,
  preferences: {
    notifications: true,
    soundEnabled: true,
    vibrationEnabled: true,
    theme: 'auto',
    language: 'en',
  },
  statistics: {
    totalStudyTime: 0,
    lessonsCompleted: 0,
    questsCompleted: 0,
    achievementsUnlocked: 0,
    currentStreak: 0,
    longestStreak: 0,
  },
  isLoading: false,
  error: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setProfile: (state, action: PayloadAction<User>) => {
      state.profile = action.payload;
    },
    updatePreferences: (state, action: PayloadAction<Partial<typeof initialState.preferences>>) => {
      state.preferences = { ...state.preferences, ...action.payload };
    },
    updateStatistics: (state, action: PayloadAction<Partial<typeof initialState.statistics>>) => {
      state.statistics = { ...state.statistics, ...action.payload };
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetUserState: (state) => {
      state.profile = null;
      state.preferences = initialState.preferences;
      state.statistics = initialState.statistics;
      state.error = null;
    },
  },
});

export const {
  setProfile,
  updatePreferences,
  updateStatistics,
  setLoading,
  setError,
  clearError,
  resetUserState,
} = userSlice.actions;

export default userSlice.reducer;