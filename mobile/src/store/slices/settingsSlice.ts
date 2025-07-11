import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SettingsState {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  fontSize: 'small' | 'medium' | 'large';
  soundEnabled: boolean;
  vibrationEnabled: boolean;
  notificationsEnabled: boolean;
  autoSyncEnabled: boolean;
  dataUsageOptimization: boolean;
  debugMode: boolean;
  tutorialCompleted: boolean;
  firstLaunch: boolean;
}

const initialState: SettingsState = {
  theme: 'auto',
  language: 'en',
  fontSize: 'medium',
  soundEnabled: true,
  vibrationEnabled: true,
  notificationsEnabled: true,
  autoSyncEnabled: true,
  dataUsageOptimization: true,
  debugMode: false,
  tutorialCompleted: false,
  firstLaunch: true,
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.language = action.payload;
    },
    setFontSize: (state, action: PayloadAction<'small' | 'medium' | 'large'>) => {
      state.fontSize = action.payload;
    },
    setSoundEnabled: (state, action: PayloadAction<boolean>) => {
      state.soundEnabled = action.payload;
    },
    setVibrationEnabled: (state, action: PayloadAction<boolean>) => {
      state.vibrationEnabled = action.payload;
    },
    setNotificationsEnabled: (state, action: PayloadAction<boolean>) => {
      state.notificationsEnabled = action.payload;
    },
    setAutoSyncEnabled: (state, action: PayloadAction<boolean>) => {
      state.autoSyncEnabled = action.payload;
    },
    setDataUsageOptimization: (state, action: PayloadAction<boolean>) => {
      state.dataUsageOptimization = action.payload;
    },
    setDebugMode: (state, action: PayloadAction<boolean>) => {
      state.debugMode = action.payload;
    },
    setTutorialCompleted: (state, action: PayloadAction<boolean>) => {
      state.tutorialCompleted = action.payload;
    },
    setFirstLaunch: (state, action: PayloadAction<boolean>) => {
      state.firstLaunch = action.payload;
    },
    updateSettings: (state, action: PayloadAction<Partial<SettingsState>>) => {
      Object.assign(state, action.payload);
    },
    resetSettings: (state) => {
      Object.assign(state, initialState);
    },
  },
});

export const {
  setTheme,
  setLanguage,
  setFontSize,
  setSoundEnabled,
  setVibrationEnabled,
  setNotificationsEnabled,
  setAutoSyncEnabled,
  setDataUsageOptimization,
  setDebugMode,
  setTutorialCompleted,
  setFirstLaunch,
  updateSettings,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;