import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import characterReducer from './slices/characterSlice';
import questReducer from './slices/questSlice';
import parentReducer from './slices/parentSlice';
import notificationReducer from './slices/notificationSlice';
import friendReducer from './slices/friendSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    character: characterReducer,
    quest: questReducer,
    parent: parentReducer,
    notifications: notificationReducer,
    friends: friendReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types
        ignoredActions: ['auth/login/fulfilled', 'auth/register/fulfilled'],
        // Ignore these field paths in all actions
        ignoredActionPaths: ['payload.timestamp', 'meta.arg'],
        // Ignore these paths in the state
        ignoredPaths: ['auth.user.created_at', 'auth.user.updated_at'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;