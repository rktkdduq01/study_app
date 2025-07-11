import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { combineReducers } from 'redux';

import authReducer from './slices/authSlice';
import userReducer from './slices/userSlice';
import characterReducer from './slices/characterSlice';
import questReducer from './slices/questSlice';
import achievementReducer from './slices/achievementSlice';
import multiplayerReducer from './slices/multiplayerSlice';
import contentReducer from './slices/contentSlice';
import notificationReducer from './slices/notificationSlice';
import settingsReducer from './slices/settingsSlice';
import offlineReducer from './slices/offlineSlice';

const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['auth', 'user', 'character', 'settings', 'offline'],
  blacklist: ['notification'],
};

const rootReducer = combineReducers({
  auth: authReducer,
  user: userReducer,
  character: characterReducer,
  quest: questReducer,
  achievement: achievementReducer,
  multiplayer: multiplayerReducer,
  content: contentReducer,
  notification: notificationReducer,
  settings: settingsReducer,
  offline: offlineReducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }),
  devTools: __DEV__,
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;