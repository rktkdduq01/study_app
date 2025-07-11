import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as ReduxProvider } from 'react-redux';
import { StatusBar, View, StyleSheet } from 'react-native';
import Toast from 'react-native-toast-message';
import { store } from './src/store/store';
import AppNavigator from './src/navigation/AppNavigator';
import { AuthProvider } from './src/contexts/AuthContext';
import { NetworkProvider } from './src/contexts/NetworkContext';
import { NotificationProvider } from './src/contexts/NotificationContext';
import LoadingScreen from './src/components/common/LoadingScreen';
import { initializeApp } from './src/utils/appInitializer';
import { Colors } from './src/constants/Colors';

const App: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    initializeApplication();
  }, []);

  const initializeApplication = async () => {
    try {
      await initializeApp();
      setIsInitialized(true);
    } catch (error) {
      console.error('Failed to initialize app:', error);
      // Handle initialization error
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <ReduxProvider store={store}>
      <NavigationContainer>
        <AuthProvider>
          <NetworkProvider>
            <NotificationProvider>
              <View style={styles.container}>
                <StatusBar
                  backgroundColor={Colors.primary.dark}
                  barStyle="light-content"
                />
                <AppNavigator />
                <Toast />
              </View>
            </NotificationProvider>
          </NetworkProvider>
        </AuthProvider>
      </NavigationContainer>
    </ReduxProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background.primary,
  },
});

export default App;