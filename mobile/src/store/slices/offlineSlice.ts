import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface OfflineAction {
  id: string;
  type: string;
  payload: any;
  timestamp: number;
  retryCount: number;
}

interface OfflineState {
  isOnline: boolean;
  connectionType: string | null;
  isInternetReachable: boolean | null;
  pendingActions: OfflineAction[];
  syncInProgress: boolean;
  lastSyncTime: number | null;
  offlineData: Record<string, any>;
}

const initialState: OfflineState = {
  isOnline: true,
  connectionType: null,
  isInternetReachable: null,
  pendingActions: [],
  syncInProgress: false,
  lastSyncTime: null,
  offlineData: {},
};

const offlineSlice = createSlice({
  name: 'offline',
  initialState,
  reducers: {
    setNetworkStatus: (
      state,
      action: PayloadAction<{
        isConnected: boolean;
        connectionType: string | null;
        isInternetReachable: boolean | null;
      }>
    ) => {
      state.isOnline = action.payload.isConnected;
      state.connectionType = action.payload.connectionType;
      state.isInternetReachable = action.payload.isInternetReachable;
    },
    addPendingAction: (state, action: PayloadAction<Omit<OfflineAction, 'id' | 'timestamp' | 'retryCount'>>) => {
      const newAction: OfflineAction = {
        ...action.payload,
        id: Date.now().toString(),
        timestamp: Date.now(),
        retryCount: 0,
      };
      state.pendingActions.push(newAction);
    },
    removePendingAction: (state, action: PayloadAction<string>) => {
      state.pendingActions = state.pendingActions.filter(
        action => action.id !== action.payload
      );
    },
    incrementRetryCount: (state, action: PayloadAction<string>) => {
      const action = state.pendingActions.find(a => a.id === action.payload);
      if (action) {
        action.retryCount += 1;
      }
    },
    clearPendingActions: (state) => {
      state.pendingActions = [];
    },
    setSyncInProgress: (state, action: PayloadAction<boolean>) => {
      state.syncInProgress = action.payload;
    },
    setLastSyncTime: (state, action: PayloadAction<number>) => {
      state.lastSyncTime = action.payload;
    },
    setOfflineData: (state, action: PayloadAction<{ key: string; data: any }>) => {
      state.offlineData[action.payload.key] = action.payload.data;
    },
    removeOfflineData: (state, action: PayloadAction<string>) => {
      delete state.offlineData[action.payload];
    },
    clearOfflineData: (state) => {
      state.offlineData = {};
    },
    resetOfflineState: (state) => {
      state.pendingActions = [];
      state.syncInProgress = false;
      state.lastSyncTime = null;
      state.offlineData = {};
    },
  },
});

export const {
  setNetworkStatus,
  addPendingAction,
  removePendingAction,
  incrementRetryCount,
  clearPendingActions,
  setSyncInProgress,
  setLastSyncTime,
  setOfflineData,
  removeOfflineData,
  clearOfflineData,
  resetOfflineState,
} = offlineSlice.actions;

export default offlineSlice.reducer;