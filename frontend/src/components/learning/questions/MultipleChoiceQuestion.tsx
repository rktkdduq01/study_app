import React from 'react';
import {
  Box,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
  Paper,
  Fade,
  styled,
} from '@mui/material';
import { Question } from '../../../types/learning';
import { CheckCircle, RadioButtonUnchecked } from '@mui/icons-material';

interface MultipleChoiceQuestionProps {
  question: Question;
  answer: string | null;
  onAnswerChange: (answer: string) => void;
  disabled?: boolean;
  showResult?: boolean;
}

const StyledFormControlLabel = styled(FormControlLabel)(({ theme }) => ({
  width: '100%',
  margin: theme.spacing(1, 0),
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  border: `2px solid ${theme.palette.divider}`,
  transition: 'all 0.3s ease',
  '&:hover': {
    borderColor: theme.palette.primary.main,
    transform: 'translateX(4px)',
    boxShadow: theme.shadows[2],
  },
  '&.selected': {
    borderColor: theme.palette.primary.main,
    backgroundColor: theme.palette.primary.light,
  },
  '&.correct': {
    borderColor: theme.palette.success.main,
    backgroundColor: theme.palette.success.light,
  },
  '&.incorrect': {
    borderColor: theme.palette.error.main,
    backgroundColor: theme.palette.error.light,
  },
}));

const OptionLabel = styled('span')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  width: '100%',
  fontSize: '1.1rem',
  color: theme.palette.text.primary,
}));

const MultipleChoiceQuestion: React.FC<MultipleChoiceQuestionProps> = ({
  question,
  answer,
  onAnswerChange,
  disabled = false,
  showResult = false,
}) => {
  const { options = [], correctAnswer } = question.data;

  const getOptionClass = (option: string) => {
    if (!showResult && answer === option) return 'selected';
    if (showResult) {
      if (option === correctAnswer) return 'correct';
      if (answer === option && option !== correctAnswer) return 'incorrect';
    }
    return '';
  };

  const getIcon = (option: string) => {
    if (!showResult) {
      return answer === option ? (
        <Radio color="primary" />
      ) : (
        <Radio />
      );
    }
    
    if (option === correctAnswer) {
      return <CheckCircle color="success" />;
    }
    if (answer === option && option !== correctAnswer) {
      return <Radio color="error" />;
    }
    return <RadioButtonUnchecked />;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ mb: 3, fontWeight: 500 }}>
        {question.question}
      </Typography>
      
      <RadioGroup
        value={answer || ''}
        onChange={(e) => onAnswerChange(e.target.value)}
      >
        {options.map((option: string, index: number) => (
          <Fade in key={index} style={{ transitionDelay: `${index * 100}ms` }}>
            <StyledFormControlLabel
              className={getOptionClass(option)}
              value={option}
              disabled={disabled}
              control={getIcon(option)}
              label={
                <OptionLabel>
                  <Typography variant="body1" sx={{ flex: 1 }}>
                    {option}
                  </Typography>
                  {showResult && option === correctAnswer && (
                    <Typography variant="caption" color="success.main" sx={{ ml: 2 }}>
                      Correct Answer
                    </Typography>
                  )}
                </OptionLabel>
              }
            />
          </Fade>
        ))}
      </RadioGroup>
      
      {/* Visual feedback for young students */}
      {answer && !disabled && !showResult && (
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Typography variant="body2" color="primary">
            Great choice! Click submit when you're ready.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default MultipleChoiceQuestion;