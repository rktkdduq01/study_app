import React, { useState } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../../components/layout';
import {
  Container,
  
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  IconButton,
  Badge,
  Tooltip,
  Tabs,
  Tab,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Psychology,
  Chat,
  Timeline,
  Lightbulb,
  TrendingUp,
  School,
  EmojiEvents,
  History,
  Settings,
  Insights,
  QuestionAnswer,
  AutoAwesome,
  Star,
  NavigateNext,
  Celebration,
  Groups,
  MenuBook,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import AITutorChat from '../../components/ai-tutor/AITutorChat';
import GrowthRoadmapViewer from '../../components/ai-tutor/GrowthRoadmapViewer';
import { ConversationContext } from '../../types/ai-tutor';

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

const AITutorPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAppSelector((state) => state.auth);
  const { character } = useAppSelector((state) => state.character);
  const [tabValue, setTabValue] = useState(0);
  const [selectedContext, setSelectedContext] = useState<ConversationContext>(ConversationContext.GENERAL_HELP);

  const quickStartOptions = [
    {
      icon: <School />,
      title: 'Homework Help',
      description: 'Get help with your assignments',
      context: ConversationContext.PROBLEM_SOLVING,
      color: 'primary',
    },
    {
      icon: <Lightbulb />,
      title: 'Concept Explanation',
      description: 'Understand difficult topics',
      context: ConversationContext.CONCEPT_EXPLANATION,
      color: 'warning',
    },
    {
      icon: <EmojiEvents />,
      title: 'Quest Guidance',
      description: 'Find the perfect quests',
      context: ConversationContext.QUEST_GUIDANCE,
      color: 'success',
    },
    {
      icon: <Psychology />,
      title: 'Learning Strategy',
      description: 'Improve your study methods',
      context: ConversationContext.REVIEW,
      color: 'info',
    },
    {
      icon: <Celebration />,
      title: 'Motivation Boost',
      description: 'Get encouragement and support',
      context: ConversationContext.MOTIVATION,
      color: 'error',
    },
    {
      icon: <TrendingUp />,
      title: 'Career Guidance',
      description: 'Plan your future path',
      context: ConversationContext.CAREER_GUIDANCE,
      color: 'secondary',
    },
  ];

  const learningStats = {
    tutorSessions: 24,
    questsCompleted: 156,
    conceptsMastered: 48,
    averageScore: 87,
    streak: 12,
  };

  const renderDashboard = () => (
    <GridContainer columns={{ xs: 1 }}>
      {/* Welcome Card */}
      <Box>
        <Paper
          sx={{
            p: 3,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <Avatar
              sx={{
                width: 80,
                height: 80,
                bgcolor: 'rgba(255,255,255,0.2)',
              }}
            >
              <Psychology sx={{ fontSize: 48 }} />
            </Avatar>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h4" gutterBottom>
                Welcome to AI Tutor, {character?.name}! 🎓
              </Typography>
              <Typography variant="body1">
                I'm here to help you learn, grow, and achieve your goals. What would you like to work on today?
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Box>

      {/* Quick Start Options */}
      <Box>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AutoAwesome />
          Quick Start
        </Typography>
        <GridContainer columns={{ xs: 1, sm: 2, md: 3 }}>
          {quickStartOptions.map((option, index) => (
            <Box key={index}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => {
                  setSelectedContext(option.context);
                  setTabValue(1);
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <Avatar sx={{ bgcolor: `${option.color}.light` }}>
                      {React.cloneElement(option.icon, { color: option.color as any })}
                    </Avatar>
                    <Typography variant="h6">{option.title}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {option.description}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          ))}
        </GridContainer>
      </Box>

      {/* Learning Stats and Recent Insights */}
      <GridContainer columns={{ xs: 1, md: 3 }}>
        {/* Learning Stats - spans 2 columns on md */}
        <Box sx={{ gridColumn: { xs: 'span 1', md: 'span 2' } }}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUp />
            Your Learning Journey
          </Typography>
          <GridContainer columns={{ xs: 2, sm: 3 }}>
            <Box>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {learningStats.tutorSessions}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Tutor Sessions
                </Typography>
              </Box>
            </Box>
            <Box>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {learningStats.questsCompleted}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Quests Completed
                </Typography>
              </Box>
            </Box>
            <Box>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {learningStats.conceptsMastered}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Concepts Mastered
                </Typography>
              </Box>
            </Box>
            <Box>
              <Box sx={{ textAlign: 'center' }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 1 }}>
                  <Typography variant="h4" color="info.main">
                    {learningStats.averageScore}%
                  </Typography>
                  <TrendingUp color="success" />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Average Score
                </Typography>
              </Box>
            </Box>
            <Box>
              <Box sx={{ textAlign: 'center' }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 1 }}>
                  <Typography variant="h4" color="error.main">
                    {learningStats.streak}
                  </Typography>
                  <Badge badgeContent="🔥" sx={{ '& .MuiBadge-badge': { fontSize: 20 } }}>
                    <Box />
                  </Badge>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Day Streak
                </Typography>
              </Box>
            </Box>
          </GridContainer>
        </Paper>
      </Box>

      {/* Recent Insights - spans 1 column on md */}
      <Box sx={{ gridColumn: { xs: 'span 1', md: 'span 1' } }}>
        <Paper sx={{ p: 3, height: '100%' }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Insights />
            Recent Insights
          </Typography>
          <List>
            <ListItem>
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'success.light' }}>
                  <Star color="success" />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Math Mastery!"
                secondary="You've improved 25% in algebra"
              />
            </ListItem>
            <ListItem>
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'info.light' }}>
                  <Lightbulb color="info" />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="New Learning Style"
                secondary="Visual learning works best for you"
              />
            </ListItem>
            <ListItem>
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: 'warning.light' }}>
                  <TrendingUp color="warning" />
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary="Optimal Study Time"
                secondary="You focus best at 4-6 PM"
              />
            </ListItem>
          </List>
        </Paper>
      </Box>
      </GridContainer>

      {/* Growth Progress */}
      <Box>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Timeline />
            Growth Progress Preview
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              You're on track to reach Level 20 by next month! Keep up the great work!
            </Typography>
          </Alert>
          <Box sx={{ display: 'flex', justifyContent: 'center' }}>
            <Button
              variant="contained"
              onClick={() => setTabValue(2)}
              endIcon={<NavigateNext />}
            >
              View Full Roadmap
            </Button>
          </Box>
        </Paper>
      </Box>
    </GridContainer>
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Psychology color="primary" />
          AI Learning Tutor
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Your personal AI-powered learning companion
        </Typography>
      </Box>

      <Tabs value={tabValue} onChange={(_, value) => setTabValue(value)} sx={{ mb: 3 }}>
        <Tab label="Dashboard" icon={<Insights />} iconPosition="start" />
        <Tab 
          label="Chat with Tutor" 
          icon={
            <Badge badgeContent={2} color="error">
              <Chat />
            </Badge>
          } 
          iconPosition="start"
        />
        <Tab label="Growth Roadmap" icon={<Timeline />} iconPosition="start" />
        <Tab label="Session History" icon={<History />} iconPosition="start" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {renderDashboard()}
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        <AITutorChat context={selectedContext} embedded />
      </TabPanel>
      
      <TabPanel value={tabValue} index={2}>
        {user && <GrowthRoadmapViewer studentId={user.id.toString()} />}
      </TabPanel>
      
      <TabPanel value={tabValue} index={3}>
        <Alert severity="info">
          Session history coming soon! You'll be able to review all your past conversations and insights here.
        </Alert>
      </TabPanel>
    </Container>
  );
};

export default AITutorPage;
