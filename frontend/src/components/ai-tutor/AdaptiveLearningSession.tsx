import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Stack,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import {
  Timer as TimerIcon,
  Lightbulb as LightbulbIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  EmojiEvents as TrophyIcon,
  Refresh as RefreshIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { aiTutorServiceNew } from '../../services/aiTutorServiceNew';
import { useWebSocket } from '../../hooks/useWebSocket';
import PersonalizedContentViewer from './PersonalizedContentViewer';
import MultipleChoiceQuestion from '../learning/questions/MultipleChoiceQuestion';
import FillInBlankQuestion from '../learning/questions/FillInBlankQuestion';
import ShortAnswerQuestion from '../learning/questions/ShortAnswerQuestion';

interface AdaptiveLearningSessionProps {
  subject: string;
  topic: string;
  initialDifficulty?: string;
  onComplete?: (results: any) => void;
}

interface SessionMetrics {
  questionsAttempted: number;
  questionsCorrect: number;
  averageResponseTime: number;
  hintsUsed: number;
  currentStreak: number;
  maxStreak: number;
  difficultyProgression: number[];
}

const AdaptiveLearningSession: React.FC<AdaptiveLearningSessionProps> = ({
  subject,
  topic,
  initialDifficulty = 'medium',
  onComplete,
}) => {
  const { websocketService } = useWebSocket();
  
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [currentPhase, setCurrentPhase] = useState<'learning' | 'practice' | 'assessment' | 'complete'>('learning');
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [difficulty, setDifficulty] = useState(initialDifficulty);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<any>(null);
  const [showHint, setShowHint] = useState(false);
  const [hintCount, setHintCount] = useState(0);
  const [sessionTime, setSessionTime] = useState(0);
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [showFeedbackDialog, setShowFeedbackDialog] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [currentAnswer, setCurrentAnswer] = useState<string | null>(null);
  
  const [metrics, setMetrics] = useState<SessionMetrics>({
    questionsAttempted: 0,
    questionsCorrect: 0,
    averageResponseTime: 0,
    hintsUsed: 0,
    currentStreak: 0,
    maxStreak: 0,
    difficultyProgression: [],
  });

  useEffect(() => {
    startSession();
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setSessionTime(prev => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const startSession = async () => {
    try {
      setLoading(true);
      const session = await aiTutorServiceNew.startLearningSession(
        `adaptive_${subject}_${topic}_${Date.now()}`,
        'adaptive',
        subject,
        topic,
        difficulty
      );
      setSessionId(session.session_id);
    } catch (error) {
      console.error('Failed to start session:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLearningComplete = useCallback(() => {
    setCurrentPhase('practice');
    loadNextQuestion();
  }, []);

  const loadNextQuestion = async () => {
    try {
      setLoading(true);
      const question = await aiTutorServiceNew.generateAdaptiveQuestion(
        subject,
        topic,
        getDifficultyLevel(difficulty),
        [] // Previous answers would be tracked here
      );
      setCurrentQuestion(question);
      setQuestionStartTime(Date.now());
      setShowHint(false);
      setCurrentAnswer(null);
      setHintCount(0);
    } catch (error) {
      console.error('Failed to load question:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyLevel = (difficulty: string): number => {
    const levels = { beginner: 1, medium: 2, advanced: 3 };
    return levels[difficulty as keyof typeof levels] || 2;
  };

  const handleAnswerSubmit = async (answer: any) => {
    const timeSpent = Math.floor((Date.now() - questionStartTime) / 1000);
    
    try {
      const result = await aiTutorServiceNew.submitAnswer(
        currentQuestion.id,
        answer,
        timeSpent,
        sessionId || undefined
      );
      
      // Update metrics
      const newMetrics = { ...metrics };
      newMetrics.questionsAttempted++;
      
      if (result.correct) {
        newMetrics.questionsCorrect++;
        newMetrics.currentStreak++;
        newMetrics.maxStreak = Math.max(newMetrics.maxStreak, newMetrics.currentStreak);
        
        // Adjust difficulty
        if (newMetrics.currentStreak >= 3) {
          adjustDifficulty('up');
        }
      } else {
        newMetrics.currentStreak = 0;
        
        // Adjust difficulty
        if (metrics.questionsAttempted > 0 && 
            newMetrics.questionsCorrect / newMetrics.questionsAttempted < 0.5) {
          adjustDifficulty('down');
        }
      }
      
      // Calculate average response time
      const totalTime = metrics.averageResponseTime * (metrics.questionsAttempted - 1) + timeSpent;
      newMetrics.averageResponseTime = totalTime / newMetrics.questionsAttempted;
      
      setMetrics(newMetrics);
      setFeedback(result);
      setShowFeedbackDialog(true);
      
      // Send progress via WebSocket
      if (websocketService && sessionId) {
        websocketService.emit('learning_progress', {
          session_id: sessionId,
          question_index: questionIndex,
          correct: result.correct,
          time_spent: timeSpent,
          difficulty: difficulty,
          accuracy: newMetrics.questionsCorrect / newMetrics.questionsAttempted,
        });
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const adjustDifficulty = (direction: 'up' | 'down') => {
    const levels = ['beginner', 'medium', 'advanced'];
    const currentIndex = levels.indexOf(difficulty);
    
    if (direction === 'up' && currentIndex < levels.length - 1) {
      setDifficulty(levels[currentIndex + 1]);
      setSnackbarMessage('Great job! Increasing difficulty level.');
    } else if (direction === 'down' && currentIndex > 0) {
      setDifficulty(levels[currentIndex - 1]);
      setSnackbarMessage("Let's practice at an easier level.");
    }
  };

  const handleGetHint = async () => {
    if (!currentQuestion) return;
    
    const hint = await aiTutorServiceNew.getPersonalizedHint(
      currentQuestion.id,
      hintCount + 1
    );
    
    setShowHint(true);
    setHintCount(hintCount + 1);
    setMetrics(prev => ({ ...prev, hintsUsed: prev.hintsUsed + 1 }));
    
    if (sessionId) {
      aiTutorServiceNew.provideFeedback(sessionId, {
        type: 'help_request',
        question_id: currentQuestion.id,
        hint_number: hintCount + 1,
      });
    }
  };

  const handleNextQuestion = () => {
    setShowFeedbackDialog(false);
    setFeedback(null);
    setQuestionIndex(questionIndex + 1);
    
    if (questionIndex + 1 >= 10) { // Complete after 10 questions
      completeSession();
    } else {
      loadNextQuestion();
    }
  };

  const completeSession = async () => {
    setCurrentPhase('complete');
    
    if (sessionId) {
      const sessionData = {
        completion_rate: 1.0,
        engagement_score: calculateEngagementScore(),
        questions_attempted: metrics.questionsAttempted,
        questions_correct: metrics.questionsCorrect,
        average_response_time: metrics.averageResponseTime,
        hints_used: metrics.hintsUsed,
      };
      
      const result = await aiTutorServiceNew.endLearningSession(sessionId, sessionData);
      
      if (onComplete) {
        onComplete({
          ...result,
          metrics,
          duration: sessionTime,
        });
      }
    }
  };

  const calculateEngagementScore = (): number => {
    // Simple engagement calculation
    const accuracyScore = metrics.questionsCorrect / Math.max(metrics.questionsAttempted, 1);
    const hintPenalty = Math.max(0, 1 - (metrics.hintsUsed / metrics.questionsAttempted) * 0.5);
    const streakBonus = Math.min(0.2, metrics.maxStreak * 0.05);
    
    return Math.min(1, accuracyScore * hintPenalty + streakBonus);
  };

  const renderQuestion = () => {
    if (!currentQuestion) return null;
    
    const commonProps = {
      question: currentQuestion,
      answer: currentAnswer,
      onAnswerChange: setCurrentAnswer,
      disabled: !!feedback,
      showResult: !!feedback
    };
    
    switch (currentQuestion.type) {
      case 'multiple_choice':
        return <MultipleChoiceQuestion {...commonProps} />;
      case 'fill_blank':
        return <FillInBlankQuestion {...commonProps} />;
      case 'open_ended':
        return <ShortAnswerQuestion {...commonProps} />;
      default:
        return <Typography>Unsupported question type</Typography>;
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading && !sessionId) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5">
              <PsychologyIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Adaptive Learning: {topic}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip label={subject} size="small" />
              <Chip 
                label={`Difficulty: ${difficulty}`} 
                size="small" 
                color="primary" 
              />
              <Chip 
                icon={<TimerIcon />} 
                label={formatTime(sessionTime)} 
                size="small" 
                color="secondary" 
              />
            </Box>
          </Box>
          
          {/* Metrics Display */}
          <Stack direction="row" spacing={2}>
            <Tooltip title="Accuracy">
              <Chip
                icon={<CheckIcon />}
                label={`${Math.round((metrics.questionsCorrect / Math.max(metrics.questionsAttempted, 1)) * 100)}%`}
                color="success"
              />
            </Tooltip>
            <Tooltip title="Current Streak">
              <Chip
                icon={<TrendingUpIcon />}
                label={metrics.currentStreak}
                color={metrics.currentStreak > 0 ? 'warning' : 'default'}
              />
            </Tooltip>
            <Tooltip title="Questions Completed">
              <Chip
                label={`${metrics.questionsAttempted}/10`}
                variant="outlined"
              />
            </Tooltip>
          </Stack>
        </Box>
        
        <LinearProgress
          variant="determinate"
          value={(metrics.questionsAttempted / 10) * 100}
          sx={{ mt: 2 }}
        />
      </Paper>

      {/* Main Content */}
      {currentPhase === 'learning' && (
        <PersonalizedContentViewer
          subject={subject}
          topic={topic}
          difficulty={difficulty}
          onComplete={handleLearningComplete}
          sessionId={sessionId || undefined}
        />
      )}

      {currentPhase === 'practice' && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6">
              Question {questionIndex + 1} of 10
            </Typography>
            <Button
              startIcon={<LightbulbIcon />}
              onClick={handleGetHint}
              disabled={hintCount >= (currentQuestion?.hints?.length || 0)}
            >
              Get Hint ({currentQuestion?.hints?.length - hintCount} left)
            </Button>
          </Box>
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {renderQuestion()}
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => handleAnswerSubmit(currentAnswer)}
                  disabled={!currentAnswer || !!feedback}
                >
                  Submit Answer
                </Button>
              </Box>
            </>
          )}
        </Paper>
      )}

      {currentPhase === 'complete' && (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <TrophyIcon sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Session Complete!
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Great job on your adaptive learning session!
            </Typography>
            
            <Box sx={{ mt: 4, mb: 3 }}>
              <Stack direction="row" spacing={3} justifyContent="center">
                <Box>
                  <Typography variant="h3" color="primary">
                    {Math.round((metrics.questionsCorrect / metrics.questionsAttempted) * 100)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Accuracy
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="h3" color="secondary">
                    {formatTime(sessionTime)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Time Spent
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="h3" color="warning.main">
                    {metrics.maxStreak}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Best Streak
                  </Typography>
                </Box>
              </Stack>
            </Box>
            
            <Button
              variant="contained"
              size="large"
              onClick={() => window.location.reload()}
            >
              Start New Session
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Feedback Dialog */}
      <Dialog open={showFeedbackDialog} onClose={() => setShowFeedbackDialog(false)}>
        <DialogTitle>
          {feedback?.correct ? (
            <Box sx={{ display: 'flex', alignItems: 'center', color: 'success.main' }}>
              <CheckIcon sx={{ mr: 1 }} />
              Correct!
            </Box>
          ) : (
            <Box sx={{ display: 'flex', alignItems: 'center', color: 'error.main' }}>
              <CancelIcon sx={{ mr: 1 }} />
              Not Quite Right
            </Box>
          )}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            {feedback?.feedback}
          </Typography>
          {feedback?.explanation && (
            <Alert severity="info">
              <Typography variant="body2">
                {feedback.explanation}
              </Typography>
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleNextQuestion} variant="contained">
            Next Question
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={!!snackbarMessage}
        autoHideDuration={3000}
        onClose={() => setSnackbarMessage('')}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default AdaptiveLearningSession;