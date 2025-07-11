import React from 'react';
import { Grid, Card, CardContent, Typography, Box, LinearProgress } from '@mui/material';
import { 
  Timer as TimerIcon,
  School as SchoolIcon,
  EmojiEvents as TrophyIcon,
  TrendingUp as TrendingUpIcon,
  Assignment as AssignmentIcon,
  Grade as GradeIcon
} from '@mui/icons-material';

interface StatsData {
  learning_progress?: {
    total_items: number;
    completed_items: number;
    average_score: number;
    total_time_spent: number;
  };
  engagement?: {
    total_login_count: number;
    total_active_minutes: number;
    lessons_completed: number;
    quests_completed: number;
    achievements_earned: number;
    average_daily_minutes: number;
    max_streak: number;
  };
  activity_patterns?: {
    total_activities: number;
  };
}

interface DashboardStatsProps {
  data?: StatsData;
}

const DashboardStats: React.FC<DashboardStatsProps> = ({ data }) => {
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const stats = [
    {
      title: 'Study Time',
      value: formatTime(data?.learning_progress?.total_time_spent || 0),
      icon: <TimerIcon />,
      color: '#4CAF50',
      subtitle: `${data?.engagement?.average_daily_minutes || 0} min/day avg`
    },
    {
      title: 'Lessons Completed',
      value: data?.engagement?.lessons_completed || 0,
      icon: <SchoolIcon />,
      color: '#2196F3',
      subtitle: `${data?.learning_progress?.completed_items || 0} total items`
    },
    {
      title: 'Average Score',
      value: `${(data?.learning_progress?.average_score || 0).toFixed(1)}%`,
      icon: <GradeIcon />,
      color: '#FF9800',
      subtitle: 'Overall performance'
    },
    {
      title: 'Current Streak',
      value: `${data?.engagement?.max_streak || 0} days`,
      icon: <TrendingUpIcon />,
      color: '#9C27B0',
      subtitle: 'Keep it up!'
    },
    {
      title: 'Quests Done',
      value: data?.engagement?.quests_completed || 0,
      icon: <AssignmentIcon />,
      color: '#F44336',
      subtitle: 'Adventures completed'
    },
    {
      title: 'Achievements',
      value: data?.engagement?.achievements_earned || 0,
      icon: <TrophyIcon />,
      color: '#FFC107',
      subtitle: 'Trophies earned'
    }
  ];

  return (
    <Grid container spacing={2}>
      {stats.map((stat, index) => (
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2 }} key={index}>
          <Card 
            sx={{ 
              height: '100%',
              background: `linear-gradient(135deg, ${stat.color}15 0%, ${stat.color}05 100%)`,
              border: `1px solid ${stat.color}30`
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 40,
                    height: 40,
                    borderRadius: '8px',
                    backgroundColor: stat.color,
                    color: 'white',
                    mr: 2
                  }}
                >
                  {stat.icon}
                </Box>
                <Box>
                  <Typography variant="caption" color="textSecondary">
                    {stat.title}
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                    {stat.value}
                  </Typography>
                </Box>
              </Box>
              <Typography variant="caption" color="textSecondary">
                {stat.subtitle}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
      
      {/* Progress Overview */}
      <Grid size={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Overall Progress
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="textSecondary">
                  Learning Completion
                </Typography>
                <Typography variant="body2">
                  {data?.learning_progress?.completed_items || 0} / {data?.learning_progress?.total_items || 0}
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={
                  data?.learning_progress?.total_items 
                    ? (data.learning_progress.completed_items / data.learning_progress.total_items) * 100
                    : 0
                }
                sx={{ height: 8, borderRadius: 4 }}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default DashboardStats;