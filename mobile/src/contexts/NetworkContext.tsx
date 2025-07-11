import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import NetInfo from '@react-native-community/netinfo';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store/store';
import { setNetworkStatus } from '../store/slices/offlineSlice';

interface NetworkContextType {
  isConnected: boolean;
  connectionType: string | null;
  isInternetReachable: boolean | null;
}

const NetworkContext = createContext<NetworkContextType | undefined>(undefined);

interface NetworkProviderProps {
  children: ReactNode;
}

export const NetworkProvider: React.FC<NetworkProviderProps> = ({ children }) => {
  const dispatch = useDispatch<AppDispatch>();
  const [networkState, setNetworkState] = useState({
    isConnected: true,
    connectionType: null as string | null,
    isInternetReachable: null as boolean | null,
  });

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      const newState = {
        isConnected: state.isConnected ?? false,
        connectionType: state.type,
        isInternetReachable: state.isInternetReachable,
      };
      
      setNetworkState(newState);
      
      // Update Redux store
      dispatch(setNetworkStatus({
        isConnected: newState.isConnected,
        connectionType: newState.connectionType,
        isInternetReachable: newState.isInternetReachable,
      }));
    });

    return () => unsubscribe();
  }, [dispatch]);

  return (
    <NetworkContext.Provider value={networkState}>
      {children}
    </NetworkContext.Provider>
  );
};

export const useNetwork = (): NetworkContextType => {
  const context = useContext(NetworkContext);
  if (context === undefined) {
    throw new Error('useNetwork must be used within a NetworkProvider');
  }
  return context;
};