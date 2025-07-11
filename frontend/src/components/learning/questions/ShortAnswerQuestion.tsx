import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  Chip,
  Paper,
  Fade,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Edit,
  Keyboard,
  Spellcheck,
} from '@mui/icons-material';
import { Question } from '../../../types/learning';

interface ShortAnswerQuestionProps {
  question: Question;
  answer: string | null;
  onAnswerChange: (answer: string) => void;
  disabled?: boolean;
  showResult?: boolean;
}

const ShortAnswerQuestion: React.FC<ShortAnswerQuestionProps> = ({
  question,
  answer,
  onAnswerChange,
  disabled = false,
  showResult = false,
}) => {
  const [focused, setFocused] = useState(false);
  const { acceptableAnswers = [], caseSensitive = false } = question.data;
  
  const isCorrect = () => {
    if (!answer) return false;
    const userAnswer = caseSensitive ? answer : answer.toLowerCase();
    return acceptableAnswers.some((acceptable: string) => {
      const acceptableAnswer = caseSensitive ? acceptable : acceptable.toLowerCase();
      return userAnswer.trim() === acceptableAnswer.trim();
    });
  };

  const getHelperText = () => {
    if (!showResult) {
      if (answer && answer.length > 0) {
        return `${answer.length} characters`;
      }
      return 'Type your answer above';
    }
    
    if (isCorrect()) {
      return 'Correct! Well done! 🎉';
    }
    
    return `Possible answers: ${acceptableAnswers.join(', ')}`;
  };

  const getFieldColor = () => {
    if (!showResult) return 'primary';
    return isCorrect() ? 'success' : 'error';
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ mb: 3, fontWeight: 500 }}>
        {question.question}
      </Typography>
      
      <Fade in>
        <Paper
          elevation={focused ? 8 : 2}
          sx={{
            p: 2,
            transition: 'all 0.3s ease',
            border: showResult
              ? isCorrect()
                ? '2px solid'
                : '2px solid'
              : '2px solid transparent',
            borderColor: showResult
              ? isCorrect()
                ? 'success.main'
                : 'error.main'
              : 'transparent',
          }}
        >
          <TextField
            fullWidth
            multiline
            rows={3}
            value={answer || ''}
            onChange={(e) => onAnswerChange(e.target.value)}
            disabled={disabled}
            placeholder="Type your answer here..."
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            color={getFieldColor()}
            helperText={getHelperText()}
            InputProps={{
              sx: {
                fontSize: '1.1rem',
                '& .MuiInputBase-input': {
                  lineHeight: 1.6,
                },
              },
              startAdornment: (
                <InputAdornment position="start">
                  <Edit color={focused ? 'primary' : 'action'} />
                </InputAdornment>
              ),
              endAdornment: showResult && (
                <InputAdornment position="end">
                  {isCorrect() ? (
                    <CheckCircle color="success" />
                  ) : (
                    <Cancel color="error" />
                  )}
                </InputAdornment>
              ),
            }}
          />
          
          {/* Writing helpers for students */}
          {!disabled && !showResult && (
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Tooltip title="Check spelling">
                <IconButton size="small">
                  <Spellcheck fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Show keyboard shortcuts">
                <IconButton size="small">
                  <Keyboard fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}
          
          {/* Word count and tips */}
          {answer && !showResult && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
              <Typography variant="caption" color="text.secondary">
                Words: {answer.trim().split(/\s+/).filter(word => word).length}
              </Typography>
              {!caseSensitive && (
                <Chip
                  label="Case doesn't matter"
                  size="small"
                  color="info"
                  variant="outlined"
                />
              )}
            </Box>
          )}
        </Paper>
      </Fade>
      
      {/* Encouraging message */}
      {answer && !disabled && !showResult && (
        <Fade in>
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="primary">
              Looking good! Review your answer and click submit when ready.
            </Typography>
          </Box>
        </Fade>
      )}
    </Box>
  );
};

export default ShortAnswerQuestion;