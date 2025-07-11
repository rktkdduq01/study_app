import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store/store';
import { checkAuthStatus, refreshUserToken } from '../store/slices/authSlice';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  token: string | null;
  isLoading: boolean;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const dispatch = useDispatch<AppDispatch>();
  const { isAuthenticated, user, token, isLoading, refreshToken } = useSelector(
    (state: RootState) => state.auth
  );

  useEffect(() => {
    // Check auth status on app start
    dispatch(checkAuthStatus());
  }, [dispatch]);

  useEffect(() => {
    // Set up token refresh interval
    if (isAuthenticated && refreshToken) {
      const interval = setInterval(() => {
        dispatch(refreshUserToken());
      }, 15 * 60 * 1000); // Refresh every 15 minutes

      return () => clearInterval(interval);
    }
  }, [isAuthenticated, refreshToken, dispatch]);

  const refreshAuth = async () => {
    try {
      await dispatch(refreshUserToken()).unwrap();
    } catch (error) {
      console.error('Failed to refresh auth:', error);
    }
  };

  const value: AuthContextType = {
    isAuthenticated,
    user,
    token,
    isLoading,
    refreshAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};