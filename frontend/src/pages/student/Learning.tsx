import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  LinearProgress,
  Chip,
  Alert,
  Tooltip,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Fab,
  Badge,
  Snackbar,
} from '@mui/material';
import {
  ArrowBack,
  Bookmark,
  BookmarkBorder,
  Notes,
  Help,
  Fullscreen,
  FullscreenExit,
  EmojiEvents,
  Timer,
  CheckCircle,
  Close,
  Lightbulb,
  MenuBook,
  Quiz,
  Code,
  Draw,
  VideoLibrary,
} from '@mui/icons-material';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { useWebSocket } from '../../hooks/useWebSocket';
import { ContentType, LearningContent, Question } from '../../types/learning';
import LearningContentViewer from '../../components/learning/LearningContentViewer';
import ProblemSolvingInterface from '../../components/learning/ProblemSolvingInterface';
import LearningProgress from '../../components/learning/LearningProgress';
import NotesPanel from '../../components/learning/NotesPanel';
import Loading from '../../components/common/Loading';
import ErrorAlert from '../../components/common/ErrorAlert';

const LearningPage: React.FC = () => {
  const { contentId } = useParams<{ contentId: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  
  // State
  const [learningContent, setLearningContent] = useState<LearningContent | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showProblemSolving, setShowProblemSolving] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showNotes, setShowNotes] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [progress, setProgress] = useState(0);

  const { character } = useAppSelector((state) => state.character);
  const { user } = useAppSelector((state) => state.auth);
  const { websocketService } = useWebSocket();
  const progressUpdateInterval = useRef<NodeJS.Timeout>();

  // Mock data - replace with API call
  useEffect(() => {
    if (contentId) {
      // Simulate API call
      setTimeout(() => {
        setLearningContent({
          id: contentId,
          title: 'Introduction to Fractions',
          description: 'Learn the basics of fractions with fun visualizations',
          type: ContentType.INTERACTIVE,
          subject: 'math',
          grade: 5,
          difficulty: 'beginner' as any,
          estimatedTime: 20,
          objectives: [
            'Understand what fractions represent',
            'Learn to identify numerator and denominator',
            'Compare simple fractions',
            'Add and subtract fractions with same denominators'
          ],
          content: {
            text: 'Fractions represent parts of a whole...',
            interactiveUrl: '/interactive/fractions-basics',
          },
          relatedQuestions: [
            {
              id: '1',
              type: 'multiple_choice' as any,
              question: 'What is the numerator in the fraction 3/4?',
              points: 10,
              difficulty: 'beginner' as any,
              subject: 'math',
              topic: 'fractions',
              data: {
                options: ['3', '4', '7', '12'],
                correctAnswer: '3'
              },
              explanation: 'The numerator is the top number in a fraction.',
              hint: 'Look at the number above the line.'
            },
            // Add more questions...
          ],
          metadata: {
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            tags: ['fractions', 'math', 'beginner'],
            difficulty: 'beginner' as any,
            likes: 245,
            views: 1823
          }
        });
        setIsLoading(false);
      }, 1000);
    }
  }, [contentId]);

  // Timer
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeSpent((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Progress calculation and WebSocket updates
  useEffect(() => {
    if (learningContent && learningContent.relatedQuestions) {
      const questionsProgress = (currentQuestionIndex / learningContent.relatedQuestions.length) * 50;
      const contentProgress = showProblemSolving ? 50 : 25;
      setProgress(contentProgress + questionsProgress);

      // Send progress update via WebSocket
      if (user && websocketService) {
        websocketService.updateLearningProgress({
          content_id: learningContent.id,
          content_title: learningContent.title,
          progress: contentProgress + questionsProgress,
          time_spent: timeSpent,
          questions_attempted: currentQuestionIndex,
          total_questions: learningContent.relatedQuestions.length,
        });
      }
    }
  }, [currentQuestionIndex, showProblemSolving, learningContent, timeSpent, user, websocketService]);

  // Send periodic progress updates
  useEffect(() => {
    if (user && websocketService && learningContent) {
      progressUpdateInterval.current = setInterval(() => {
        websocketService.updateLearningProgress({
          content_id: learningContent.id,
          content_title: learningContent.title,
          progress: progress,
          time_spent: timeSpent,
          questions_attempted: currentQuestionIndex,
          total_questions: learningContent.relatedQuestions?.length || 0,
        });
      }, 30000); // Update every 30 seconds

      return () => {
        if (progressUpdateInterval.current) {
          clearInterval(progressUpdateInterval.current);
        }
      };
    }
  }, [user, websocketService, learningContent, progress, timeSpent, currentQuestionIndex]);

  const handleToggleFullscreen = () => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
    setIsFullscreen(!isFullscreen);
  };

  const handleBookmark = () => {
    setBookmarked(!bookmarked);
    setSnackbarMessage(bookmarked ? 'Bookmark removed' : 'Bookmark added');
  };

  const handleShowHint = () => {
    setShowHint(true);
    // Deduct points for using hint
    setSnackbarMessage('Hint used: -5 points');
  };

  const handleQuestionComplete = (correct: boolean) => {
    if (correct) {
      setSnackbarMessage('Correct! +10 XP');
      if (learningContent?.relatedQuestions && currentQuestionIndex < learningContent.relatedQuestions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        // All questions completed
        handleContentComplete();
      }
    } else {
      setSnackbarMessage('Try again! You can do it!');
    }
  };

  const handleContentComplete = () => {
    setSnackbarMessage('Content completed! +50 XP earned!');
    
    // Send completion via WebSocket
    if (user && websocketService && learningContent) {
      websocketService.updateLearningProgress({
        content_id: learningContent.id,
        content_title: learningContent.title,
        progress: 100,
        time_spent: timeSpent,
        questions_attempted: learningContent.relatedQuestions?.length || 0,
        total_questions: learningContent.relatedQuestions?.length || 0,
        completed: true,
      });
    }
    
    // Navigate to completion screen or next content
    setTimeout(() => {
      navigate('/student/quests');
    }, 2000);
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return <Loading message="Loading learning content..." />;
  }

  if (error) {
    return <ErrorAlert message={error} onRetry={() => window.location.reload()} />;
  }

  if (!learningContent) {
    return <Alert severity="error">Content not found</Alert>;
  }

  const speedDialActions = [
    { icon: <Notes />, name: 'Notes', action: () => setShowNotes(!showNotes) },
    { icon: <Help />, name: 'Hint', action: handleShowHint },
    { icon: bookmarked ? <Bookmark /> : <BookmarkBorder />, name: 'Bookmark', action: handleBookmark },
    { icon: isFullscreen ? <FullscreenExit /> : <Fullscreen />, name: 'Fullscreen', action: handleToggleFullscreen },
  ];

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <IconButton onClick={() => navigate(-1)}>
              <ArrowBack />
            </IconButton>
            <Box>
              <Typography variant="h5">{learningContent.title}</Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                <Chip size="small" label={learningContent.subject} />
                <Chip size="small" label={`Grade ${learningContent.grade}`} />
                <Chip size="small" label={learningContent.difficulty} color="primary" />
              </Box>
            </Box>
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              icon={<Timer />}
              label={formatTime(timeSpent)}
              color="secondary"
            />
            <Chip
              icon={<EmojiEvents />}
              label={`${character?.total_experience || 0} XP`}
              color="warning"
            />
            <Tooltip title="Complete to earn rewards!">
              <Chip
                icon={<CheckCircle />}
                label={`${Math.round(progress)}%`}
                color={progress === 100 ? 'success' : 'default'}
              />
            </Tooltip>
          </Box>
        </Box>
        
        <LinearProgress 
          variant="determinate" 
          value={progress} 
          sx={{ mt: 2, height: 8, borderRadius: 4 }}
          color={progress === 100 ? 'success' : 'primary'}
        />
      </Paper>

      {/* Learning Objectives */}
      <Paper sx={{ p: 2, mb: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Lightbulb /> What you'll learn
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {learningContent.objectives.map((objective, index) => (
            <Chip
              key={index}
              label={objective}
              size="small"
              sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'inherit' }}
            />
          ))}
        </Box>
      </Paper>

      {/* Main Content Area */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        {/* Content Viewer */}
        <Box sx={{ flex: 1 }}>
          <Paper sx={{ p: 3, minHeight: '60vh' }}>
            {!showProblemSolving ? (
              <LearningContentViewer
                content={learningContent}
                onComplete={() => setShowProblemSolving(true)}
              />
            ) : (
              <ProblemSolvingInterface
                questions={learningContent.relatedQuestions || []}
                currentIndex={currentQuestionIndex}
                onAnswerSubmit={handleQuestionComplete}
                showHint={showHint}
                onHintClose={() => setShowHint(false)}
              />
            )}
          </Paper>
        </Box>

        {/* Side Panel */}
        {showNotes && (
          <Box sx={{ width: 300 }}>
            <NotesPanel
              contentId={learningContent.id}
              onClose={() => setShowNotes(false)}
            />
          </Box>
        )}
      </Box>

      {/* Progress Tracker */}
      <Box sx={{ mt: 2 }}>
        <LearningProgress
          totalQuestions={learningContent.relatedQuestions?.length || 0}
          currentQuestion={currentQuestionIndex + 1}
          correctAnswers={0} // Track this in state
          timeSpent={timeSpent}
        />
      </Box>

      {/* Speed Dial for Actions */}
      <SpeedDial
        ariaLabel="Learning actions"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        icon={<SpeedDialIcon />}
      >
        {speedDialActions.map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={action.icon}
            tooltipTitle={action.name}
            onClick={action.action}
          />
        ))}
      </SpeedDial>

      {/* Snackbar for notifications */}
      <Snackbar
        open={!!snackbarMessage}
        autoHideDuration={3000}
        onClose={() => setSnackbarMessage('')}
        message={snackbarMessage}
        action={
          <IconButton size="small" color="inherit" onClick={() => setSnackbarMessage('')}>
            <Close />
          </IconButton>
        }
      />
    </Container>
  );
};

export default LearningPage;