import React, { useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import LinearGradient from 'react-native-linear-gradient';
import Icon from 'react-native-vector-icons/MaterialIcons';

import { AppDispatch, RootState } from '../../store/store';
import { fetchCharacter } from '../../store/slices/characterSlice';
import { Colors } from '../../constants/Colors';
import { Layout } from '../../constants/Layout';

const HomeScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigation = useNavigation();
  const { user } = useSelector((state: RootState) => state.auth);
  const { character, stats, isLoading } = useSelector((state: RootState) => state.character);

  useEffect(() => {
    dispatch(fetchCharacter());
  }, [dispatch]);

  const handleRefresh = () => {
    dispatch(fetchCharacter());
  };

  const navigateToScreen = (screenName: string) => {
    navigation.navigate(screenName as never);
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
  };

  const quickActions = [
    { icon: 'play-arrow', title: 'Start Learning', screen: 'Game', color: Colors.gradient.primary },
    { icon: 'assignment', title: 'Quests', screen: 'Quest', color: Colors.gradient.success },
    { icon: 'group', title: 'Multiplayer', screen: 'Multiplayer', color: Colors.gradient.secondary },
    { icon: 'emoji-events', title: 'Achievements', screen: 'Achievement', color: Colors.gradient.warning },
  ];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={isLoading} onRefresh={handleRefresh} />
      }
    >
      <LinearGradient
        colors={Colors.gradient.primary}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View style={styles.greetingContainer}>
            <Text style={styles.greeting}>{getGreeting()},</Text>
            <Text style={styles.userName}>{user?.username || 'Learner'}!</Text>
          </View>
          <TouchableOpacity
            style={styles.profileButton}
            onPress={() => navigateToScreen('Profile')}
          >
            <Icon name="account-circle" size={32} color={Colors.primary.contrast} />
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <View style={styles.content}>
        {/* Character Summary */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Your Character</Text>
            <TouchableOpacity onPress={() => navigateToScreen('Character')}>
              <Icon name="arrow-forward" size={20} color={Colors.primary.main} />
            </TouchableOpacity>
          </View>
          
          {character && stats ? (
            <View style={styles.characterSummary}>
              <View style={styles.characterInfo}>
                <Text style={styles.characterName}>{character.name || 'Hero'}</Text>
                <Text style={styles.characterClass}>
                  Level {character.level} {character.character_class}
                </Text>
              </View>
              
              <View style={styles.statsContainer}>
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>HP</Text>
                  <View style={styles.statBar}>
                    <View
                      style={[
                        styles.statFill,
                        { width: `${(stats.health / stats.max_health) * 100}%` },
                        { backgroundColor: Colors.rpg.health },
                      ]}
                    />
                  </View>
                  <Text style={styles.statValue}>{stats.health}/{stats.max_health}</Text>
                </View>
                
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>MP</Text>
                  <View style={styles.statBar}>
                    <View
                      style={[
                        styles.statFill,
                        { width: `${(stats.mana / stats.max_mana) * 100}%` },
                        { backgroundColor: Colors.rpg.mana },
                      ]}
                    />
                  </View>
                  <Text style={styles.statValue}>{stats.mana}/{stats.max_mana}</Text>
                </View>
                
                <View style={styles.statItem}>
                  <Text style={styles.statLabel}>EXP</Text>
                  <View style={styles.statBar}>
                    <View
                      style={[
                        styles.statFill,
                        { width: `${(character.experience / (character.level * 100)) * 100}%` },
                        { backgroundColor: Colors.rpg.experience },
                      ]}
                    />
                  </View>
                  <Text style={styles.statValue}>{character.experience}/{character.level * 100}</Text>
                </View>
              </View>
            </View>
          ) : (
            <TouchableOpacity
              style={styles.createCharacterButton}
              onPress={() => navigateToScreen('Character')}
            >
              <Text style={styles.createCharacterText}>Create Your Character</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Quick Actions */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Quick Actions</Text>
          <View style={styles.quickActionsGrid}>
            {quickActions.map((action, index) => (
              <TouchableOpacity
                key={index}
                style={styles.quickActionItem}
                onPress={() => navigateToScreen(action.screen)}
              >
                <LinearGradient
                  colors={action.color}
                  style={styles.quickActionGradient}
                >
                  <Icon name={action.icon} size={24} color={Colors.primary.contrast} />
                </LinearGradient>
                <Text style={styles.quickActionText}>{action.title}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Daily Progress */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Today's Progress</Text>
          <View style={styles.progressContainer}>
            <View style={styles.progressItem}>
              <View style={styles.progressIcon}>
                <Icon name="menu-book" size={20} color={Colors.primary.main} />
              </View>
              <View style={styles.progressInfo}>
                <Text style={styles.progressLabel}>Lessons Completed</Text>
                <Text style={styles.progressValue}>3/5</Text>
              </View>
            </View>
            
            <View style={styles.progressItem}>
              <View style={styles.progressIcon}>
                <Icon name="timer" size={20} color={Colors.success.main} />
              </View>
              <View style={styles.progressInfo}>
                <Text style={styles.progressLabel}>Study Time</Text>
                <Text style={styles.progressValue}>45 min</Text>
              </View>
            </View>
            
            <View style={styles.progressItem}>
              <View style={styles.progressIcon}>
                <Icon name="emoji-events" size={20} color={Colors.warning.main} />
              </View>
              <View style={styles.progressInfo}>
                <Text style={styles.progressLabel}>Achievements</Text>
                <Text style={styles.progressValue}>2 earned</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Recent Activity */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Recent Activity</Text>
          <View style={styles.activityContainer}>
            <View style={styles.activityItem}>
              <View style={styles.activityIcon}>
                <Icon name="star" size={16} color={Colors.warning.main} />
              </View>
              <View style={styles.activityInfo}>
                <Text style={styles.activityText}>Completed Math Quest: Algebra Basics</Text>
                <Text style={styles.activityTime}>2 hours ago</Text>
              </View>
            </View>
            
            <View style={styles.activityItem}>
              <View style={styles.activityIcon}>
                <Icon name="trending-up" size={16} color={Colors.success.main} />
              </View>
              <View style={styles.activityInfo}>
                <Text style={styles.activityText}>Leveled up to Level 5</Text>
                <Text style={styles.activityTime}>1 day ago</Text>
              </View>
            </View>
            
            <View style={styles.activityItem}>
              <View style={styles.activityIcon}>
                <Icon name="group" size={16} color={Colors.primary.main} />
              </View>
              <View style={styles.activityInfo}>
                <Text style={styles.activityText}>Joined Study Group: Physics Masters</Text>
                <Text style={styles.activityTime}>2 days ago</Text>
              </View>
            </View>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background.primary,
  },
  header: {
    paddingTop: Layout.statusBarHeight,
    paddingHorizontal: Layout.screenPadding,
    paddingBottom: Layout.spacing.lg,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  greetingContainer: {
    flex: 1,
  },
  greeting: {
    fontSize: Layout.fontSize.md,
    color: Colors.primary.contrast,
    opacity: 0.9,
  },
  userName: {
    fontSize: Layout.fontSize.xl,
    fontWeight: 'bold',
    color: Colors.primary.contrast,
  },
  profileButton: {
    padding: Layout.spacing.sm,
  },
  content: {
    padding: Layout.screenPadding,
  },
  card: {
    backgroundColor: Colors.background.secondary,
    borderRadius: Layout.borderRadius.md,
    padding: Layout.cardPadding,
    marginBottom: Layout.spacing.lg,
    ...Layout.shadow,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Layout.spacing.md,
  },
  cardTitle: {
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
    color: Colors.text.primary,
  },
  characterSummary: {
    marginTop: Layout.spacing.md,
  },
  characterInfo: {
    marginBottom: Layout.spacing.md,
  },
  characterName: {
    fontSize: Layout.fontSize.lg,
    fontWeight: 'bold',
    color: Colors.text.primary,
  },
  characterClass: {
    fontSize: Layout.fontSize.md,
    color: Colors.text.secondary,
  },
  statsContainer: {
    gap: Layout.spacing.md,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Layout.spacing.sm,
  },
  statLabel: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.secondary,
    width: 30,
  },
  statBar: {
    flex: 1,
    height: 8,
    backgroundColor: Colors.border.light,
    borderRadius: Layout.borderRadius.xs,
    overflow: 'hidden',
  },
  statFill: {
    height: '100%',
    borderRadius: Layout.borderRadius.xs,
  },
  statValue: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.primary,
    width: 50,
    textAlign: 'right',
  },
  createCharacterButton: {
    backgroundColor: Colors.overlay.primary,
    padding: Layout.spacing.md,
    borderRadius: Layout.borderRadius.sm,
    alignItems: 'center',
  },
  createCharacterText: {
    color: Colors.primary.main,
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Layout.spacing.md,
  },
  quickActionItem: {
    flex: 1,
    minWidth: '45%',
    alignItems: 'center',
  },
  quickActionGradient: {
    width: 60,
    height: 60,
    borderRadius: Layout.borderRadius.round,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Layout.spacing.sm,
  },
  quickActionText: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.primary,
    textAlign: 'center',
  },
  progressContainer: {
    gap: Layout.spacing.md,
  },
  progressItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Layout.spacing.md,
  },
  progressIcon: {
    width: 36,
    height: 36,
    borderRadius: Layout.borderRadius.sm,
    backgroundColor: Colors.overlay.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressInfo: {
    flex: 1,
  },
  progressLabel: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.secondary,
  },
  progressValue: {
    fontSize: Layout.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text.primary,
  },
  activityContainer: {
    gap: Layout.spacing.md,
  },
  activityItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Layout.spacing.md,
  },
  activityIcon: {
    width: 24,
    height: 24,
    borderRadius: Layout.borderRadius.round,
    backgroundColor: Colors.background.tertiary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  activityInfo: {
    flex: 1,
  },
  activityText: {
    fontSize: Layout.fontSize.sm,
    color: Colors.text.primary,
  },
  activityTime: {
    fontSize: Layout.fontSize.xs,
    color: Colors.text.secondary,
    marginTop: Layout.spacing.xs,
  },
});

export default HomeScreen;