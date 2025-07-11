import React, { useEffect, useState } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../../components/layout';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  
  Chip,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  Divider,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  ArrowBack,
  PlayArrow,
  EmojiEvents,
  School,
  AccessTime,
  CheckCircle,
  Quiz,
  VideoLibrary,
  Code,
  Lightbulb,
  Star,
  Timer,
} from '@mui/icons-material';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { useAppSelector } from '../../hooks/useAppSelector';
import { fetchQuestById, startQuest, submitQuestAnswer, completeQuest } from '../../store/slices/questSlice';
import { QuestType, QuestDifficulty, QuestStatus } from '../../types/quest';
import Loading from '../../components/common/Loading';
import ErrorAlert from '../../components/common/ErrorAlert';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const QuestDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  
  const { currentQuest, isLoading, error } = useAppSelector((state) => state.quest);
  const { character } = useAppSelector((state) => state.character);
  const [tabValue, setTabValue] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [showCompletionDialog, setShowCompletionDialog] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [startTime, setStartTime] = useState<Date | null>(null);

  useEffect(() => {
    if (id) {
      dispatch(fetchQuestById(Number(id)));
    }
  }, [dispatch, id]);

  useEffect(() => {
    if (isPlaying && startTime) {
      const timer = setInterval(() => {
        setTimeSpent(Math.floor((new Date().getTime() - startTime.getTime()) / 1000));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [isPlaying, startTime]);

  const handleStartQuest = async () => {
    if (!currentQuest || !character) return;
    
    try {
      await dispatch(startQuest({ questId: currentQuest.id, characterId: character.id })).unwrap();
      setIsPlaying(true);
      setStartTime(new Date());
      setTabValue(1);
    } catch (error) {
      console.error('Failed to start quest:', error);
    }
  };

  const handleAnswerChange = (questionIndex: number, answer: string) => {
    setAnswers({
      ...answers,
      [questionIndex]: answer,
    });
  };

  const handleSubmitAnswer = async (questionIndex: number) => {
    if (!currentQuest || !answers[questionIndex]) return;
    
    try {
      await dispatch(submitQuestAnswer({
        questId: currentQuest.id,
        questionIndex,
        answer: answers[questionIndex],
      })).unwrap();
      
      if (questionIndex < (currentQuest.content?.questions?.length || 0) - 1) {
        setCurrentStep(questionIndex + 1);
      } else {
        handleCompleteQuest();
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const handleCompleteQuest = async () => {
    if (!currentQuest) return;
    
    try {
      await dispatch(completeQuest({
        questId: currentQuest.id,
        timeSpent,
      })).unwrap();
      setShowCompletionDialog(true);
    } catch (error) {
      console.error('Failed to complete quest:', error);
    }
  };

  const getDifficultyColor = (difficulty: QuestDifficulty) => {
    switch (difficulty) {
      case QuestDifficulty.EASY:
        return 'success';
      case QuestDifficulty.MEDIUM:
        return 'warning';
      case QuestDifficulty.HARD:
        return 'error';
      case QuestDifficulty.EXPERT:
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getQuestTypeIcon = (type: QuestType) => {
    switch (type) {
      case QuestType.LESSON:
        return <VideoLibrary />;
      case QuestType.QUIZ:
        return <Quiz />;
      case QuestType.PROJECT:
        return <Code />;
      case QuestType.CHALLENGE:
        return <EmojiEvents />;
      default:
        return <School />;
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return <Loading message="Loading quest details..." />;
  }

  if (error) {
    return <ErrorAlert message={error} onRetry={() => dispatch(fetchQuestById(Number(id)))} />;
  }

  if (!currentQuest) {
    return (
      <Container>
        <Alert severity="error">Quest not found</Alert>
      </Container>
    );
  }

  const userProgress = currentQuest.user_progress?.[0];
  const canStart = !userProgress || userProgress.status !== QuestStatus.COMPLETED;

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/student/quests')}
          sx={{ mb: 2 }}
        >
          Back to Quests
        </Button>
        
        <Paper sx={{ p: 3 }}>
          <GridContainer spacing={3} alignItems="center">
            <Box sx={{ width: { xs: '100%', md: '66.666%' } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                {getQuestTypeIcon(currentQuest.type)}
                <Typography variant="h4">{currentQuest.title}</Typography>
              </Box>
              
              <Typography variant="body1" color="text.secondary" paragraph>
                {currentQuest.description}
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label={currentQuest.type}
                  size="small"
                  icon={getQuestTypeIcon(currentQuest.type)}
                />
                <Chip
                  label={currentQuest.difficulty}
                  size="small"
                  color={getDifficultyColor(currentQuest.difficulty)}
                />
                <Chip
                  label={currentQuest.subject}
                  size="small"
                  icon={<School />}
                />
                <Chip
                  label={`${currentQuest.exp_reward} XP`}
                  size="small"
                  icon={<Star />}
                  variant="outlined"
                />
                {currentQuest.coin_reward > 0 && (
                  <Chip
                    label={`${currentQuest.coin_reward} Coins`}
                    size="small"
                    variant="outlined"
                  />
                )}
                <Chip
                  label={`${currentQuest.estimated_duration} min`}
                  size="small"
                  icon={<AccessTime />}
                  variant="outlined"
                />
              </Box>
            </Box>
            
            <Box sx={{ width: { xs: '100%', md: '33.333%' } }}>
              <Box sx={{ textAlign: 'center' }}>
                {userProgress ? (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Progress
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={userProgress.completion_percentage}
                      sx={{ mb: 1, height: 8, borderRadius: 4 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {userProgress.completion_percentage}% Complete
                    </Typography>
                    {userProgress.status === QuestStatus.COMPLETED && (
                      <Chip
                        label="Completed"
                        color="success"
                        icon={<CheckCircle />}
                        sx={{ mt: 1 }}
                      />
                    )}
                  </Box>
                ) : (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Ready to Start?
                    </Typography>
                    <Button
                      variant="contained"
                      size="large"
                      startIcon={<PlayArrow />}
                      onClick={handleStartQuest}
                      disabled={!canStart || isPlaying}
                      sx={{ mt: 2 }}
                    >
                      Start Quest
                    </Button>
                  </Box>
                )}
              </Box>
            </Box>
          </GridContainer>
        </Paper>
      </Box>

      {/* Content Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, value) => setTabValue(value)}>
          <Tab label="Overview" />
          <Tab label="Play" disabled={!isPlaying} />
          <Tab label="Requirements" />
          <Tab label="Rewards" />
        </Tabs>
        
        <TabPanel value={tabValue} index={0}>
          <GridContainer spacing={3}>
            <Box sx={{ width: { xs: '100%', md: '66.666%' } }}>
              <Typography variant="h6" gutterBottom>
                What You'll Learn
              </Typography>
              <List>
                {currentQuest.objectives?.map((objective, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <Lightbulb color="primary" />
                    </ListItemIcon>
                    <ListItemText primary={objective} />
                  </ListItem>
                ))}
              </List>
              
              {currentQuest.long_description && (
                <>
                  <Divider sx={{ my: 3 }} />
                  <Typography variant="h6" gutterBottom>
                    Detailed Description
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {currentQuest.long_description}
                  </Typography>
                </>
              )}
            </Box>
            
            <Box sx={{ width: { xs: '100%', md: '33.333%' } }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Quest Stats
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Completion Rate
                      </Typography>
                      <Typography variant="h6">
                        {currentQuest.completion_rate || 0}%
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Average Time
                      </Typography>
                      <Typography variant="h6">
                        {currentQuest.average_completion_time || currentQuest.estimated_duration} min
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Total Attempts
                      </Typography>
                      <Typography variant="h6">
                        {currentQuest.total_attempts || 0}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </GridContainer>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          {isPlaying && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">
                  Quest Progress
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Chip
                    icon={<Timer />}
                    label={formatTime(timeSpent)}
                    color="primary"
                  />
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => setIsPlaying(false)}
                  >
                    Pause Quest
                  </Button>
                </Box>
              </Box>
              
              {currentQuest.content?.questions && (
                <Stepper activeStep={currentStep} orientation="vertical">
                  {currentQuest.content.questions.map((question, index) => (
                    <Step key={index}>
                      <StepLabel>
                        Question {index + 1}
                      </StepLabel>
                      <StepContent>
                        <Typography variant="body1" paragraph>
                          {question.question}
                        </Typography>
                        
                        {question.type === 'multiple_choice' && (
                          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                            {question.options?.map((option: string, optionIndex: number) => (
                              <Button
                                key={optionIndex}
                                variant={answers[index] === option ? 'contained' : 'outlined'}
                                onClick={() => handleAnswerChange(index, option)}
                                sx={{ justifyContent: 'flex-start' }}
                              >
                                {option}
                              </Button>
                            ))}
                          </Box>
                        )}
                        
                        {question.type === 'short_answer' && (
                          <TextField
                            fullWidth
                            multiline
                            rows={3}
                            value={answers[index] || ''}
                            onChange={(e) => handleAnswerChange(index, e.target.value)}
                            placeholder="Type your answer here..."
                            sx={{ mb: 2 }}
                          />
                        )}
                        
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button
                            variant="contained"
                            onClick={() => handleSubmitAnswer(index)}
                            disabled={!answers[index]}
                          >
                            Submit Answer
                          </Button>
                          {index > 0 && (
                            <Button
                              onClick={() => setCurrentStep(index - 1)}
                            >
                              Previous
                            </Button>
                          )}
                        </Box>
                      </StepContent>
                    </Step>
                  ))}
                </Stepper>
              )}
              
              {currentQuest.type === QuestType.LESSON && currentQuest.content?.lesson && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Lesson Content
                  </Typography>
                  <Card>
                    <CardContent>
                      <Typography variant="body1">
                        {currentQuest.content.lesson}
                      </Typography>
                    </CardContent>
                  </Card>
                  <Box sx={{ mt: 3, textAlign: 'center' }}>
                    <Button
                      variant="contained"
                      size="large"
                      onClick={handleCompleteQuest}
                    >
                      Complete Lesson
                    </Button>
                  </Box>
                </Box>
              )}
            </Box>
          )}
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Prerequisites
          </Typography>
          {currentQuest.prerequisites && currentQuest.prerequisites.length > 0 ? (
            <List>
              {currentQuest.prerequisites.map((prereq, index) => (
                <ListItem key={index}>
                  <ListItemIcon>
                    <CheckCircle color="action" />
                  </ListItemIcon>
                  <ListItemText primary={prereq} />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body1" color="text.secondary">
              No prerequisites required
            </Typography>
          )}
          
          <Divider sx={{ my: 3 }} />
          
          <Typography variant="h6" gutterBottom>
            Recommended Level
          </Typography>
          <Typography variant="body1">
            Level {currentQuest.min_level} or higher
          </Typography>
        </TabPanel>
        
        <TabPanel value={tabValue} index={3}>
          <GridContainer spacing={3}>
            <Box sx={{ width: { xs: '100%', md: '50%' } }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Experience Points
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Star sx={{ fontSize: 48, color: 'gold' }} />
                    <Box>
                      <Typography variant="h4">
                        {currentQuest.exp_reward} XP
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        For {currentQuest.subject}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Box>
            
            {currentQuest.coin_reward > 0 && (
              <Box sx={{ width: { xs: '100%', md: '50%' } }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Coins
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <EmojiEvents sx={{ fontSize: 48, color: 'gold' }} />
                      <Box>
                        <Typography variant="h4">
                          {currentQuest.coin_reward}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Spend in the shop
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            )}
            
            {currentQuest.achievement_unlocks && currentQuest.achievement_unlocks.length > 0 && (
              <Box sx={{ width: '100%' }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Unlockable Achievements
                    </Typography>
                    <List>
                      {currentQuest.achievement_unlocks.map((achievement, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <EmojiEvents color="primary" />
                          </ListItemIcon>
                          <ListItemText
                            primary={achievement.name}
                            secondary={achievement.description}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Box>
            )}
          </GridContainer>
        </TabPanel>
      </Paper>

      {/* Completion Dialog */}
      <Dialog
        open={showCompletionDialog}
        onClose={() => {
          setShowCompletionDialog(false);
          navigate('/student/quests');
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ textAlign: 'center' }}>
            <EmojiEvents sx={{ fontSize: 64, color: 'gold' }} />
            <Typography variant="h5" sx={{ mt: 2 }}>
              Quest Completed!
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body1" paragraph>
              Congratulations! You've successfully completed "{currentQuest.title}"
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mt: 3 }}>
              <Box>
                <Typography variant="h6">{currentQuest.exp_reward} XP</Typography>
                <Typography variant="body2" color="text.secondary">Earned</Typography>
              </Box>
              {currentQuest.coin_reward > 0 && (
                <Box>
                  <Typography variant="h6">{currentQuest.coin_reward} Coins</Typography>
                  <Typography variant="body2" color="text.secondary">Earned</Typography>
                </Box>
              )}
              <Box>
                <Typography variant="h6">{formatTime(timeSpent)}</Typography>
                <Typography variant="body2" color="text.secondary">Time</Typography>
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 3 }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/student/quests')}
          >
            Back to Quests
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default QuestDetailPage;
