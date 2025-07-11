import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  IconButton,
  Chip,
  Fade,
  Grow,
  Alert,
  Snackbar,
  LinearProgress,
  Tooltip,
  Zoom,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Lightbulb,
  NavigateNext,
  Timer,
  EmojiEvents,
  Star,
  Replay,
  Close,
  TipsAndUpdates,
} from '@mui/icons-material';
import { Question, QuestionType, AnswerSubmission } from '../../types/learning';
import MultipleChoiceQuestion from './questions/MultipleChoiceQuestion';
import ShortAnswerQuestion from './questions/ShortAnswerQuestion';
import TrueFalseQuestion from './questions/TrueFalseQuestion';
import FillInBlankQuestion from './questions/FillInBlankQuestion';
import MatchingQuestion from './questions/MatchingQuestion';
import OrderingQuestion from './questions/OrderingQuestion';
import CodingQuestion from './questions/CodingQuestion';
import DrawingQuestion from './questions/DrawingQuestion';

interface ProblemSolvingInterfaceProps {
  questions: Question[];
  currentIndex: number;
  onAnswerSubmit: (correct: boolean, answer: AnswerSubmission) => void;
  showHint: boolean;
  onHintClose: () => void;
  timeLimit?: number;
}

const ProblemSolvingInterface: React.FC<ProblemSolvingInterfaceProps> = ({
  questions,
  currentIndex,
  onAnswerSubmit,
  showHint,
  onHintClose,
  timeLimit,
}) => {
  const [currentAnswer, setCurrentAnswer] = useState<any>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [attempts, setAttempts] = useState(0);
  const [timeLeft, setTimeLeft] = useState(timeLimit || 0);
  const [showExplanation, setShowExplanation] = useState(false);
  const [earnedPoints, setEarnedPoints] = useState(0);
  const [showEncouragement, setShowEncouragement] = useState(false);

  const currentQuestion = questions[currentIndex];

  // Timer effect
  useEffect(() => {
    if (timeLimit && timeLeft > 0 && !showFeedback) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0 && timeLimit) {
      handleSubmit();
    }
  }, [timeLeft, timeLimit, showFeedback]);

  // Reset state when question changes
  useEffect(() => {
    setCurrentAnswer(null);
    setShowFeedback(false);
    setIsCorrect(null);
    setAttempts(0);
    setShowExplanation(false);
    setTimeLeft(currentQuestion.timeLimit || timeLimit || 0);
  }, [currentIndex, currentQuestion, timeLimit]);

  const renderQuestion = () => {
    const props = {
      question: currentQuestion,
      answer: currentAnswer,
      onAnswerChange: setCurrentAnswer,
      disabled: showFeedback,
    };

    switch (currentQuestion.type) {
      case QuestionType.MULTIPLE_CHOICE:
        return <MultipleChoiceQuestion {...props} />;
      case QuestionType.SHORT_ANSWER:
        return <ShortAnswerQuestion {...props} />;
      case QuestionType.TRUE_FALSE:
        return <TrueFalseQuestion {...props} />;
      case QuestionType.FILL_IN_BLANK:
        return <FillInBlankQuestion {...props} />;
      case QuestionType.MATCHING:
        return <MatchingQuestion {...props} />;
      case QuestionType.ORDERING:
        return <OrderingQuestion {...props} />;
      case QuestionType.CODING:
        return <CodingQuestion {...props} />;
      case QuestionType.DRAWING:
        return <DrawingQuestion {...props} />;
      default:
        return <Typography>Question type not supported</Typography>;
    }
  };

  const checkAnswer = (): boolean => {
    // This is a simplified check - in real implementation, 
    // each question type would have its own validation logic
    switch (currentQuestion.type) {
      case QuestionType.MULTIPLE_CHOICE:
      case QuestionType.TRUE_FALSE:
        return currentAnswer === currentQuestion.data.correctAnswer;
      case QuestionType.SHORT_ANSWER:
        return currentQuestion.data.acceptableAnswers?.includes(currentAnswer) || false;
      default:
        return false;
    }
  };

  const handleSubmit = () => {
    const correct = checkAnswer();
    setIsCorrect(correct);
    setShowFeedback(true);
    setAttempts(attempts + 1);

    // Calculate points based on attempts and time
    let points = currentQuestion.points;
    if (!correct) {
      points = 0;
    } else {
      // Deduct points for multiple attempts
      points = Math.max(points - (attempts * 5), 10);
      // Bonus for quick answers
      if (timeLimit && timeLeft > timeLimit * 0.7) {
        points += 5;
      }
    }
    setEarnedPoints(points);

    // Show encouragement for students
    if (!correct && attempts < 2) {
      setShowEncouragement(true);
    }

    const submission: AnswerSubmission = {
      questionId: currentQuestion.id,
      answer: currentAnswer,
      timeSpent: timeLimit ? timeLimit - timeLeft : 0,
      attempts: attempts + 1,
    };

    if (correct) {
      setTimeout(() => {
        onAnswerSubmit(true, submission);
      }, 2000);
    }
  };

  const handleTryAgain = () => {
    setShowFeedback(false);
    setIsCorrect(null);
    setShowEncouragement(false);
  };

  const handleShowExplanation = () => {
    setShowExplanation(true);
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      {/* Question Header */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">
              Question {currentIndex + 1} of {questions.length}
            </Typography>
            <Chip
              size="small"
              label={currentQuestion.difficulty}
              color={currentQuestion.difficulty === 'beginner' ? 'success' : 'warning'}
            />
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {timeLimit && (
              <Chip
                icon={<Timer />}
                label={`${Math.floor(timeLeft / 60)}:${(timeLeft % 60).toString().padStart(2, '0')}`}
                color={timeLeft < 30 ? 'error' : 'default'}
              />
            )}
            <Chip
              icon={<Star />}
              label={`${currentQuestion.points} pts`}
              color="primary"
            />
          </Box>
        </Box>
        
        <LinearProgress
          variant="determinate"
          value={((currentIndex + 1) / questions.length) * 100}
          sx={{ mb: 2 }}
        />
      </Paper>

      {/* Question Content */}
      <Fade in key={currentQuestion.id}>
        <Paper sx={{ p: 4, mb: 3, position: 'relative' }}>
          {/* Topic Badge */}
          <Chip
            label={currentQuestion.topic}
            size="small"
            sx={{ position: 'absolute', top: 16, right: 16 }}
          />
          
          {renderQuestion()}
          
          {/* Action Buttons */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 4 }}>
            <Box>
              {currentQuestion.hint && !showFeedback && (
                <Tooltip title="Using hints will reduce your points">
                  <Button
                    startIcon={<Lightbulb />}
                    onClick={() => {/* Show hint logic */}}
                    size="small"
                  >
                    Get Hint (-5 pts)
                  </Button>
                </Tooltip>
              )}
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              {!showFeedback ? (
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleSubmit}
                  disabled={!currentAnswer}
                  endIcon={<NavigateNext />}
                >
                  Submit Answer
                </Button>
              ) : (
                <>
                  {!isCorrect && attempts < 3 && (
                    <Button
                      variant="outlined"
                      onClick={handleTryAgain}
                      startIcon={<Replay />}
                    >
                      Try Again
                    </Button>
                  )}
                  {currentQuestion.explanation && (
                    <Button
                      variant="outlined"
                      onClick={handleShowExplanation}
                      startIcon={<TipsAndUpdates />}
                    >
                      Show Explanation
                    </Button>
                  )}
                </>
              )}
            </Box>
          </Box>
        </Paper>
      </Fade>

      {/* Feedback */}
      {showFeedback && (
        <Grow in={showFeedback}>
          <Paper
            sx={{
              p: 3,
              bgcolor: isCorrect ? 'success.light' : 'error.light',
              color: isCorrect ? 'success.contrastText' : 'error.contrastText',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {isCorrect ? (
                <>
                  <CheckCircle sx={{ fontSize: 40 }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6">Excellent! 🎉</Typography>
                    <Typography variant="body2">
                      You earned {earnedPoints} points!
                    </Typography>
                  </Box>
                </>
              ) : (
                <>
                  <Cancel sx={{ fontSize: 40 }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h6">Not quite right</Typography>
                    <Typography variant="body2">
                      {attempts < 3 ? "Don't give up! You can try again." : "Let's review the explanation."}
                    </Typography>
                  </Box>
                </>
              )}
            </Box>
          </Paper>
        </Grow>
      )}

      {/* Explanation */}
      {showExplanation && currentQuestion.explanation && (
        <Fade in={showExplanation}>
          <Alert
            severity="info"
            sx={{ mt: 2 }}
            action={
              <IconButton size="small" onClick={() => setShowExplanation(false)}>
                <Close />
              </IconButton>
            }
          >
            <Typography variant="subtitle2" gutterBottom>
              Explanation:
            </Typography>
            <Typography variant="body2">
              {currentQuestion.explanation}
            </Typography>
          </Alert>
        </Fade>
      )}

      {/* Hint Display */}
      <Snackbar
        open={showHint}
        onClose={onHintClose}
        message={currentQuestion.hint}
        action={
          <IconButton size="small" color="inherit" onClick={onHintClose}>
            <Close />
          </IconButton>
        }
      />

      {/* Encouragement Message */}
      <Snackbar
        open={showEncouragement}
        autoHideDuration={3000}
        onClose={() => setShowEncouragement(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="info" onClose={() => setShowEncouragement(false)}>
          <Typography variant="body2">
            Keep trying! Every mistake is a chance to learn! 💪
          </Typography>
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ProblemSolvingInterface;