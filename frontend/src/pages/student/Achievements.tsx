import React, { useState, useEffect } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../../components/layout';
import {
  Container,
  
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Avatar,
  IconButton,
  Tooltip,
  Badge,
  Tab,
  Tabs,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  Alert,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  CircularProgress,
  Zoom,
  Fade,
  Grow,
} from '@mui/material';
import {
  EmojiEvents,
  Star,
  LocalFireDepartment,
  School,
  Groups,
  Collections,
  AutoAwesome,
  Timer,
  Psychology,
  Explore,
  Lock,
  LockOpen,
  TrendingUp,
  Celebration,
  EmojiEmotions,
  NavigateNext,
  Info,
  WorkspacePremium,
  DiamondOutlined,
  MilitaryTech,
  Speed,
  CalendarMonth,
  Leaderboard,
  CardGiftcard,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { 
  Achievement, 
  AchievementCategory, 
  AchievementRarity, 
  UserAchievement,
  AchievementStats,
  AchievementChallenge,
  AchievementNotification
} from '../../types/achievement';
import { format } from 'date-fns';
import confetti from 'canvas-confetti';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
  </div>
);

const AchievementsPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { character } = useAppSelector((state) => state.character);
  const [tabValue, setTabValue] = useState(0);
  const [selectedAchievement, setSelectedAchievement] = useState<Achievement | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [notification, setNotification] = useState<AchievementNotification | null>(null);

  // Mock data - would come from API
  const stats: AchievementStats = {
    total_achievements: 150,
    completed_achievements: 45,
    total_points: 15000,
    earned_points: 4500,
    completion_percentage: 30,
    achievements_by_category: {
      learning: { total: 30, completed: 12 },
      quest: { total: 25, completed: 10 },
      streak: { total: 20, completed: 8 },
      social: { total: 15, completed: 5 },
      collection: { total: 20, completed: 3 },
      special: { total: 10, completed: 2 },
      time_challenge: { total: 15, completed: 3 },
      mastery: { total: 10, completed: 2 },
      exploration: { total: 5, completed: 0 },
    },
    achievements_by_rarity: {
      common: { total: 60, completed: 30 },
      rare: { total: 50, completed: 10 },
      epic: { total: 30, completed: 4 },
      legendary: { total: 10, completed: 1 },
    },
    recent_unlocks: [],
    next_achievable: [],
    daily_progress: 75,
    weekly_streak: 5,
  };

  const dailyChallenge: AchievementChallenge = {
    id: 'daily-1',
    title: "Today's Speed Learning Challenge",
    description: 'Complete 3 quests in under 30 minutes total',
    type: 'daily',
    achievements: [],
    end_time: new Date(Date.now() + 8 * 60 * 60 * 1000), // 8 hours from now
    bonus_reward: {
      type: 'gems',
      value: 50,
    },
    participants: 1234,
    leaderboard: {
      user_rank: 42,
      top_players: [
        { name: 'Alex', avatar: '👑', progress: 100 },
        { name: 'Sarah', avatar: '🌟', progress: 95 },
        { name: 'Mike', avatar: '🔥', progress: 90 },
      ],
    },
  };

  const achievements: Achievement[] = [
    // Time Challenge Achievements
    {
      id: 1,
      name: 'Speed Demon',
      description: 'Complete 5 quests in under 10 minutes each',
      category: AchievementCategory.TIME_CHALLENGE,
      rarity: AchievementRarity.RARE,
      points: 100,
      max_progress: 5,
      is_hidden: false,
      is_active: true,
      created_at: '',
      updated_at: '',
      reward_type: 'gems',
      reward_value: 25,
      time_limit: 600, // 10 minutes
    },
    {
      id: 2,
      name: 'Lightning Scholar',
      description: 'Answer 20 questions correctly in 60 seconds',
      category: AchievementCategory.TIME_CHALLENGE,
      rarity: AchievementRarity.EPIC,
      points: 200,
      max_progress: 20,
      is_hidden: false,
      is_active: true,
      created_at: '',
      updated_at: '',
      reward_type: 'title',
      reward_value: 'The Swift',
      time_limit: 60,
    },
    // Mastery Achievements
    {
      id: 3,
      name: 'Math Master',
      description: 'Achieve 100% accuracy in 10 consecutive math quests',
      category: AchievementCategory.MASTERY,
      rarity: AchievementRarity.EPIC,
      points: 300,
      max_progress: 10,
      is_hidden: false,
      is_active: true,
      created_at: '',
      updated_at: '',
      reward_type: 'badge',
      reward_value: 'math_master_badge',
      difficulty_multiplier: 2.0,
    },
    // Streak Achievements
    {
      id: 4,
      name: 'Unstoppable Force',
      description: 'Maintain a 30-day learning streak',
      category: AchievementCategory.STREAK,
      rarity: AchievementRarity.LEGENDARY,
      points: 500,
      max_progress: 30,
      is_hidden: false,
      is_active: true,
      created_at: '',
      updated_at: '',
      reward_type: 'character_skin',
      reward_value: 'legendary_aura',
    },
    // Special Event Achievement
    {
      id: 5,
      name: 'Winter Wonder',
      description: 'Complete all winter-themed quests before the season ends',
      category: AchievementCategory.SPECIAL,
      rarity: AchievementRarity.RARE,
      points: 150,
      max_progress: 5,
      is_hidden: false,
      is_active: true,
      created_at: '',
      updated_at: '',
      seasonal: true,
      reward_type: 'item',
      reward_value: 'snowflake_charm',
    },
  ];

  const userAchievements: UserAchievement[] = [
    {
      id: 1,
      user_id: 1,
      achievement_id: 1,
      progress: 3,
      is_completed: false,
      created_at: '',
      updated_at: '',
      achievement: achievements[0],
    },
    {
      id: 2,
      user_id: 1,
      achievement_id: 3,
      progress: 7,
      is_completed: false,
      created_at: '',
      updated_at: '',
      achievement: achievements[2],
    },
  ];

  const getCategoryIcon = (category: AchievementCategory) => {
    switch (category) {
      case AchievementCategory.LEARNING:
        return <School />;
      case AchievementCategory.QUEST:
        return <EmojiEvents />;
      case AchievementCategory.STREAK:
        return <LocalFireDepartment />;
      case AchievementCategory.SOCIAL:
        return <Groups />;
      case AchievementCategory.COLLECTION:
        return <Collections />;
      case AchievementCategory.SPECIAL:
        return <AutoAwesome />;
      case AchievementCategory.TIME_CHALLENGE:
        return <Timer />;
      case AchievementCategory.MASTERY:
        return <Psychology />;
      case AchievementCategory.EXPLORATION:
        return <Explore />;
      default:
        return <Star />;
    }
  };

  const getRarityColor = (rarity: AchievementRarity) => {
    switch (rarity) {
      case AchievementRarity.COMMON:
        return '#9e9e9e';
      case AchievementRarity.RARE:
        return '#2196f3';
      case AchievementRarity.EPIC:
        return '#9c27b0';
      case AchievementRarity.LEGENDARY:
        return '#ff9800';
      default:
        return '#9e9e9e';
    }
  };

  const getRarityIcon = (rarity: AchievementRarity) => {
    switch (rarity) {
      case AchievementRarity.COMMON:
        return <Star />;
      case AchievementRarity.RARE:
        return <WorkspacePremium />;
      case AchievementRarity.EPIC:
        return <DiamondOutlined />;
      case AchievementRarity.LEGENDARY:
        return <MilitaryTech />;
      default:
        return <Star />;
    }
  };

  const handleAchievementClick = (achievement: Achievement) => {
    setSelectedAchievement(achievement);
  };

  const triggerCelebration = (achievement: Achievement) => {
    setShowCelebration(true);
    setNotification({
      achievement,
      unlockedAt: new Date(),
      isNew: true,
      celebrationType: achievement.rarity === AchievementRarity.LEGENDARY ? 'legendary' : 
                       achievement.rarity === AchievementRarity.EPIC ? 'epic' : 'normal',
    });

    // Confetti animation
    if (achievement.rarity === AchievementRarity.LEGENDARY) {
      // Epic celebration for legendary
      const duration = 5 * 1000;
      const animationEnd = Date.now() + duration;
      const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

      const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;

      const interval: any = setInterval(() => {
        const timeLeft = animationEnd - Date.now();
        if (timeLeft <= 0) return clearInterval(interval);

        const particleCount = 50 * (timeLeft / duration);
        confetti({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
        });
        confetti({
          ...defaults,
          particleCount,
          origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
        });
      }, 250);
    } else {
      // Normal celebration
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
      });
    }

    setTimeout(() => setShowCelebration(false), 5000);
  };

  const renderProgressSection = () => (
    <GridContainer spacing={3}>
      {/* Overall Progress */}
      <Box sx={{ width: '100%' }}>
        <Paper sx={{ p: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <EmojiEvents />
            Achievement Progress
          </Typography>
          <GridContainer spacing={3} alignItems="center">
            <Box sx={{ width: { xs: '100%', md: '33.33%' } }}>
              <Box sx={{ position: 'relative', display: 'inline-flex' }}>
                <CircularProgress
                  variant="determinate"
                  value={stats.completion_percentage}
                  size={120}
                  thickness={4}
                  sx={{ color: 'rgba(255,255,255,0.3)' }}
                />
                <CircularProgress
                  variant="determinate"
                  value={stats.completion_percentage}
                  size={120}
                  thickness={4}
                  sx={{ color: 'white', position: 'absolute', left: 0 }}
                />
                <Box
                  sx={{
                    top: 0,
                    left: 0,
                    bottom: 0,
                    right: 0,
                    position: 'absolute',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography variant="h4" component="div">
                    {stats.completion_percentage}%
                  </Typography>
                </Box>
              </Box>
            </Box>
            <Box sx={{ width: { xs: '100%', md: '66.67%' } }}>
              <GridContainer spacing={2}>
                <Box sx={{ width: { xs: '50%', sm: '25%' } }}>
                  <Typography variant="h4">{stats.completed_achievements}</Typography>
                  <Typography variant="body2">Unlocked</Typography>
                </Box>
                <Box sx={{ width: { xs: '50%', sm: '25%' } }}>
                  <Typography variant="h4">{stats.total_achievements}</Typography>
                  <Typography variant="body2">Total</Typography>
                </Box>
                <Box sx={{ width: { xs: '50%', sm: '25%' } }}>
                  <Typography variant="h4">{stats.earned_points}</Typography>
                  <Typography variant="body2">Points Earned</Typography>
                </Box>
                <Box sx={{ width: { xs: '50%', sm: '25%' } }}>
                  <Typography variant="h4">{stats.weekly_streak}</Typography>
                  <Typography variant="body2">Week Streak</Typography>
                </Box>
              </GridContainer>
            </Box>
          </GridContainer>
        </Paper>
      </Box>

      {/* Daily Challenge */}
      <Box sx={{ width: { xs: '100%', md: '50%' } }}>
        <Card sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              right: 0,
              width: 100,
              height: 100,
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              borderRadius: '0 0 0 100%',
              opacity: 0.1,
            }}
          />
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Speed color="error" />
              Daily Challenge
            </Typography>
            <Typography variant="h5" gutterBottom>
              {dailyChallenge.title}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {dailyChallenge.description}
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Progress</Typography>
                <Typography variant="body2">2/3 Quests</Typography>
              </Box>
              <LinearProgress variant="determinate" value={66} sx={{ height: 8, borderRadius: 4 }} />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Chip
                icon={<Timer />}
                label={`${Math.floor((dailyChallenge.end_time.getTime() - Date.now()) / 1000 / 60 / 60)}h left`}
                color="warning"
                size="small"
              />
              <Chip
                icon={<Groups />}
                label={`${dailyChallenge.participants} participants`}
                size="small"
              />
            </Box>

            <Alert severity="success" sx={{ mb: 2 }}>
              <Typography variant="body2">
                Reward: {dailyChallenge.bonus_reward?.value} {dailyChallenge.bonus_reward?.type}
              </Typography>
            </Alert>

            <Button
              fullWidth
              variant="contained"
              color="primary"
              endIcon={<NavigateNext />}
              onClick={() => navigate('/student/quests')}
            >
              Continue Challenge
            </Button>
          </CardContent>
        </Card>
      </Box>

      {/* Leaderboard Preview */}
      <Box sx={{ width: { xs: '100%', md: '50%' } }}>
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Leaderboard color="warning" />
              Challenge Leaderboard
            </Typography>
            <Box sx={{ mb: 2 }}>
              <Chip
                label={`Your Rank: #${dailyChallenge.leaderboard?.user_rank}`}
                color="primary"
                sx={{ mb: 2 }}
              />
              <List>
                {dailyChallenge.leaderboard?.top_players.map((player, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: index === 0 ? 'gold' : index === 1 ? 'silver' : '#cd7f32' }}>
                        {player.avatar}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={player.name}
                      secondary={`${player.progress}% complete`}
                    />
                    <Chip
                      label={`#${index + 1}`}
                      size="small"
                      color={index === 0 ? 'warning' : 'default'}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
            <Button
              fullWidth
              variant="outlined"
              onClick={() => navigate('/student/leaderboard')}
            >
              View Full Leaderboard
            </Button>
          </CardContent>
        </Card>
      </Box>
    </GridContainer>
  );

  const renderAchievementCard = (achievement: Achievement, userAchievement?: UserAchievement) => {
    const progress = userAchievement?.progress || 0;
    const isCompleted = userAchievement?.is_completed || false;
    const progressPercentage = (progress / achievement.max_progress) * 100;

    return (
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <Card
          sx={{
            height: '100%',
            cursor: 'pointer',
            position: 'relative',
            border: `2px solid ${isCompleted ? getRarityColor(achievement.rarity) : 'transparent'}`,
            opacity: isCompleted ? 1 : 0.8,
            '&:hover': {
              boxShadow: 6,
              borderColor: getRarityColor(achievement.rarity),
            },
          }}
          onClick={() => handleAchievementClick(achievement)}
        >
          {achievement.seasonal && (
            <Chip
              label="Limited Time"
              size="small"
              color="error"
              sx={{ position: 'absolute', top: 8, right: 8, zIndex: 1 }}
            />
          )}
          
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar
                sx={{
                  bgcolor: isCompleted ? getRarityColor(achievement.rarity) : 'grey.400',
                  width: 56,
                  height: 56,
                  mr: 2,
                }}
              >
                {getCategoryIcon(achievement.category)}
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" gutterBottom>
                  {achievement.name}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {getRarityIcon(achievement.rarity)}
                  <Typography variant="caption" color="text.secondary">
                    {achievement.rarity.charAt(0).toUpperCase() + achievement.rarity.slice(1)}
                  </Typography>
                  {achievement.points && (
                    <Chip label={`${achievement.points} pts`} size="small" />
                  )}
                </Box>
              </Box>
              {isCompleted && (
                <Tooltip title="Achievement Unlocked!">
                  <Celebration color="success" />
                </Tooltip>
              )}
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {achievement.description}
            </Typography>

            {!isCompleted && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="caption">Progress</Typography>
                  <Typography variant="caption">
                    {progress}/{achievement.max_progress}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={progressPercentage}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    bgcolor: 'grey.300',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: getRarityColor(achievement.rarity),
                    },
                  }}
                />
              </Box>
            )}

            {achievement.reward_type && (
              <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <CardGiftcard fontSize="small" color="action" />
                <Typography variant="caption">
                  Reward: {achievement.reward_value} {achievement.reward_type}
                </Typography>
              </Box>
            )}

            {achievement.time_limit && !isCompleted && (
              <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                <Timer fontSize="small" color="warning" />
                <Typography variant="caption" color="warning.main">
                  Time limit: {achievement.time_limit}s
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  const renderCategoryTab = (category: AchievementCategory) => {
    const categoryAchievements = achievements.filter(a => a.category === category);
    const categoryStats = stats.achievements_by_category[category];

    return (
      <Box>
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {getCategoryIcon(category)}
              {category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' ')} Achievements
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body2">
                {categoryStats?.completed || 0}/{categoryStats?.total || 0} Completed
              </Typography>
              <CircularProgress
                variant="determinate"
                value={((categoryStats?.completed || 0) / (categoryStats?.total || 1)) * 100}
                size={40}
                thickness={4}
              />
            </Box>
          </Box>
        </Paper>

        <GridContainer spacing={3}>
          {categoryAchievements.map((achievement) => {
            const userAchievement = userAchievements.find(ua => ua.achievement_id === achievement.id);
            return (
              <Box sx={{ width: { xs: '100%', sm: '50%', md: '33.33%' } }} key={achievement.id}>
                {renderAchievementCard(achievement, userAchievement)}
              </Box>
            );
          })}
        </GridContainer>
      </Box>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EmojiEvents color="primary" />
          Achievements
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Complete challenges, earn rewards, and show off your accomplishments!
        </Typography>
      </Box>

      {/* Progress Section */}
      {renderProgressSection()}

      {/* Achievement Categories */}
      <Box sx={{ mt: 4 }}>
        <Tabs
          value={tabValue}
          onChange={(_, value) => setTabValue(value)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="All" icon={<Star />} iconPosition="start" />
          <Tab label="Time Challenges" icon={<Timer />} iconPosition="start" />
          <Tab label="Mastery" icon={<Psychology />} iconPosition="start" />
          <Tab label="Streaks" icon={<LocalFireDepartment />} iconPosition="start" />
          <Tab label="Special Events" icon={<AutoAwesome />} iconPosition="start" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <GridContainer spacing={3}>
            {achievements.map((achievement) => {
              const userAchievement = userAchievements.find(ua => ua.achievement_id === achievement.id);
              return (
                <Box sx={{ width: { xs: '100%', sm: '50%', md: '33.33%' } }} key={achievement.id}>
                  {renderAchievementCard(achievement, userAchievement)}
                </Box>
              );
            })}
          </GridContainer>
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          {renderCategoryTab(AchievementCategory.TIME_CHALLENGE)}
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          {renderCategoryTab(AchievementCategory.MASTERY)}
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          {renderCategoryTab(AchievementCategory.STREAK)}
        </TabPanel>
        <TabPanel value={tabValue} index={4}>
          {renderCategoryTab(AchievementCategory.SPECIAL)}
        </TabPanel>
      </Box>

      {/* Achievement Detail Dialog */}
      <Dialog
        open={!!selectedAchievement}
        onClose={() => setSelectedAchievement(null)}
        maxWidth="sm"
        fullWidth
      >
        {selectedAchievement && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar
                  sx={{
                    bgcolor: getRarityColor(selectedAchievement.rarity),
                    width: 48,
                    height: 48,
                  }}
                >
                  {getCategoryIcon(selectedAchievement.category)}
                </Avatar>
                <Box>
                  <Typography variant="h6">{selectedAchievement.name}</Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {getRarityIcon(selectedAchievement.rarity)}
                    <Typography variant="caption">
                      {selectedAchievement.rarity.charAt(0).toUpperCase() + selectedAchievement.rarity.slice(1)}
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" paragraph>
                {selectedAchievement.description}
              </Typography>
              
              {selectedAchievement.reward_type && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Reward:</strong> {selectedAchievement.reward_value} {selectedAchievement.reward_type}
                  </Typography>
                </Alert>
              )}

              {selectedAchievement.time_limit && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Time Limit:</strong> Complete within {selectedAchievement.time_limit} seconds
                  </Typography>
                </Alert>
              )}

              <Box sx={{ mt: 3 }}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={() => {
                    setSelectedAchievement(null);
                    navigate('/student/quests');
                  }}
                >
                  Start Working on This Achievement
                </Button>
              </Box>
            </DialogContent>
          </>
        )}
      </Dialog>

      {/* Celebration Notification */}
      {notification && showCelebration && (
        <Zoom in={showCelebration}>
          <Paper
            sx={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              p: 4,
              zIndex: 9999,
              textAlign: 'center',
              maxWidth: 400,
              boxShadow: 24,
              border: `3px solid ${getRarityColor(notification.achievement.rarity)}`,
            }}
          >
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                rotate: [0, 360, 0],
              }}
              transition={{ duration: 0.5 }}
            >
              <Avatar
                sx={{
                  width: 120,
                  height: 120,
                  bgcolor: getRarityColor(notification.achievement.rarity),
                  mx: 'auto',
                  mb: 2,
                }}
              >
                <EmojiEvents sx={{ fontSize: 60 }} />
              </Avatar>
            </motion.div>
            
            <Typography variant="h4" gutterBottom>
              Achievement Unlocked!
            </Typography>
            <Typography variant="h5" gutterBottom>
              {notification.achievement.name}
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              {notification.achievement.description}
            </Typography>
            
            {notification.achievement.reward_type && (
              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  You earned: {notification.achievement.reward_value} {notification.achievement.reward_type}!
                </Typography>
              </Alert>
            )}
          </Paper>
        </Zoom>
      )}
    </Container>
  );
};

export default AchievementsPage;
