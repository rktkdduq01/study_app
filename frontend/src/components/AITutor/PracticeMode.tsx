import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  TextField,
  Chip,
  LinearProgress,
  Alert,
  IconButton,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  Tooltip
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Lightbulb as HintIcon,
  Timer as TimerIcon,
  TrendingUp as DifficultyIcon,
  Help as HelpIcon,
  NavigateNext as NextIcon,
  NavigateBefore as PrevIcon,
  Flag as FlagIcon,
  Psychology as AIIcon
} from '@mui/icons-material';
import { aiTutorService, PracticeQuestion, Hint, AIFeedback } from '../../services/aiTutor';

interface PracticeModeProps {
  subject: string;
  topic: string;
  initialDifficulty?: number;
  onComplete?: (score: number) => void;
}

export const PracticeMode: React.FC<PracticeModeProps> = ({
  subject,
  topic,
  initialDifficulty = 5,
  onComplete
}) => {
  const [questions, setQuestions] = useState<PracticeQuestion[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<Record<string, string>>({});
  const [showExplanations, setShowExplanations] = useState<Record<string, boolean>>({});
  const [hints, setHints] = useState<Record<string, Hint>>({});
  const [hintLevels, setHintLevels] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timer, setTimer] = useState(0);
  const [isTimerRunning, setIsTimerRunning] = useState(true);
  const [showFeedback, setShowFeedback] = useState(false);
  const [aiFeedback, setAiFeedback] = useState<AIFeedback | null>(null);
  const [flaggedQuestions, setFlaggedQuestions] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadQuestions();
  }, [subject, topic]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isTimerRunning) {
      interval = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning]);

  const loadQuestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const generatedQuestions = await aiTutorService.generatePracticeQuestions({
        subject,
        topic,
        count: 10
      });
      setQuestions(generatedQuestions);
    } catch (err) {
      setError('Failed to load practice questions. Please try again.');
      console.error('Questions loading error:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentQuestion = questions[currentQuestionIndex];

  const handleAnswerSelect = (answer: string) => {
    if (!currentQuestion) return;
    setUserAnswers(prev => ({ ...prev, [currentQuestion.id]: answer }));
  };

  const handleGetHint = async () => {
    if (!currentQuestion) return;
    
    const currentLevel = hintLevels[currentQuestion.id] || 0;
    const nextLevel = currentLevel + 1;
    
    try {
      const hint = await aiTutorService.getHint({
        question: currentQuestion.question,
        userAttempts: userAnswers[currentQuestion.id] ? [userAnswers[currentQuestion.id]] : [],
        hintLevel: nextLevel
      });
      
      setHints(prev => ({ ...prev, [currentQuestion.id]: hint }));
      setHintLevels(prev => ({ ...prev, [currentQuestion.id]: nextLevel }));
    } catch (err) {
      console.error('Failed to get hint:', err);
    }
  };

  const handleCheckAnswer = async () => {
    if (!currentQuestion || !userAnswers[currentQuestion.id]) return;
    
    setShowExplanations(prev => ({ ...prev, [currentQuestion.id]: true }));
    
    // Get AI feedback
    try {
      const feedback = await aiTutorService.provideFeedback({
        question: currentQuestion.question,
        userAnswer: userAnswers[currentQuestion.id],
        correctAnswer: currentQuestion.correctAnswer,
        subject
      });
      setAiFeedback(feedback);
      setShowFeedback(true);
    } catch (err) {
      console.error('Failed to get AI feedback:', err);
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setShowFeedback(false);
      setAiFeedback(null);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      setShowFeedback(false);
      setAiFeedback(null);
    }
  };

  const handleComplete = () => {
    setIsTimerRunning(false);
    const score = calculateScore();
    if (onComplete) {
      onComplete(score);
    }
  };

  const toggleFlagQuestion = () => {
    if (!currentQuestion) return;
    setFlaggedQuestions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(currentQuestion.id)) {
        newSet.delete(currentQuestion.id);
      } else {
        newSet.add(currentQuestion.id);
      }
      return newSet;
    });
  };

  const calculateScore = () => {
    let correct = 0;
    questions.forEach(q => {
      if (userAnswers[q.id] === q.correctAnswer) {
        correct++;
      }
    });
    return (correct / questions.length) * 100;
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getQuestionStatus = (question: PracticeQuestion) => {
    if (!userAnswers[question.id]) return 'unanswered';
    if (!showExplanations[question.id]) return 'answered';
    return userAnswers[question.id] === question.correctAnswer ? 'correct' : 'incorrect';
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>Loading practice questions...</Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (error || !currentQuestion) {
    return (
      <Alert severity="error" action={
        <Button color="inherit" size="small" onClick={loadQuestions}>
          Retry
        </Button>
      }>
        {error || 'No questions available'}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h5">Practice: {topic}</Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <Chip label={subject} size="small" />
                <Chip 
                  icon={<DifficultyIcon />} 
                  label={`Difficulty: ${currentQuestion.difficulty}/10`} 
                  size="small" 
                  color="secondary"
                />
                <Chip 
                  icon={<TimerIcon />} 
                  label={formatTime(timer)} 
                  size="small" 
                  color={isTimerRunning ? "primary" : "default"}
                />
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Flag for review">
                <IconButton 
                  onClick={toggleFlagQuestion}
                  color={flaggedQuestions.has(currentQuestion.id) ? "error" : "default"}
                >
                  <FlagIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Progress */}
      <Box sx={{ mb: 3 }}>
        <Stepper activeStep={currentQuestionIndex} alternativeLabel>
          {questions.map((q, index) => {
            const status = getQuestionStatus(q);
            return (
              <Step key={q.id} completed={status === 'correct' || status === 'incorrect'}>
                <StepLabel
                  error={status === 'incorrect'}
                  StepIconComponent={() => (
                    <Box
                      sx={{
                        width: 30,
                        height: 30,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        bgcolor: 
                          status === 'correct' ? 'success.main' :
                          status === 'incorrect' ? 'error.main' :
                          status === 'answered' ? 'warning.main' :
                          'grey.300',
                        color: status === 'unanswered' ? 'text.secondary' : 'white',
                        cursor: 'pointer',
                        position: 'relative'
                      }}
                      onClick={() => {
                        setCurrentQuestionIndex(index);
                        setShowFeedback(false);
                        setAiFeedback(null);
                      }}
                    >
                      {index + 1}
                      {flaggedQuestions.has(q.id) && (
                        <FlagIcon 
                          sx={{ 
                            position: 'absolute', 
                            top: -5, 
                            right: -5, 
                            fontSize: 16,
                            color: 'error.main'
                          }} 
                        />
                      )}
                    </Box>
                  )}
                />
              </Step>
            );
          })}
        </Stepper>
      </Box>

      {/* Question */}
      <Card>
        <CardContent>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Question {currentQuestionIndex + 1} of {questions.length}
            </Typography>
            <Typography variant="body1" paragraph>
              {currentQuestion.question}
            </Typography>
            {currentQuestion.topicTags.length > 0 && (
              <Box sx={{ display: 'flex', gap: 0.5, mb: 2 }}>
                {currentQuestion.topicTags.map((tag, index) => (
                  <Chip key={index} label={tag} size="small" variant="outlined" />
                ))}
              </Box>
            )}
          </Box>

          {/* Answer Options */}
          {currentQuestion.type === 'multiple_choice' && currentQuestion.options && (
            <FormControl component="fieldset" fullWidth>
              <RadioGroup
                value={userAnswers[currentQuestion.id] || ''}
                onChange={(e) => handleAnswerSelect(e.target.value)}
              >
                {currentQuestion.options.map((option, index) => (
                  <FormControlLabel
                    key={index}
                    value={option}
                    control={<Radio />}
                    label={option}
                    disabled={showExplanations[currentQuestion.id]}
                    sx={{
                      mb: 1,
                      p: 1,
                      border: 1,
                      borderColor: 'divider',
                      borderRadius: 1,
                      bgcolor: 
                        showExplanations[currentQuestion.id] && option === currentQuestion.correctAnswer
                          ? 'success.light'
                          : showExplanations[currentQuestion.id] && option === userAnswers[currentQuestion.id] && option !== currentQuestion.correctAnswer
                          ? 'error.light'
                          : 'background.paper'
                    }}
                  />
                ))}
              </RadioGroup>
            </FormControl>
          )}

          {currentQuestion.type === 'short_answer' && (
            <TextField
              fullWidth
              multiline
              rows={3}
              value={userAnswers[currentQuestion.id] || ''}
              onChange={(e) => handleAnswerSelect(e.target.value)}
              disabled={showExplanations[currentQuestion.id]}
              placeholder="Type your answer here..."
              sx={{ mb: 2 }}
            />
          )}

          {/* Hint */}
          {hints[currentQuestion.id] && (
            <Alert severity="info" sx={{ mb: 2 }} icon={<HintIcon />}>
              <Typography variant="body2">
                <strong>Hint Level {hints[currentQuestion.id].level}:</strong> {hints[currentQuestion.id].hint}
              </Typography>
              {hints[currentQuestion.id].guidance && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {hints[currentQuestion.id].guidance}
                </Typography>
              )}
            </Alert>
          )}

          {/* Explanation */}
          <Collapse in={showExplanations[currentQuestion.id]}>
            <Alert 
              severity={userAnswers[currentQuestion.id] === currentQuestion.correctAnswer ? 'success' : 'error'}
              sx={{ mb: 2 }}
            >
              <Typography variant="body2">
                {userAnswers[currentQuestion.id] === currentQuestion.correctAnswer ? 'Correct!' : 'Incorrect.'}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                <strong>Correct Answer:</strong> {currentQuestion.correctAnswer}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                <strong>Explanation:</strong> {currentQuestion.explanation}
              </Typography>
            </Alert>
          </Collapse>

          {/* AI Feedback */}
          <Dialog open={showFeedback} onClose={() => setShowFeedback(false)} maxWidth="sm" fullWidth>
            <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AIIcon />
              AI Tutor Feedback
            </DialogTitle>
            <DialogContent>
              {aiFeedback && (
                <Box>
                  <Alert severity={aiFeedback.isCorrect ? 'success' : 'info'} sx={{ mb: 2 }}>
                    {aiFeedback.feedback}
                  </Alert>
                  
                  {aiFeedback.strengths.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>Strengths:</Typography>
                      <List dense>
                        {aiFeedback.strengths.map((strength, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <CheckIcon color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={strength} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                  
                  {aiFeedback.improvements.length > 0 && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>Areas for Improvement:</Typography>
                      <List dense>
                        {aiFeedback.improvements.map((improvement, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <DifficultyIcon color="warning" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={improvement} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setShowFeedback(false)}>Close</Button>
            </DialogActions>
          </Dialog>

          {/* Actions */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                startIcon={<PrevIcon />}
                onClick={handlePrevious}
                disabled={currentQuestionIndex === 0}
              >
                Previous
              </Button>
              <Button
                endIcon={<NextIcon />}
                onClick={handleNext}
                disabled={currentQuestionIndex === questions.length - 1}
              >
                Next
              </Button>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 1 }}>
              {!showExplanations[currentQuestion.id] && (
                <>
                  <Button
                    variant="outlined"
                    startIcon={<HintIcon />}
                    onClick={handleGetHint}
                    disabled={!hints[currentQuestion.id] || !hints[currentQuestion.id].nextLevelAvailable}
                  >
                    Get Hint
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleCheckAnswer}
                    disabled={!userAnswers[currentQuestion.id]}
                  >
                    Check Answer
                  </Button>
                </>
              )}
              
              {currentQuestionIndex === questions.length - 1 && 
               Object.keys(showExplanations).length === questions.length && (
                <Button
                  variant="contained"
                  color="success"
                  onClick={handleComplete}
                >
                  Complete Practice
                </Button>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Summary for flagged questions */}
      {flaggedQuestions.size > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Flagged for Review ({flaggedQuestions.size})
            </Typography>
            <List dense>
              {Array.from(flaggedQuestions).map(qId => {
                const q = questions.find(question => question.id === qId);
                if (!q) return null;
                const qIndex = questions.findIndex(question => question.id === qId);
                return (
                  <ListItem 
                    key={qId}
                    onClick={() => {
                      setCurrentQuestionIndex(qIndex);
                      setShowFeedback(false);
                      setAiFeedback(null);
                    }}
                    sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                  >
                    <ListItemText 
                      primary={`Question ${qIndex + 1}`}
                      secondary={q.question.substring(0, 50) + '...'}
                    />
                  </ListItem>
                );
              })}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};