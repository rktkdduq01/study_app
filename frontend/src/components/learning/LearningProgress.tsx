import React from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  
  Chip,
  Avatar,
} from '@mui/material';
import {
  CheckCircle,
  Timer,
  Quiz,
  EmojiEvents,
  TrendingUp,
} from '@mui/icons-material';
import { GridContainer, FlexContainer, FlexRow } from '../layout';

interface LearningProgressProps {
  totalQuestions: number;
  currentQuestion: number;
  correctAnswers: number;
  timeSpent: number;
}

const LearningProgress: React.FC<LearningProgressProps> = ({
  totalQuestions,
  currentQuestion,
  correctAnswers,
  timeSpent,
}) => {
  const progressPercentage = totalQuestions > 0 
    ? (currentQuestion / totalQuestions) * 100 
    : 0;
  
  const accuracyPercentage = currentQuestion > 0
    ? (correctAnswers / currentQuestion) * 100
    : 0;

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 80) return 'success';
    if (accuracy >= 60) return 'warning';
    return 'error';
  };

  const getEncouragingMessage = () => {
    if (accuracyPercentage >= 90) return "Outstanding! Keep it up! 🌟";
    if (accuracyPercentage >= 70) return "Great job! You're doing well! 👏";
    if (accuracyPercentage >= 50) return "Good effort! Keep practicing! 💪";
    return "Don't give up! You can do this! 🚀";
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TrendingUp color="primary" />
        Your Progress
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Question Progress and Accuracy */}
        <GridContainer columns={{ xs: 1, md: 2 }} spacing={3}>
          {/* Question Progress */}
          <Box>
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Questions Completed
                </Typography>
                <Typography variant="body2" fontWeight="bold">
                  {currentQuestion} / {totalQuestions}
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={progressPercentage} 
                sx={{ height: 10, borderRadius: 5 }}
              />
            </Box>
          </Box>

          {/* Accuracy */}
          <Box>
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Accuracy Rate
                </Typography>
                <Typography variant="body2" fontWeight="bold">
                  {Math.round(accuracyPercentage)}%
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={accuracyPercentage} 
                color={getAccuracyColor(accuracyPercentage)}
                sx={{ height: 10, borderRadius: 5 }}
              />
            </Box>
          </Box>
        </GridContainer>

        {/* Stats Cards */}
        <GridContainer columns={{ xs: 2, md: 4 }} spacing={3}>
          <Box sx={{ textAlign: 'center' }}>
            <Avatar sx={{ bgcolor: 'success.light', mx: 'auto', mb: 1 }}>
              <CheckCircle color="success" />
            </Avatar>
            <Typography variant="h5" fontWeight="bold">
              {correctAnswers}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Correct Answers
            </Typography>
          </Box>

          <Box sx={{ textAlign: 'center' }}>
            <Avatar sx={{ bgcolor: 'primary.light', mx: 'auto', mb: 1 }}>
              <Quiz color="primary" />
            </Avatar>
            <Typography variant="h5" fontWeight="bold">
              {totalQuestions - currentQuestion}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Questions Left
            </Typography>
          </Box>

          <Box sx={{ textAlign: 'center' }}>
            <Avatar sx={{ bgcolor: 'secondary.light', mx: 'auto', mb: 1 }}>
              <Timer color="secondary" />
            </Avatar>
            <Typography variant="h5" fontWeight="bold">
              {formatTime(timeSpent)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Time Spent
            </Typography>
          </Box>

          <Box sx={{ textAlign: 'center' }}>
            <Avatar sx={{ bgcolor: 'warning.light', mx: 'auto', mb: 1 }}>
              <EmojiEvents color="warning" />
            </Avatar>
            <Typography variant="h5" fontWeight="bold">
              {Math.round(accuracyPercentage * 0.5)}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Points Earned
            </Typography>
          </Box>
        </GridContainer>

        {/* Encouraging Message */}
        <Box 
          sx={{ 
            textAlign: 'center', 
            p: 2, 
            bgcolor: 'primary.light',
            borderRadius: 2,
          }}
        >
          <Typography variant="h6" color="primary.dark">
            {getEncouragingMessage()}
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default LearningProgress;