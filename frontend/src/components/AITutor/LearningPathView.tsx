import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Slider,
  Paper,
  Chip,
  LinearProgress,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Collapse,
  IconButton,
  Divider
} from '@mui/material';
import {
  School as SchoolIcon,
  Flag as FlagIcon,
  CheckCircle as CheckIcon,
  RadioButtonUnchecked as UncheckedIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Timer as TimerIcon,
  CalendarToday as CalendarIcon,
  TrendingUp as ProgressIcon
} from '@mui/icons-material';
import { aiTutorService, LearningPath, LearningPathRequest } from '../../services/aiTutor';

export const LearningPathView: React.FC = () => {
  const [goal, setGoal] = useState('');
  const [timelineDays, setTimelineDays] = useState(30);
  const [learningPath, setLearningPath] = useState<LearningPath | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedModules, setExpandedModules] = useState<Set<number>>(new Set());
  const [completedTopics, setCompletedTopics] = useState<Set<string>>(new Set());

  const handleCreatePath = async () => {
    if (!goal.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const request: LearningPathRequest = {
        goal: goal.trim(),
        timelineDays
      };
      const path = await aiTutorService.createLearningPath(request);
      setLearningPath(path);
    } catch (err) {
      setError('Failed to create learning path. Please try again.');
      console.error('Learning path creation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleModule = (moduleIndex: number) => {
    setExpandedModules(prev => {
      const newSet = new Set(prev);
      if (newSet.has(moduleIndex)) {
        newSet.delete(moduleIndex);
      } else {
        newSet.add(moduleIndex);
      }
      return newSet;
    });
  };

  const toggleTopicComplete = (topicId: string) => {
    setCompletedTopics(prev => {
      const newSet = new Set(prev);
      if (newSet.has(topicId)) {
        newSet.delete(topicId);
      } else {
        newSet.add(topicId);
      }
      return newSet;
    });
  };

  const calculateModuleProgress = (module: any) => {
    const moduleTopics = module.topics.map((t: string) => `${module.name}-${t}`);
    const completed = moduleTopics.filter((t: string) => completedTopics.has(t)).length;
    return (completed / moduleTopics.length) * 100;
  };

  const calculateOverallProgress = () => {
    if (!learningPath) return 0;
    const totalTopics = learningPath.modules.reduce((acc, m) => acc + m.topics.length, 0);
    return totalTopics > 0 ? (completedTopics.size / totalTopics) * 100 : 0;
  };

  if (!learningPath) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h5" gutterBottom>Create Your Learning Path</Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Tell us your learning goal, and we'll create a personalized path to help you achieve it.
          </Typography>
          
          <Box sx={{ mt: 3 }}>
            <TextField
              fullWidth
              label="What do you want to learn?"
              placeholder="e.g., Master calculus, Become fluent in Spanish, Learn web development"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              disabled={loading}
              sx={{ mb: 3 }}
            />
            
            <Box sx={{ mb: 3 }}>
              <Typography gutterBottom>Timeline: {timelineDays} days</Typography>
              <Slider
                value={timelineDays}
                onChange={(_, value) => setTimelineDays(value as number)}
                min={7}
                max={180}
                step={7}
                marks={[
                  { value: 7, label: '1 week' },
                  { value: 30, label: '1 month' },
                  { value: 90, label: '3 months' },
                  { value: 180, label: '6 months' }
                ]}
                disabled={loading}
              />
            </Box>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <Button
              variant="contained"
              size="large"
              onClick={handleCreatePath}
              disabled={!goal.trim() || loading}
              fullWidth
            >
              {loading ? 'Creating Your Path...' : 'Create Learning Path'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h5">{learningPath.goal}</Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <Chip 
                  icon={<CalendarIcon />} 
                  label={`${learningPath.durationDays} days`} 
                  size="small" 
                />
                <Chip 
                  icon={<SchoolIcon />} 
                  label={`${learningPath.modules.length} modules`} 
                  size="small" 
                />
              </Box>
            </Box>
            <Button 
              variant="outlined" 
              onClick={() => setLearningPath(null)}
            >
              Create New Path
            </Button>
          </Box>
          
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Overall Progress
              </Typography>
              <Typography variant="body2" color="primary">
                {calculateOverallProgress().toFixed(0)}%
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={calculateOverallProgress()} 
              sx={{ height: 8, borderRadius: 1 }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Modules */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 8 }}>
          <Typography variant="h6" gutterBottom>Learning Modules</Typography>
          {learningPath.modules.map((module, index) => (
            <Card key={index} sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6">
                      Module {module.order}: {module.name}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                      <Chip 
                        icon={<TimerIcon />} 
                        label={`${module.estimatedHours} hours`} 
                        size="small" 
                        variant="outlined"
                      />
                      <Chip 
                        icon={<ProgressIcon />} 
                        label={`${calculateModuleProgress(module).toFixed(0)}% complete`} 
                        size="small" 
                        color={calculateModuleProgress(module) === 100 ? "success" : "default"}
                      />
                    </Box>
                  </Box>
                  <IconButton onClick={() => toggleModule(index)}>
                    {expandedModules.has(index) ? <CollapseIcon /> : <ExpandIcon />}
                  </IconButton>
                </Box>
                
                <LinearProgress 
                  variant="determinate" 
                  value={calculateModuleProgress(module)} 
                  sx={{ mt: 2, mb: 1 }}
                />
                
                <Collapse in={expandedModules.has(index)}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" gutterBottom>Topics:</Typography>
                  <List dense>
                    {module.topics.map((topic, topicIdx) => {
                      const topicId = `${module.name}-${topic}`;
                      const isCompleted = completedTopics.has(topicId);
                      return (
                        <ListItem 
                          key={topicIdx}
                          onClick={() => toggleTopicComplete(topicId)}
                          sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                        >
                          <ListItemIcon>
                            {isCompleted ? (
                              <CheckIcon color="success" />
                            ) : (
                              <UncheckedIcon />
                            )}
                          </ListItemIcon>
                          <ListItemText 
                            primary={topic}
                            sx={{
                              textDecoration: isCompleted ? 'line-through' : 'none',
                              color: isCompleted ? 'text.secondary' : 'text.primary'
                            }}
                          />
                        </ListItem>
                      );
                    })}
                  </List>
                </Collapse>
              </CardContent>
            </Card>
          ))}
        </Grid>

        {/* Milestones Timeline */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Typography variant="h6" gutterBottom>Milestones</Typography>
          <Paper sx={{ p: 2 }}>
            <List>
              {learningPath.milestones.map((milestone, index) => (
                <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {index === learningPath.milestones.length - 1 ? <FlagIcon color="primary" /> : <CheckIcon color="success" />}
                      <Typography variant="subtitle2">
                        {milestone.title}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Day {milestone.day}
                    </Typography>
                  </Box>
                  <Box sx={{ ml: 4 }}>
                    {milestone.goals.map((goal, goalIdx) => (
                      <Typography key={goalIdx} variant="body2" color="text.secondary">
                        • {goal}
                      </Typography>
                    ))}
                    <Chip 
                      label={milestone.assessmentType} 
                      size="small" 
                      sx={{ mt: 1 }}
                    />
                  </Box>
                  {index < learningPath.milestones.length - 1 && <Divider sx={{ my: 2, width: '100%' }} />}
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
      </Grid>

      {/* Daily Schedule Preview */}
      {learningPath.dailySchedule && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Recommended Daily Schedule</Typography>
            <Alert severity="info" sx={{ mt: 2 }}>
              Based on your timeline, we recommend studying for about{' '}
              <strong>{Math.ceil(learningPath.modules.reduce((acc, m) => acc + m.estimatedHours, 0) / learningPath.durationDays * 60)} minutes</strong>{' '}
              per day to stay on track.
            </Alert>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};