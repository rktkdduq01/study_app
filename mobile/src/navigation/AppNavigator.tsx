import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { RootState } from '../store/store';
import { Colors } from '../constants/Colors';
import { Layout } from '../constants/Layout';

// Auth Screens
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';
import ForgotPasswordScreen from '../screens/auth/ForgotPasswordScreen';
import EmailVerificationScreen from '../screens/auth/EmailVerificationScreen';

// Main Screens
import HomeScreen from '../screens/main/HomeScreen';
import CharacterScreen from '../screens/main/CharacterScreen';
import QuestScreen from '../screens/main/QuestScreen';
import AchievementScreen from '../screens/main/AchievementScreen';
import ProfileScreen from '../screens/main/ProfileScreen';
import SettingsScreen from '../screens/main/SettingsScreen';

// Game Screens
import GameScreen from '../screens/game/GameScreen';
import BattleScreen from '../screens/game/BattleScreen';
import InventoryScreen from '../screens/game/InventoryScreen';
import ShopScreen from '../screens/game/ShopScreen';

// Multiplayer Screens
import MultiplayerScreen from '../screens/multiplayer/MultiplayerScreen';
import GuildScreen from '../screens/multiplayer/GuildScreen';
import ChatScreen from '../screens/multiplayer/ChatScreen';
import FriendsScreen from '../screens/multiplayer/FriendsScreen';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const AuthStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: false,
      cardStyle: { backgroundColor: Colors.background.primary },
    }}
  >
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
    <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
    <Stack.Screen name="EmailVerification" component={EmailVerificationScreen} />
  </Stack.Navigator>
);

const MainTabs = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName;

        switch (route.name) {
          case 'Home':
            iconName = 'home';
            break;
          case 'Character':
            iconName = 'person';
            break;
          case 'Quest':
            iconName = 'assignment';
            break;
          case 'Achievement':
            iconName = 'emoji-events';
            break;
          case 'Profile':
            iconName = 'account-circle';
            break;
          default:
            iconName = 'circle';
        }

        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: Colors.primary.main,
      tabBarInactiveTintColor: Colors.text.secondary,
      tabBarStyle: {
        backgroundColor: Colors.background.secondary,
        borderTopColor: Colors.border.light,
        height: Layout.tabBarHeight,
        paddingBottom: 8,
        paddingTop: 8,
      },
      tabBarLabelStyle: {
        fontSize: Layout.fontSize.xs,
        fontWeight: '600',
      },
      headerStyle: {
        backgroundColor: Colors.primary.main,
        height: Layout.headerHeight,
      },
      headerTintColor: Colors.primary.contrast,
      headerTitleStyle: {
        fontWeight: 'bold',
        fontSize: Layout.fontSize.lg,
      },
    })}
  >
    <Tab.Screen 
      name="Home" 
      component={HomeScreen}
      options={{ title: 'Home' }}
    />
    <Tab.Screen 
      name="Character" 
      component={CharacterScreen}
      options={{ title: 'Character' }}
    />
    <Tab.Screen 
      name="Quest" 
      component={QuestScreen}
      options={{ title: 'Quests' }}
    />
    <Tab.Screen 
      name="Achievement" 
      component={AchievementScreen}
      options={{ title: 'Achievements' }}
    />
    <Tab.Screen 
      name="Profile" 
      component={ProfileScreen}
      options={{ title: 'Profile' }}
    />
  </Tab.Navigator>
);

const AppStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerShown: false,
      cardStyle: { backgroundColor: Colors.background.primary },
    }}
  >
    <Stack.Screen name="MainTabs" component={MainTabs} />
    <Stack.Screen name="Settings" component={SettingsScreen} />
    <Stack.Screen name="Game" component={GameScreen} />
    <Stack.Screen name="Battle" component={BattleScreen} />
    <Stack.Screen name="Inventory" component={InventoryScreen} />
    <Stack.Screen name="Shop" component={ShopScreen} />
    <Stack.Screen name="Multiplayer" component={MultiplayerScreen} />
    <Stack.Screen name="Guild" component={GuildScreen} />
    <Stack.Screen name="Chat" component={ChatScreen} />
    <Stack.Screen name="Friends" component={FriendsScreen} />
  </Stack.Navigator>
);

const AppNavigator: React.FC = () => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  return (
    <NavigationContainer>
      {isAuthenticated ? <AppStack /> : <AuthStack />}
    </NavigationContainer>
  );
};

export default AppNavigator;