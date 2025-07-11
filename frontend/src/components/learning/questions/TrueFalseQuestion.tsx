import React from 'react';
import {
  Box,
  Typography,
  Button,
  ButtonGroup,
  Paper,
  Zoom,
  styled,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  ThumbUp,
  ThumbDown,
} from '@mui/icons-material';
import { Question } from '../../../types/learning';

interface TrueFalseQuestionProps {
  question: Question;
  answer: string | null;
  onAnswerChange: (answer: string) => void;
  disabled?: boolean;
  showResult?: boolean;
}

const StyledButton = styled(Button)(({ theme }) => ({
  padding: theme.spacing(3, 6),
  fontSize: '1.2rem',
  fontWeight: 600,
  borderRadius: theme.spacing(2),
  textTransform: 'none',
  transition: 'all 0.3s ease',
  minWidth: 150,
  '&:hover': {
    transform: 'scale(1.05)',
  },
  '&.selected': {
    transform: 'scale(1.05)',
    boxShadow: theme.shadows[8],
  },
}));

const TrueFalseQuestion: React.FC<TrueFalseQuestionProps> = ({
  question,
  answer,
  onAnswerChange,
  disabled = false,
  showResult = false,
}) => {
  const { correctAnswer } = question.data;

  const getButtonVariant = (value: string) => {
    if (!answer) return 'outlined';
    return answer === value ? 'contained' : 'outlined';
  };

  const getButtonColor = (value: string) => {
    if (!showResult) {
      return answer === value ? 'primary' : 'inherit';
    }
    
    if (value === correctAnswer) return 'success';
    if (answer === value && value !== correctAnswer) return 'error';
    return 'inherit';
  };

  const getIcon = (value: string) => {
    if (showResult && value === correctAnswer) {
      return <CheckCircle />;
    }
    if (showResult && answer === value && value !== correctAnswer) {
      return <Cancel />;
    }
    return value === 'true' ? <ThumbUp /> : <ThumbDown />;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ mb: 4, fontWeight: 500 }}>
        {question.question}
      </Typography>
      
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 3 }}>
          <Typography variant="body1" sx={{ mb: 4, textAlign: 'center', fontSize: '1.1rem' }}>
            Is this statement true or false?
          </Typography>
          
          <ButtonGroup
            size="large"
            sx={{
              display: 'flex',
              gap: 3,
              '& .MuiButton-root': {
                flex: 1,
              },
            }}
          >
            <Zoom in style={{ transitionDelay: '100ms' }}>
              <StyledButton
                className={answer === 'true' ? 'selected' : ''}
                variant={getButtonVariant('true')}
                color={getButtonColor('true')}
                onClick={() => onAnswerChange('true')}
                disabled={disabled}
                startIcon={getIcon('true')}
                sx={{
                  bgcolor: answer === 'true' && !showResult ? 'primary.light' : undefined,
                }}
              >
                TRUE
              </StyledButton>
            </Zoom>
            
            <Zoom in style={{ transitionDelay: '200ms' }}>
              <StyledButton
                className={answer === 'false' ? 'selected' : ''}
                variant={getButtonVariant('false')}
                color={getButtonColor('false')}
                onClick={() => onAnswerChange('false')}
                disabled={disabled}
                startIcon={getIcon('false')}
                sx={{
                  bgcolor: answer === 'false' && !showResult ? 'primary.light' : undefined,
                }}
              >
                FALSE
              </StyledButton>
            </Zoom>
          </ButtonGroup>
          
          {/* Visual feedback */}
          {showResult && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              {answer === correctAnswer ? (
                <Typography variant="h6" color="success.main">
                  Correct! 🎉
                </Typography>
              ) : (
                <Typography variant="h6" color="error.main">
                  The correct answer is {correctAnswer && typeof correctAnswer === 'string' ? correctAnswer.toUpperCase() : ''}
                </Typography>
              )}
            </Box>
          )}
        </Paper>
      </Box>
      
      {/* Encouraging message for students */}
      {answer && !disabled && !showResult && (
        <Zoom in>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="body2" color="primary">
              You selected {answer.toUpperCase()}. Click submit to check your answer!
            </Typography>
          </Box>
        </Zoom>
      )}
    </Box>
  );
};

export default TrueFalseQuestion;