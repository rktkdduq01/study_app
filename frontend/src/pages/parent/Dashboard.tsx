import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Card,
  CardContent,
  Chip,
  IconButton,
  Button,
  Stack,
  LinearProgress,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Alert,
  Badge,
  CircularProgress,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Timer as TimerIcon,
  Star as StarIcon,
  LocalFireDepartment as FireIcon,
  Notifications as NotificationsIcon,
  Assessment as AssessmentIcon,
  TrackChanges as TargetIcon,
  Security as SecurityIcon,
  MoreVert as MoreVertIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  AutoAwesome as AutoAwesomeIcon,
  School as SchoolIcon,
  EmojiEvents as TrophyIcon,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { useWebSocket } from '../../hooks/useWebSocket';
import { 
  fetchConnectedChildren, 
  fetchParentNotifications,
  fetchFamilyDashboard,
  fetchMyFamily,
  fetchFamilyMembers,
  fetchFamilyNotifications
} from '../../store/slices/parentSlice';
import { GridContainer } from '../../components/layout';

interface ChildData {
  id: string;
  name: string;
  avatar: string;
  level: number;
  currentXP: number;
  requiredXP: number;
  todayProgress: {
    timeSpent: number; // in minutes
    questsCompleted: number;
    xpEarned: number;
  };
  streak: number;
  grade: string;
}

interface Notification {
  id: string;
  type: 'achievement' | 'alert' | 'info';
  title: string;
  message: string;
  time: string;
  read: boolean;
}

interface Activity {
  id: string;
  childName: string;
  childAvatar: string;
  action: string;
  subject: string;
  time: string;
  xpEarned?: number;
}

const ParentDashboard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const { 
    connectedChildren, 
    familyDashboard,
    family,
    familyMembers,
    familyNotifications,
    isLoading 
  } = useAppSelector((state) => state.parent);
  const { subscribe } = useWebSocket();
  const [realTimeProgress, setRealTimeProgress] = useState<Record<string, any>>({});

  useEffect(() => {
    // Fetch parent data on component mount
    const loadDashboardData = async () => {
      try {
        // First get family info
        const familyResult = await dispatch(fetchMyFamily()).unwrap();
        
        if (familyResult && familyResult.id) {
          // Then load dashboard and members
          await Promise.all([
            dispatch(fetchFamilyDashboard()),
            dispatch(fetchFamilyMembers(familyResult.id)),
            dispatch(fetchFamilyNotifications())
          ]);
        }
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
        // Fallback to old endpoints
        dispatch(fetchConnectedChildren());
        dispatch(fetchParentNotifications());
      }
    };
    
    loadDashboardData();
  }, [dispatch]);

  // Subscribe to real-time updates
  useEffect(() => {
    const unsubscribeProgress = subscribe('child_progress_update', (data) => {
      console.log('Child progress update:', data);
      setRealTimeProgress(prev => ({
        ...prev,
        [data.user_id]: data
      }));
    });

    const unsubscribeNotification = subscribe('parent_notification', (data) => {
      console.log('Parent notification:', data);
      // Notification will be handled by the notification system
    });

    return () => {
      unsubscribeProgress();
      unsubscribeNotification();
    };
  }, [subscribe]);

  // Use actual user data or fallback to mock
  const parentName = user?.username || "Parent";
  
  // Use family dashboard data if available
  const dashboardChildren = familyDashboard?.children || [];
  
  // Map dashboard children to ChildData format or use mock
  const children: ChildData[] = dashboardChildren.length > 0 ? dashboardChildren.map(child => ({
    id: child.child_id.toString(),
    name: child.child_name,
    avatar: child.avatar_url || '/avatars/default.png',
    level: child.current_level,
    currentXP: child.today_stats?.xp || 0,
    requiredXP: child.today_stats?.next_level_xp || 1000,
    todayProgress: {
      timeSpent: child.today_stats?.time_spent || 0,
      questsCompleted: child.completed_quests_today || 0,
      xpEarned: child.today_stats?.xp_earned || 0,
    },
    streak: child.current_streak,
    grade: child.today_stats?.grade || 'Unknown',
  })) : [
    {
      id: '1',
      name: 'Emma',
      avatar: '/avatars/emma.png',
      level: 12,
      currentXP: 3200,
      requiredXP: 4000,
      todayProgress: {
        timeSpent: 45,
        questsCompleted: 3,
        xpEarned: 150,
      },
      streak: 7,
      grade: '5th Grade',
    },
    {
      id: '2',
      name: 'Lucas',
      avatar: '/avatars/lucas.png',
      level: 8,
      currentXP: 1800,
      requiredXP: 2500,
      todayProgress: {
        timeSpent: 30,
        questsCompleted: 2,
        xpEarned: 100,
      },
      streak: 3,
      grade: '3rd Grade',
    },
  ];

  // Use family notifications if available
  const apiNotifications = familyNotifications || [];
  
  // Map API notifications to component format or use mock
  const notifications: Notification[] = apiNotifications.length > 0 ? apiNotifications.map(notif => ({
    id: notif.id.toString(),
    type: notif.alert_type === 'achievement_unlocked' ? 'achievement' : 
          notif.severity === 'warning' ? 'alert' : 'info',
    title: notif.title,
    message: notif.message,
    time: new Date(notif.created_at).toLocaleString(),
    read: notif.is_read,
  })) : [
    {
      id: '1',
      type: 'achievement',
      title: 'Emma reached Level 12!',
      message: 'Completed the "Math Master" quest series',
      time: '2 hours ago',
      read: false,
    },
    {
      id: '2',
      type: 'alert',
      title: 'Screen time limit approaching',
      message: 'Lucas has 15 minutes remaining today',
      time: '3 hours ago',
      read: false,
    },
    {
      id: '3',
      type: 'info',
      title: 'Weekly report available',
      message: 'View detailed progress for both children',
      time: '1 day ago',
      read: true,
    },
  ];

  // Use dashboard activities if available
  const apiActivities = familyDashboard?.recent_activities || [];
  
  // Map API activities to component format or use mock
  const recentActivities: Activity[] = apiActivities.length > 0 ? apiActivities.map(activity => ({
    id: activity.id.toString(),
    childName: activity.child_name || 'Unknown',
    childAvatar: '/avatars/default.png',
    action: activity.activity_type,
    subject: activity.activity_data?.subject || 'General',
    time: new Date(activity.created_at).toLocaleString(),
    xpEarned: activity.activity_data?.xp_earned,
  })) : [
    {
      id: '1',
      childName: 'Emma',
      childAvatar: '/avatars/emma.png',
      action: 'completed',
      subject: 'Fractions Adventure Quest',
      time: '30 min ago',
      xpEarned: 50,
    },
    {
      id: '2',
      childName: 'Lucas',
      childAvatar: '/avatars/lucas.png',
      action: 'started',
      subject: 'Reading Comprehension Challenge',
      time: '1 hour ago',
    },
    {
      id: '3',
      childName: 'Emma',
      childAvatar: '/avatars/emma.png',
      action: 'earned achievement',
      subject: '7-Day Streak Badge',
      time: '2 hours ago',
      xpEarned: 100,
    },
  ];

  const formatTime = (minutes: number): string => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'achievement':
        return <CheckCircleIcon color="success" />;
      case 'alert':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Welcome Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Welcome back, {parentName}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's how your children are progressing today
        </Typography>
      </Box>

      <GridContainer spacing={3} columns={{ xs: 1, sm: 1, md: 1, lg: 1, xl: 1 }}>
        {/* Children Overview Cards */}
        <Box>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Children Overview
          </Typography>
          <GridContainer spacing={3} columns={{ xs: 1, sm: 1, md: 2, lg: 2, xl: 2 }}>
            {children.map((child) => (
              <Box key={child.id}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Avatar
                        src={child.avatar}
                        sx={{ width: 64, height: 64, mr: 2 }}
                      >
                        {child.name[0]}
                      </Avatar>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6">{child.name}</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={`Level ${child.level}`}
                            size="small"
                            color="primary"
                            icon={<StarIcon />}
                          />
                          <Typography variant="body2" color="text.secondary">
                            {child.grade}
                          </Typography>
                        </Box>
                      </Box>
                      <IconButton 
                        size="small"
                        onClick={() => navigate(`/parent/child/${child.id}`)}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </Box>

                    {/* Progress Bar */}
                    <Box sx={{ mb: 3 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2">Level Progress</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {child.currentXP} / {child.requiredXP} XP
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={(child.currentXP / child.requiredXP) * 100}
                        sx={{ height: 8, borderRadius: 1 }}
                      />
                    </Box>

                    {/* Today's Progress */}
                    <Typography variant="subtitle2" sx={{ mb: 2 }}>
                      Today's Progress
                    </Typography>
                    <GridContainer spacing={2} columns={{ xs: 3, sm: 3, md: 3, lg: 3, xl: 3 }} sx={{ mb: 2 }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <TimerIcon color="action" />
                        <Typography variant="h6">
                          {formatTime(child.todayProgress.timeSpent)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Time Spent
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <TrophyIcon color="action" />
                        <Typography variant="h6">
                          {child.todayProgress.questsCompleted}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Quests
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'center' }}>
                        <TrendingUpIcon color="action" />
                        <Typography variant="h6">
                          +{child.todayProgress.xpEarned}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          XP Earned
                        </Typography>
                      </Box>
                    </GridContainer>

                    {/* Real-time Progress Indicator */}
                    {realTimeProgress[child.id] && (
                      <Alert severity="info" sx={{ mb: 2 }}>
                        <Typography variant="body2">
                          Currently studying: {realTimeProgress[child.id].progress?.content_title || 'Unknown'}
                          ({Math.round(realTimeProgress[child.id].progress?.progress || 0)}% complete)
                        </Typography>
                      </Alert>
                    )}

                    {/* Streak */}
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        bgcolor: 'primary.light',
                        borderRadius: 2,
                        p: 1,
                      }}
                    >
                      <FireIcon color="error" sx={{ mr: 1 }} />
                      <Typography variant="body2" fontWeight="medium">
                        {child.streak} Day Streak!
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </GridContainer>
        </Box>

        {/* Notifications Panel and AI Insights Section */}
        <GridContainer spacing={3} columns={{ xs: 1, sm: 1, md: 3, lg: 3, xl: 3 }}>
          <Box sx={{ gridColumn: { xs: 'span 1', md: 'span 1' } }}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                  Notifications
                </Typography>
                <Badge badgeContent={2} color="error">
                  <NotificationsIcon />
                </Badge>
              </Box>
              <List sx={{ width: '100%' }}>
                {notifications.map((notification, index) => (
                  <React.Fragment key={notification.id}>
                    <ListItem
                      alignItems="flex-start"
                      sx={{
                        bgcolor: notification.read ? 'transparent' : 'action.hover',
                        borderRadius: 1,
                        mb: 1,
                      }}
                    >
                      <ListItemAvatar>
                        {getNotificationIcon(notification.type)}
                      </ListItemAvatar>
                      <ListItemText
                        primary={notification.title}
                        secondary={
                          <>
                            <Typography variant="body2" color="text.secondary">
                              {notification.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {notification.time}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                    {index < notifications.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          </Box>

          {/* AI Insights Section */}
          <Box sx={{ gridColumn: { xs: 'span 1', md: 'span 2' } }}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <AutoAwesomeIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">AI Insights</Typography>
              </Box>
              <Stack spacing={2}>
                <Alert severity="success" icon={<SchoolIcon />}>
                  <Typography variant="subtitle2">Strong Performance in Math</Typography>
                  <Typography variant="body2">
                    Emma shows exceptional progress in mathematics, completing 15% more
                    problems than average with 92% accuracy.
                  </Typography>
                </Alert>
                <Alert severity="info" icon={<TrendingUpIcon />}>
                  <Typography variant="subtitle2">Reading Improvement Opportunity</Typography>
                  <Typography variant="body2">
                    Lucas could benefit from more reading practice. Consider setting a
                    daily 20-minute reading goal to improve comprehension skills.
                  </Typography>
                </Alert>
                <Alert severity="warning" icon={<TimerIcon />}>
                  <Typography variant="subtitle2">Screen Time Pattern</Typography>
                  <Typography variant="body2">
                    Both children tend to use most of their screen time between 4-6 PM.
                    Consider spreading activities throughout the day for better engagement.
                  </Typography>
                </Alert>
              </Stack>
            </Paper>
          </Box>
        </GridContainer>

        {/* Recent Activities Timeline and Quick Actions */}
        <GridContainer spacing={3} columns={{ xs: 1, sm: 1, md: 3, lg: 3, xl: 3 }}>
          <Box sx={{ gridColumn: { xs: 'span 1', md: 'span 2' } }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Recent Activities
              </Typography>
              <List>
                {recentActivities.map((activity) => (
                  <ListItem key={activity.id} sx={{ px: 0 }}>
                    <ListItemAvatar>
                      <Avatar src={activity.childAvatar} sx={{ width: 40, height: 40 }}>
                        {activity.childName[0]}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Typography variant="body2">
                          <strong>{activity.childName}</strong> {activity.action}{' '}
                          <strong>{activity.subject}</strong>
                        </Typography>
                      }
                      secondary={activity.time}
                    />
                    {activity.xpEarned && (
                      <Chip
                        label={`+${activity.xpEarned} XP`}
                        size="small"
                        color="success"
                        variant="outlined"
                      />
                    )}
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Box>

          {/* Quick Actions */}
          <Box sx={{ gridColumn: { xs: 'span 1', md: 'span 1' } }}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Quick Actions
              </Typography>
              <Stack spacing={2}>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<AssessmentIcon />}
                  size="large"
                >
                  View Reports
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<TargetIcon />}
                  size="large"
                >
                  Set Goals
                </Button>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<SecurityIcon />}
                  size="large"
                >
                  Manage Controls
                </Button>
              </Stack>
            </Paper>
          </Box>
        </GridContainer>
      </GridContainer>
    </Box>
  );
};

export default ParentDashboard;