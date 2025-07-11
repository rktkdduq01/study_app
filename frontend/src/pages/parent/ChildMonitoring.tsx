import React, { useState } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../../components/layout';
import { useParams } from 'react-router-dom';
import {
  Box,
  Container,
  
  Paper,
  Typography,
  Avatar,
  Tabs,
  Tab,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Button,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemAvatar,
  Divider,
  TextField,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Rating,
  Tooltip,
  Badge,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp,
  AccessTime,
  EmojiEvents,
  Psychology,
  Settings,
  FilterList,
  CalendarToday,
  School,
  SportsEsports,
  Timer,
  Star,
  WorkspacePremium,
  Lightbulb,
  Warning,
  CheckCircle,
  ArrowUpward,
  ArrowDownward,
  Edit,
  Notifications,
  Shield,
  Speed,
  Calculate,
  Language,
  Science,
  Palette,
  MusicNote,
  SportsSoccer,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  RadarChart,
  Radar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const ChildMonitoring: React.FC = () => {
  const { childId } = useParams();
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [activityFilter, setActivityFilter] = useState('all');
  const [dateRange, setDateRange] = useState('week');

  // Mock data - replace with actual API calls
  const childData = {
    id: childId,
    name: 'Emma Johnson',
    avatar: '/avatar-emma.jpg',
    level: 15,
    points: 2450,
    streak: 7,
    totalActivities: 156,
    averageSessionTime: 35,
    strengths: ['Mathematics', 'Problem Solving', 'Creative Thinking'],
    weaknesses: ['Reading Comprehension', 'Time Management'],
  };

  const progressData = [
    { date: 'Mon', points: 320, activities: 5, time: 45 },
    { date: 'Tue', points: 280, activities: 4, time: 38 },
    { date: 'Wed', points: 350, activities: 6, time: 52 },
    { date: 'Thu', points: 310, activities: 5, time: 40 },
    { date: 'Fri', points: 380, activities: 7, time: 55 },
    { date: 'Sat', points: 340, activities: 6, time: 48 },
    { date: 'Sun', points: 300, activities: 5, time: 42 },
  ];

  const subjectPerformance = [
    { subject: 'Mathematics', score: 85, fullMark: 100 },
    { subject: 'Science', score: 78, fullMark: 100 },
    { subject: 'Language', score: 65, fullMark: 100 },
    { subject: 'Art', score: 92, fullMark: 100 },
    { subject: 'Music', score: 88, fullMark: 100 },
    { subject: 'Sports', score: 76, fullMark: 100 },
  ];

  const timeBreakdown = [
    { name: 'Mathematics', value: 30, color: '#8884d8' },
    { name: 'Science', value: 25, color: '#82ca9d' },
    { name: 'Language', value: 20, color: '#ffc658' },
    { name: 'Art', value: 15, color: '#ff7c7c' },
    { name: 'Other', value: 10, color: '#8dd1e1' },
  ];

  const activities = [
    {
      id: 1,
      title: 'Completed Math Challenge',
      subject: 'Mathematics',
      points: 50,
      time: '2 hours ago',
      type: 'challenge',
      duration: 15,
      performance: 92,
    },
    {
      id: 2,
      title: 'Science Quiz Attempted',
      subject: 'Science',
      points: 30,
      time: '4 hours ago',
      type: 'quiz',
      duration: 20,
      performance: 78,
    },
    {
      id: 3,
      title: 'Art Creation Project',
      subject: 'Art',
      points: 40,
      time: 'Yesterday',
      type: 'project',
      duration: 35,
      performance: 95,
    },
    {
      id: 4,
      title: 'Reading Comprehension',
      subject: 'Language',
      points: 25,
      time: 'Yesterday',
      type: 'reading',
      duration: 25,
      performance: 65,
    },
  ];

  const achievements = [
    {
      id: 1,
      title: 'Math Wizard',
      description: 'Complete 50 math challenges',
      progress: 45,
      total: 50,
      icon: Calculate,
      earned: false,
      rarity: 'gold',
    },
    {
      id: 2,
      title: 'Science Explorer',
      description: 'Discover 20 science concepts',
      progress: 20,
      total: 20,
      icon: Science,
      earned: true,
      earnedDate: '2024-01-15',
      rarity: 'silver',
    },
    {
      id: 3,
      title: 'Creative Artist',
      description: 'Create 30 art projects',
      progress: 28,
      total: 30,
      icon: Palette,
      earned: false,
      rarity: 'gold',
    },
    {
      id: 4,
      title: 'Consistent Learner',
      description: 'Maintain a 7-day streak',
      progress: 7,
      total: 7,
      icon: Star,
      earned: true,
      earnedDate: '2024-01-20',
      rarity: 'bronze',
    },
  ];

  const aiInsights = [
    {
      type: 'strength',
      title: 'Exceptional Problem-Solving Skills',
      description: 'Emma shows remarkable ability in solving complex mathematical problems, often using creative approaches.',
      recommendation: 'Consider enrolling in advanced mathematics programs or competitions.',
      confidence: 92,
    },
    {
      type: 'improvement',
      title: 'Reading Speed Below Average',
      description: 'Reading comprehension scores indicate slower processing of text-based content.',
      recommendation: 'Implement daily 15-minute reading sessions with progressively complex texts.',
      confidence: 87,
    },
    {
      type: 'pattern',
      title: 'Peak Performance Times',
      description: 'Analysis shows highest engagement and performance between 3-5 PM.',
      recommendation: 'Schedule challenging activities during these peak hours.',
      confidence: 94,
    },
    {
      type: 'suggestion',
      title: 'Cross-Subject Integration',
      description: 'Emma excels when subjects are interconnected, especially math and art.',
      recommendation: 'Look for activities that combine mathematical concepts with creative projects.',
      confidence: 89,
    },
  ];

  const getSubjectIcon = (subject: string) => {
    const icons: { [key: string]: React.ElementType } = {
      Mathematics: Calculate,
      Science: Science,
      Language: Language,
      Art: Palette,
      Music: MusicNote,
      Sports: SportsSoccer,
    };
    return icons[subject] || School;
  };

  const getActivityTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      challenge: theme.palette.error.main,
      quiz: theme.palette.warning.main,
      project: theme.palette.success.main,
      reading: theme.palette.info.main,
    };
    return colors[type] || theme.palette.primary.main;
  };

  const getRarityColor = (rarity: string) => {
    const colors: { [key: string]: string } = {
      bronze: '#CD7F32',
      silver: '#C0C0C0',
      gold: '#FFD700',
    };
    return colors[rarity] || theme.palette.grey[500];
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Child Header */}
      <Paper
        elevation={0}
        sx={{
          p: 4,
          mb: 3,
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
          color: 'white',
          borderRadius: 3,
        }}
      >
        <GridContainer spacing={3} alignItems="center">
          <Box>
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              badgeContent={
                <Box
                  sx={{
                    bgcolor: theme.palette.success.main,
                    color: 'white',
                    borderRadius: '50%',
                    width: 24,
                    height: 24,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    fontWeight: 'bold',
                    border: '2px solid white',
                  }}
                >
                  {childData.level}
                </Box>
              }
            >
              <Avatar
                sx={{
                  width: 100,
                  height: 100,
                  border: '4px solid white',
                  boxShadow: theme.shadows[3],
                }}
              >
                {childData.name.charAt(0)}
              </Avatar>
            </Badge>
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h3" fontWeight="bold" gutterBottom>
              {childData.name}
            </Typography>
            <GridContainer spacing={4}>
              <Box>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Total Points
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {childData.points.toLocaleString()}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Learning Streak
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {childData.streak} days
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Activities Completed
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {childData.totalActivities}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Avg. Session Time
                </Typography>
                <Typography variant="h5" fontWeight="bold">
                  {childData.averageSessionTime} min
                </Typography>
              </Box>
            </GridContainer>
          </Box>
          <Box>
            <Button
              variant="outlined"
              color="inherit"
              startIcon={<Edit />}
              sx={{
                borderColor: 'white',
                color: 'white',
                '&:hover': {
                  borderColor: 'white',
                  bgcolor: alpha(theme.palette.common.white, 0.1),
                },
              }}
            >
              Edit Profile
            </Button>
          </Box>
        </GridContainer>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              py: 2,
              fontSize: '1rem',
              fontWeight: 500,
            },
          }}
        >
          <Tab icon={<TrendingUp />} label="Overview" iconPosition="start" />
          <Tab icon={<AccessTime />} label="Activities" iconPosition="start" />
          <Tab icon={<EmojiEvents />} label="Achievements" iconPosition="start" />
          <Tab icon={<Psychology />} label="AI Analysis" iconPosition="start" />
          <Tab icon={<Settings />} label="Settings" iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Overview Tab */}
      <TabPanel value={activeTab} index={0}>
        <GridContainer spacing={3}>
          {/* Progress Charts */}
          <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 8' } }}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
                <Typography variant="h6" fontWeight="bold">
                  Learning Progress
                </Typography>
                <TextField
                  select
                  size="small"
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  sx={{ minWidth: 120 }}
                >
                  <MenuItem value="week">This Week</MenuItem>
                  <MenuItem value="month">This Month</MenuItem>
                  <MenuItem value="year">This Year</MenuItem>
                </TextField>
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={progressData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <ChartTooltip />
                  <Legend />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="points"
                    stroke={theme.palette.primary.main}
                    strokeWidth={2}
                    name="Points Earned"
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="time"
                    stroke={theme.palette.secondary.main}
                    strokeWidth={2}
                    name="Time (min)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>
          </Box>

          {/* Quick Stats */}
          <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 4' } }}>
            <GridContainer spacing={2}>
              <Box sx={{ gridColumn: 'span 12' }}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <TrendingUp sx={{ color: theme.palette.success.main, mr: 1 }} />
                      <Typography variant="h6">Weekly Progress</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1 }}>
                      <Typography variant="h4" fontWeight="bold">
                        +15%
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                        vs last week
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={75}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ gridColumn: 'span 12' }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Strengths
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {childData.strengths.map((strength) => (
                        <Chip
                          key={strength}
                          label={strength}
                          color="success"
                          size="small"
                          icon={<CheckCircle />}
                        />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Box>
              <Box sx={{ gridColumn: 'span 12' }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Areas to Improve
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {childData.weaknesses.map((weakness) => (
                        <Chip
                          key={weakness}
                          label={weakness}
                          color="warning"
                          size="small"
                          icon={<Warning />}
                        />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            </GridContainer>
          </Box>

          {/* Subject Performance Radar */}
          <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Subject Performance
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={subjectPerformance}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar
                    name="Performance"
                    dataKey="score"
                    stroke={theme.palette.primary.main}
                    fill={theme.palette.primary.main}
                    fillOpacity={0.6}
                  />
                  <ChartTooltip />
                </RadarChart>
              </ResponsiveContainer>
            </Paper>
          </Box>

          {/* Time Breakdown */}
          <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                Time Spent by Subject
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={timeBreakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {timeBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Paper>
          </Box>
        </GridContainer>
      </TabPanel>

      {/* Activities Tab */}
      <TabPanel value={activeTab} index={1}>
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h6" fontWeight="bold">
              Activity Log
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                select
                size="small"
                value={activityFilter}
                onChange={(e) => setActivityFilter(e.target.value)}
                sx={{ minWidth: 150 }}
                label="Filter by Type"
              >
                <MenuItem value="all">All Activities</MenuItem>
                <MenuItem value="challenge">Challenges</MenuItem>
                <MenuItem value="quiz">Quizzes</MenuItem>
                <MenuItem value="project">Projects</MenuItem>
                <MenuItem value="reading">Reading</MenuItem>
              </TextField>
              <Button startIcon={<CalendarToday />} variant="outlined">
                Date Range
              </Button>
            </Box>
          </Box>

          <List>
            {activities.map((activity, index) => (
              <React.Fragment key={activity.id}>
                <ListItem
                  sx={{
                    borderRadius: 2,
                    mb: 1,
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                    },
                  }}
                >
                  <ListItemAvatar>
                    <Avatar
                      sx={{
                        bgcolor: alpha(getActivityTypeColor(activity.type), 0.1),
                        color: getActivityTypeColor(activity.type),
                      }}
                    >
                      {React.createElement(getSubjectIcon(activity.subject))}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1" fontWeight="medium">
                          {activity.title}
                        </Typography>
                        <Chip
                          label={activity.type}
                          size="small"
                          sx={{
                            bgcolor: alpha(getActivityTypeColor(activity.type), 0.1),
                            color: getActivityTypeColor(activity.type),
                          }}
                        />
                      </Box>
                    }
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                          {activity.time}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Timer fontSize="small" />
                          <Typography variant="body2">{activity.duration} min</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Star fontSize="small" sx={{ color: theme.palette.warning.main }} />
                          <Typography variant="body2">+{activity.points} points</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <Speed fontSize="small" />
                          <Typography variant="body2">{activity.performance}%</Typography>
                        </Box>
                      </Box>
                    }
                  />
                  <IconButton edge="end">
                    <ArrowUpward
                      sx={{
                        color:
                          activity.performance >= 80
                            ? theme.palette.success.main
                            : theme.palette.warning.main,
                      }}
                    />
                  </IconButton>
                </ListItem>
                {index < activities.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>

          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Button variant="outlined">Load More Activities</Button>
          </Box>
        </Paper>
      </TabPanel>

      {/* Achievements Tab */}
      <TabPanel value={activeTab} index={2}>
        <GridContainer spacing={3}>
          <Box sx={{ gridColumn: 'span 12' }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="subtitle2">
                Emma has earned 12 achievements and is working towards 8 more!
              </Typography>
            </Alert>
          </Box>

          {achievements.map((achievement) => (
            <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }} key={achievement.id}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Card
                  sx={{
                    height: '100%',
                    borderWidth: 2,
                    borderStyle: 'solid',
                    borderColor: achievement.earned
                      ? getRarityColor(achievement.rarity)
                      : 'transparent',
                    bgcolor: achievement.earned
                      ? alpha(getRarityColor(achievement.rarity), 0.05)
                      : 'background.paper',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                >
                  {achievement.earned && (
                    <Box
                      sx={{
                        position: 'absolute',
                        top: 10,
                        right: 10,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                      }}
                    >
                      <CheckCircle sx={{ color: theme.palette.success.main, fontSize: 20 }} />
                      <Typography variant="caption" color="success.main">
                        Earned
                      </Typography>
                    </Box>
                  )}
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Avatar
                        sx={{
                          width: 60,
                          height: 60,
                          bgcolor: achievement.earned
                            ? getRarityColor(achievement.rarity)
                            : theme.palette.grey[300],
                          color: achievement.earned ? 'white' : theme.palette.grey[600],
                        }}
                      >
                        {React.createElement(achievement.icon, { fontSize: 'large' })}
                      </Avatar>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" fontWeight="bold">
                          {achievement.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {achievement.description}
                        </Typography>
                        {achievement.earned && (
                          <Typography variant="caption" color="text.secondary">
                            Earned on {achievement.earnedDate}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                    {!achievement.earned && (
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Progress</Typography>
                          <Typography variant="body2" fontWeight="bold">
                            {achievement.progress} / {achievement.total}
                          </Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={(achievement.progress / achievement.total) * 100}
                          sx={{
                            height: 8,
                            borderRadius: 4,
                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                            '& .MuiLinearProgress-bar': {
                              bgcolor: getRarityColor(achievement.rarity),
                            },
                          }}
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            </Box>
          ))}
        </GridContainer>
      </TabPanel>

      {/* AI Analysis Tab */}
      <TabPanel value={activeTab} index={3}>
        <GridContainer spacing={3}>
          {aiInsights.map((insight, index) => (
            <Box sx={{ gridColumn: 'span 12' }} key={index}>
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <Card
                  sx={{
                    borderLeft: 4,
                    borderColor:
                      insight.type === 'strength'
                        ? theme.palette.success.main
                        : insight.type === 'improvement'
                        ? theme.palette.warning.main
                        : insight.type === 'pattern'
                        ? theme.palette.info.main
                        : theme.palette.primary.main,
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                      <Avatar
                        sx={{
                          bgcolor:
                            insight.type === 'strength'
                              ? alpha(theme.palette.success.main, 0.1)
                              : insight.type === 'improvement'
                              ? alpha(theme.palette.warning.main, 0.1)
                              : insight.type === 'pattern'
                              ? alpha(theme.palette.info.main, 0.1)
                              : alpha(theme.palette.primary.main, 0.1),
                          color:
                            insight.type === 'strength'
                              ? theme.palette.success.main
                              : insight.type === 'improvement'
                              ? theme.palette.warning.main
                              : insight.type === 'pattern'
                              ? theme.palette.info.main
                              : theme.palette.primary.main,
                        }}
                      >
                        {insight.type === 'strength' ? (
                          <CheckCircle />
                        ) : insight.type === 'improvement' ? (
                          <Warning />
                        ) : insight.type === 'pattern' ? (
                          <Psychology />
                        ) : (
                          <Lightbulb />
                        )}
                      </Avatar>
                      <Box sx={{ flexGrow: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                          <Typography variant="h6" fontWeight="bold">
                            {insight.title}
                          </Typography>
                          <Chip
                            label={`${insight.confidence}% confidence`}
                            size="small"
                            color={insight.confidence >= 90 ? 'success' : 'primary'}
                          />
                        </Box>
                        <Typography variant="body1" color="text.secondary" paragraph>
                          {insight.description}
                        </Typography>
                        <Alert
                          severity="info"
                          icon={<Lightbulb />}
                          sx={{
                            bgcolor: alpha(theme.palette.info.main, 0.05),
                            border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
                          }}
                        >
                          <Typography variant="body2">
                            <strong>Recommendation:</strong> {insight.recommendation}
                          </Typography>
                        </Alert>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </motion.div>
            </Box>
          ))}

          <Box sx={{ gridColumn: 'span 12' }}>
            <Paper sx={{ p: 3, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Psychology sx={{ color: theme.palette.primary.main, fontSize: 32 }} />
                <Typography variant="h6" fontWeight="bold">
                  AI Learning Profile Summary
                </Typography>
              </Box>
              <Typography variant="body1" paragraph>
                Based on comprehensive analysis of Emma's learning patterns, she demonstrates a
                visual-kinesthetic learning style with strong analytical capabilities. Her optimal
                learning occurs through hands-on activities and visual representations, particularly
                in STEM subjects.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Chip label="Visual Learner" color="primary" />
                <Chip label="Problem Solver" color="primary" />
                <Chip label="Creative Thinker" color="primary" />
                <Chip label="Afternoon Peak Performance" color="primary" />
              </Box>
            </Paper>
          </Box>
        </GridContainer>
      </TabPanel>

      {/* Settings Tab */}
      <TabPanel value={activeTab} index={4}>
        <GridContainer spacing={3}>
          <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <Shield sx={{ color: theme.palette.primary.main }} />
                  <Typography variant="h6" fontWeight="bold">
                    Parental Controls
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Screen Time Limits"
                  />
                  <FormControlLabel control={<Switch defaultChecked />} label="Content Filtering" />
                  <FormControlLabel
                    control={<Switch />}
                    label="Purchase Restrictions"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Progress Notifications"
                  />
                  <TextField
                    fullWidth
                    label="Daily Time Limit"
                    type="number"
                    defaultValue={60}
                    InputProps={{
                      endAdornment: <Typography variant="body2">minutes</Typography>,
                    }}
                    helperText="Maximum daily screen time"
                  />
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <School sx={{ color: theme.palette.primary.main }} />
                  <Typography variant="h6" fontWeight="bold">
                    Learning Preferences
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    fullWidth
                    select
                    label="Difficulty Level"
                    defaultValue="adaptive"
                  >
                    <MenuItem value="easy">Easy</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="hard">Hard</MenuItem>
                    <MenuItem value="adaptive">Adaptive</MenuItem>
                  </TextField>
                  <TextField
                    fullWidth
                    select
                    label="Learning Style"
                    defaultValue="visual"
                  >
                    <MenuItem value="visual">Visual</MenuItem>
                    <MenuItem value="auditory">Auditory</MenuItem>
                    <MenuItem value="kinesthetic">Kinesthetic</MenuItem>
                    <MenuItem value="mixed">Mixed</MenuItem>
                  </TextField>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Enable AI Recommendations"
                  />
                  <FormControlLabel control={<Switch defaultChecked />} label="Adaptive Learning" />
                  <FormControlLabel control={<Switch />} label="Competition Mode" />
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <Notifications sx={{ color: theme.palette.primary.main }} />
                  <Typography variant="h6" fontWeight="bold">
                    Notification Settings
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Daily Progress Summary"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Achievement Alerts"
                  />
                  <FormControlLabel
                    control={<Switch />}
                    label="Low Activity Warnings"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Weekly Reports"
                  />
                  <TextField
                    fullWidth
                    select
                    label="Report Frequency"
                    defaultValue="weekly"
                  >
                    <MenuItem value="daily">Daily</MenuItem>
                    <MenuItem value="weekly">Weekly</MenuItem>
                    <MenuItem value="monthly">Monthly</MenuItem>
                  </TextField>
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <WorkspacePremium sx={{ color: theme.palette.primary.main }} />
                  <Typography variant="h6" fontWeight="bold">
                    Goals & Rewards
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    fullWidth
                    label="Weekly Point Goal"
                    type="number"
                    defaultValue={1000}
                    helperText="Points to earn each week"
                  />
                  <TextField
                    fullWidth
                    label="Weekly Activity Goal"
                    type="number"
                    defaultValue={20}
                    helperText="Activities to complete each week"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked />}
                    label="Enable Reward System"
                  />
                  <FormControlLabel
                    control={<Switch />}
                    label="Real-world Rewards"
                  />
                  <Button variant="outlined" fullWidth>
                    Manage Reward Settings
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ gridColumn: 'span 12' }}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button variant="outlined">Reset to Defaults</Button>
              <Button variant="contained">Save Settings</Button>
            </Box>
          </Box>
        </GridContainer>
      </TabPanel>
    </Container>
  );
};

export default ChildMonitoring;
