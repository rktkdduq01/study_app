import React, { useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  LinearProgress,
  Chip,
  Avatar,
} from '@mui/material';
import {
  EmojiEvents as TrophyIcon,
  Assignment as QuestIcon,
  TrendingUp as TrendingUpIcon,
  School as SchoolIcon,
  Star as StarIcon,
  LocalFireDepartment as FireIcon,
  Psychology as AIIcon,
  NavigateNext,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { fetchDailyQuests, fetchMyQuestProgress } from '../../store/slices/questSlice';
import { updateStreak } from '../../store/slices/characterSlice';
import { QuestStatus, QuestDifficulty } from '../../types/quest';
import { DashboardLayout, StatCard } from '../../components/layout/DashboardLayout';
import { useAsyncData } from '../../hooks/useAsyncData';

const StudentDashboard: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { character } = useAppSelector((state) => state.character);
  const { dailyQuests, myProgress } = useAppSelector((state) => state.quest);
  const { user } = useAppSelector((state) => state.auth);

  // Use async data hook for loading state management
  const { loading, error, execute } = useAsyncData(
    async () => {
      await Promise.all([
        dispatch(fetchDailyQuests()).unwrap(),
        dispatch(fetchMyQuestProgress()).unwrap(),
        character && dispatch(updateStreak(character.id)).unwrap()
      ]);
    },
    { immediate: true }
  );

  const getDifficultyColor = (difficulty: QuestDifficulty) => {
    switch (difficulty) {
      case QuestDifficulty.EASY:
        return 'success';
      case QuestDifficulty.MEDIUM:
        return 'warning';
      case QuestDifficulty.HARD:
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: QuestStatus) => {
    switch (status) {
      case QuestStatus.COMPLETED:
        return 'success';
      case QuestStatus.IN_PROGRESS:
        return 'primary';
      case QuestStatus.AVAILABLE:
        return 'default';
      default:
        return 'default';
    }
  };

  const activeQuests = myProgress.filter(p => p.status === QuestStatus.IN_PROGRESS).length;
  const completedToday = myProgress.filter(
    p => p.status === QuestStatus.COMPLETED && 
    new Date(p.completed_at || '').toDateString() === new Date().toDateString()
  ).length;

  const sections = [
    // Stats Section
    {
      id: 'stats',
      gridProps: { xs: 12 },
      component: (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
          <StatCard
            title="Level"
            value={character?.level || 1}
            icon={<TrophyIcon />}
            color="primary"
          />
          <StatCard
            title="Total XP"
            value={character?.experience_points || 0}
            icon={<StarIcon />}
            color="secondary"
          />
          <StatCard
            title="Study Streak"
            value={`${character?.study_streak || 0} days`}
            icon={<FireIcon />}
            color="error"
          />
          <StatCard
            title="Active Quests"
            value={activeQuests}
            icon={<QuestIcon />}
            color="info"
          />
        </Box>
      )
    },
    // Character Card
    {
      id: 'character',
      gridProps: { xs: 12, md: 4 },
      component: (
        <Card sx={{ height: '100%' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar
                sx={{ width: 80, height: 80, mr: 2 }}
                src={character?.avatar_url}
              >
                {character?.name?.[0] || user?.username?.[0]}
              </Avatar>
              <Box>
                <Typography variant="h6">{character?.name || user?.username}</Typography>
                <Chip 
                  label={`Level ${character?.level || 1}`} 
                  color="primary" 
                  size="small" 
                />
              </Box>
            </Box>
            
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Next Level</Typography>
                <Typography variant="body2" color="primary">
                  {character?.experience_points || 0} / {((character?.level || 1) * 100)}
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={((character?.experience_points || 0) % 100)} 
              />
            </Box>
            
            <Button
              fullWidth
              variant="contained"
              startIcon={<TrophyIcon />}
              onClick={() => navigate('/character')}
            >
              View Character
            </Button>
          </CardContent>
        </Card>
      )
    },
    // Daily Quests
    {
      id: 'daily-quests',
      gridProps: { xs: 12, md: 4 },
      title: 'Daily Quests',
      component: (
        <Box>
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Completed Today: {completedToday}/{dailyQuests.length}
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={(completedToday / (dailyQuests.length || 1)) * 100} 
            />
          </Box>
          
          {dailyQuests.slice(0, 3).map((quest) => (
            <Card key={quest.id} sx={{ mb: 1 }}>
              <CardContent sx={{ py: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="subtitle2">{quest.title}</Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                      <Chip 
                        label={quest.difficulty} 
                        size="small" 
                        color={getDifficultyColor(quest.difficulty)} 
                      />
                      <Chip label={`${quest.experience_points} XP`} size="small" />
                    </Box>
                  </Box>
                  <Button 
                    size="small" 
                    endIcon={<NavigateNext />}
                    onClick={() => navigate(`/quests/${quest.id}`)}
                  >
                    Start
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ))}
          
          <Button 
            fullWidth 
            sx={{ mt: 1 }} 
            onClick={() => navigate('/quests')}
          >
            View All Quests
          </Button>
        </Box>
      )
    },
    // Quick Actions
    {
      id: 'quick-actions',
      gridProps: { xs: 12, md: 4 },
      title: 'Quick Actions',
      component: (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Button
            fullWidth
            variant="outlined"
            size="large"
            startIcon={<AIIcon />}
            onClick={() => navigate('/ai-tutor')}
          >
            AI Tutor
          </Button>
          <Button
            fullWidth
            variant="outlined"
            size="large"
            startIcon={<SchoolIcon />}
            onClick={() => navigate('/subjects')}
          >
            Study Subjects
          </Button>
          <Button
            fullWidth
            variant="outlined"
            size="large"
            startIcon={<TrendingUpIcon />}
            onClick={() => navigate('/leaderboard')}
          >
            Leaderboard
          </Button>
        </Box>
      )
    }
  ];

  return (
    <DashboardLayout
      title="Student Dashboard"
      subtitle={`Welcome back, ${user?.username}! Ready to learn today?`}
      loading={loading}
      error={error}
      sections={sections}
      onRefresh={execute}
    />
  );
};

export default StudentDashboard;