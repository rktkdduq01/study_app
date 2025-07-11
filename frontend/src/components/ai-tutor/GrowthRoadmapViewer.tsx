import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemAvatar,
  Tabs,
  Tab,
  Alert,
  IconButton,
  Collapse,
  CircularProgress,
} from '@mui/material';
import Timeline from '@mui/lab/Timeline';
import TimelineItem from '@mui/lab/TimelineItem';
import TimelineSeparator from '@mui/lab/TimelineSeparator';
import TimelineConnector from '@mui/lab/TimelineConnector';
import TimelineContent from '@mui/lab/TimelineContent';
import TimelineDot from '@mui/lab/TimelineDot';
import TimelineOppositeContent from '@mui/lab/TimelineOppositeContent';
import {
  EmojiEvents,
  School,
  TrendingUp,
  CheckCircle,
  RadioButtonUnchecked,
  Star,
  Flag,
  NavigateNext,
  ExpandMore,
  ExpandLess,
  CalendarToday,
  Timer,
  Assignment,
  Psychology,
  Lightbulb,
  AutoAwesome,
  LocalFireDepartment,
  Timeline as TimelineIcon,
  Map,
  Explore,
  EmojiFlags,
  Celebration,
} from '@mui/icons-material';
import { 
  GrowthRoadmap, 
  Milestone, 
  Goal, 
  LearningPathNode,
  GrowthStage,
} from '../../types/ai-tutor';
import aiTutorService from '../../services/aiTutorService';
import { useNavigate } from 'react-router-dom';
import { GridContainer, FlexContainer, FlexRow } from '../layout';

interface GrowthRoadmapViewerProps {
  studentId: string;
  embedded?: boolean;
}

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

const GrowthRoadmapViewer: React.FC<GrowthRoadmapViewerProps> = ({
  studentId,
  embedded = false,
}) => {
  const navigate = useNavigate();
  const [roadmap, setRoadmap] = useState<GrowthRoadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [tabValue, setTabValue] = useState(0);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [selectedTimeframe, setSelectedTimeframe] = useState<'month' | 'quarter' | 'year'>('quarter');

  useEffect(() => {
    loadRoadmap();
  }, [studentId, selectedTimeframe]);

  const loadRoadmap = async () => {
    try {
      setLoading(true);
      const data = await aiTutorService.generateGrowthRoadmap(studentId, selectedTimeframe);
      setRoadmap(data);
    } catch (error) {
      console.error('Failed to load growth roadmap:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleNodeExpansion = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const getGoalIcon = (type: string) => {
    switch (type) {
      case 'academic': return <School />;
      case 'skill': return <Psychology />;
      case 'personal': return <Star />;
      case 'social': return <EmojiEvents />;
      default: return <Flag />;
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'concept': return <Lightbulb />;
      case 'skill': return <Psychology />;
      case 'project': return <Assignment />;
      case 'assessment': return <EmojiEvents />;
      default: return <School />;
    }
  };

  const renderCurrentStage = () => (
    <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <EmojiFlags />
          Current Stage: {roadmap?.currentStage.title}
        </Typography>
        <Typography variant="body1" paragraph>
          {roadmap?.currentStage.description}
        </Typography>
        
        <GridContainer spacing={2} columns={{xs: 1, md: 3}}>
          <Box>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ width: 60, height: 60, mx: 'auto', mb: 1, bgcolor: 'rgba(255,255,255,0.2)' }}>
                <Typography variant="h5">{roadmap?.currentStage.level}</Typography>
              </Avatar>
              <Typography variant="subtitle2">Current Level</Typography>
            </Box>
          </Box>
          <Box>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ width: 60, height: 60, mx: 'auto', mb: 1, bgcolor: 'rgba(255,255,255,0.2)' }}>
                <Typography variant="h5">{roadmap?.currentStage.masteredConcepts.length}</Typography>
              </Avatar>
              <Typography variant="subtitle2">Mastered Concepts</Typography>
            </Box>
          </Box>
          <Box>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ width: 60, height: 60, mx: 'auto', mb: 1, bgcolor: 'rgba(255,255,255,0.2)' }}>
                <Typography variant="h5">{roadmap?.milestones.filter(m => m.completed).length}</Typography>
              </Avatar>
              <Typography variant="subtitle2">Milestones Achieved</Typography>
            </Box>
          </Box>
        </GridContainer>

        {roadmap?.currentStage.currentFocus && roadmap.currentStage.currentFocus.length > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Current Focus Areas:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {roadmap.currentStage.currentFocus.map((focus, index) => (
                <Chip
                  key={index}
                  label={focus}
                  sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
                  icon={<LocalFireDepartment />}
                />
              ))}
            </Box>
          </Box>
        )}

        {roadmap?.currentStage.readyForNext && (
          <Alert severity="success" sx={{ mt: 2, bgcolor: 'rgba(255,255,255,0.1)', color: 'white' }}>
            <Typography variant="body2">
              🎉 Congratulations! You're ready to advance to the next stage!
            </Typography>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  const renderMilestones = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <EmojiEvents color="primary" />
        Milestones
      </Typography>
      
      <Timeline position="alternate">
        {roadmap?.milestones.map((milestone, index) => (
          <TimelineItem key={milestone.id}>
            <TimelineOppositeContent sx={{ color: 'text.secondary' }}>
              {milestone.completed ? (
                <Typography variant="caption">
                  Completed {new Date(milestone.completedAt!).toLocaleDateString()}
                </Typography>
              ) : (
                <Chip
                  label={`${milestone.progress}% Complete`}
                  size="small"
                  color={milestone.progress >= 75 ? 'success' : milestone.progress >= 50 ? 'warning' : 'default'}
                />
              )}
            </TimelineOppositeContent>
            
            <TimelineSeparator>
              <TimelineDot color={milestone.completed ? 'success' : 'grey'}>
                {milestone.completed ? <CheckCircle /> : <RadioButtonUnchecked />}
              </TimelineDot>
              {index < roadmap!.milestones.length - 1 && <TimelineConnector />}
            </TimelineSeparator>
            
            <TimelineContent>
              <Card sx={{ cursor: 'pointer' }} onClick={() => toggleNodeExpansion(milestone.id)}>
                <CardContent>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {milestone.title}
                    <IconButton size="small">
                      {expandedNodes.has(milestone.id) ? <ExpandLess /> : <ExpandMore />}
                    </IconButton>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {milestone.description}
                  </Typography>
                  
                  <Collapse in={expandedNodes.has(milestone.id)}>
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Requirements:
                      </Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            <School fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={`Level ${milestone.requiredLevel}`}
                            secondary="Required level"
                          />
                        </ListItem>
                        {milestone.requiredConcepts.map((concept, idx) => (
                          <ListItem key={idx}>
                            <ListItemIcon>
                              <Lightbulb fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={concept} />
                          </ListItem>
                        ))}
                      </List>
                      
                      {milestone.reward && (
                        <Alert severity="success" sx={{ mt: 2 }}>
                          <Typography variant="subtitle2">
                            Reward: {milestone.reward.value}
                          </Typography>
                        </Alert>
                      )}
                    </Box>
                  </Collapse>
                  
                  <LinearProgress
                    variant="determinate"
                    value={milestone.progress}
                    sx={{ mt: 2, height: 6, borderRadius: 3 }}
                  />
                </CardContent>
              </Card>
            </TimelineContent>
          </TimelineItem>
        ))}
      </Timeline>
    </Box>
  );

  const renderGoals = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Flag color="primary" />
        Goals
      </Typography>
      
      <GridContainer spacing={2} columns={{xs: 1, md: 2}}>
        {/* Short Term Goals */}
        <Box>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Timer />
              Short Term Goals
            </Typography>
            <List>
              {roadmap?.shortTermGoals.map((goal) => (
                <ListItem key={goal.id} sx={{ flexDirection: 'column', alignItems: 'stretch' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    {getGoalIcon(goal.type)}
                    <Typography variant="subtitle2">{goal.title}</Typography>
                    <Chip 
                      label={goal.timeframe}
                      size="small"
                      color={goal.timeframe === 'daily' ? 'success' : 'primary'}
                    />
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Target: {goal.measurableTarget}
                  </Typography>
                  
                  <Box sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption">Progress</Typography>
                      <Typography variant="caption">
                        {goal.currentProgress}/{goal.targetValue}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(goal.currentProgress / goal.targetValue) * 100}
                      sx={{ height: 6, borderRadius: 3 }}
                    />
                  </Box>
                  
                  {goal.relatedQuests.length > 0 && (
                    <Button
                      size="small"
                      startIcon={<Assignment />}
                      onClick={() => navigate(`/student/quests/${goal.relatedQuests[0]}`)}
                    >
                      Start Related Quest
                    </Button>
                  )}
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>

        {/* Long Term Goals */}
        <Box>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Explore />
              Long Term Goals
            </Typography>
            <List>
              {roadmap?.longTermGoals.map((goal) => (
                <ListItem key={goal.id}>
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'primary.light' }}>
                      {getGoalIcon(goal.type)}
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={goal.title}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          {goal.measurableTarget}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                          {goal.strategies.slice(0, 2).map((strategy, idx) => (
                            <Chip key={idx} label={strategy} size="small" />
                          ))}
                        </Box>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Box>
      </GridContainer>
    </Box>
  );

  const renderLearningPath = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Map color="primary" />
        Recommended Learning Path
      </Typography>
      
      <Stepper orientation="vertical" activeStep={0}>
        {roadmap?.recommendedPath.map((node, index) => (
          <Step key={node.id} expanded={expandedNodes.has(node.id)}>
            <StepLabel
              StepIconComponent={() => (
                <Avatar sx={{ width: 32, height: 32, bgcolor: index === 0 ? 'primary.main' : 'grey.400' }}>
                  {getNodeIcon(node.type)}
                </Avatar>
              )}
              onClick={() => toggleNodeExpansion(node.id)}
              sx={{ cursor: 'pointer' }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="subtitle1">{node.title}</Typography>
                <Chip label={node.type} size="small" />
                <Chip label={`${node.estimatedTime} min`} size="small" variant="outlined" />
              </Box>
            </StepLabel>
            <StepContent>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" paragraph>
                  Expected Outcomes:
                </Typography>
                <List dense>
                  {node.outcomes.map((outcome, idx) => (
                    <ListItem key={idx}>
                      <ListItemIcon>
                        <CheckCircle fontSize="small" color="success" />
                      </ListItemIcon>
                      <ListItemText primary={outcome} />
                    </ListItem>
                  ))}
                </List>
                
                {node.prerequisites.length > 0 && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <Typography variant="caption">
                      Prerequisites: {node.prerequisites.join(', ')}
                    </Typography>
                  </Alert>
                )}
                
                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => {/* Start learning activity */}}
                  >
                    Start Learning
                  </Button>
                </Box>
              </Box>
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {roadmap?.alternativePaths && roadmap.alternativePaths.length > 0 && (
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="body2">
            {roadmap.alternativePaths.length} alternative paths available based on your learning style
          </Typography>
        </Alert>
      )}
    </Box>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!roadmap) {
    return <Alert severity="error">Failed to load growth roadmap</Alert>;
  }

  return (
    <Box sx={{ maxHeight: embedded ? '500px' : 'auto', overflow: 'auto' }}>
      {/* Timeframe Selection */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center', gap: 1 }}>
        {(['month', 'quarter', 'year'] as const).map((timeframe) => (
          <Chip
            key={timeframe}
            label={timeframe.charAt(0).toUpperCase() + timeframe.slice(1)}
            onClick={() => setSelectedTimeframe(timeframe)}
            color={selectedTimeframe === timeframe ? 'primary' : 'default'}
            variant={selectedTimeframe === timeframe ? 'filled' : 'outlined'}
          />
        ))}
      </Box>

      {/* Current Stage Overview */}
      {renderCurrentStage()}

      {/* Next Checkpoint */}
      {roadmap.nextCheckpoint && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            <CalendarToday fontSize="small" sx={{ verticalAlign: 'middle', mr: 1 }} />
            Next Checkpoint: {new Date(roadmap.nextCheckpoint.date).toLocaleDateString()}
          </Typography>
          <Typography variant="body2">
            {roadmap.nextCheckpoint.assessmentType.replace('_', ' ')} - 
            Focus on: {roadmap.nextCheckpoint.goals.join(', ')}
          </Typography>
        </Alert>
      )}

      {/* Tabs */}
      <Tabs value={tabValue} onChange={(_, value) => setTabValue(value)} sx={{ mb: 2 }}>
        <Tab label="Learning Path" icon={<Map />} iconPosition="start" />
        <Tab label="Milestones" icon={<EmojiEvents />} iconPosition="start" />
        <Tab label="Goals" icon={<Flag />} iconPosition="start" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        {renderLearningPath()}
      </TabPanel>
      <TabPanel value={tabValue} index={1}>
        {renderMilestones()}
      </TabPanel>
      <TabPanel value={tabValue} index={2}>
        {renderGoals()}
      </TabPanel>

      {/* Estimated Completion */}
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Estimated completion: {roadmap.estimatedCompletion}
        </Typography>
      </Box>
    </Box>
  );
};

export default GrowthRoadmapViewer;