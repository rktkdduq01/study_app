import React from 'react';
import { Box, Typography, TextField, Chip } from '@mui/material';
import { Question } from '../../../types/learning';

interface FillInBlankQuestionProps {
  question: Question;
  answer: any;
  onAnswerChange: (answer: any) => void;
  disabled?: boolean;
}

const FillInBlankQuestion: React.FC<FillInBlankQuestionProps> = ({
  question,
  answer = {},
  onAnswerChange,
  disabled = false,
}) => {
  const { blanks = [] } = question.data;
  
  const handleBlankChange = (blankId: string, value: string) => {
    onAnswerChange({
      ...answer,
      [blankId]: value,
    });
  };

  // Parse question text and replace blanks with input fields
  const renderQuestionWithBlanks = () => {
    let questionText = question.question;
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;
    
    blanks.forEach((blank, index) => {
      const blankPattern = `___${index + 1}___`;
      const blankIndex = questionText.indexOf(blankPattern, lastIndex);
      
      if (blankIndex !== -1) {
        // Add text before blank
        if (blankIndex > lastIndex) {
          elements.push(
            <span key={`text-${index}`}>
              {questionText.substring(lastIndex, blankIndex)}
            </span>
          );
        }
        
        // Add input field
        elements.push(
          <TextField
            key={`blank-${blank.id}`}
            value={answer[blank.id] || ''}
            onChange={(e) => handleBlankChange(blank.id, e.target.value)}
            disabled={disabled}
            placeholder={blank.placeholder || '?'}
            size="small"
            sx={{
              mx: 1,
              minWidth: 100,
              '& .MuiInputBase-input': {
                textAlign: 'center',
                fontWeight: 600,
              },
            }}
          />
        );
        
        lastIndex = blankIndex + blankPattern.length;
      }
    });
    
    // Add remaining text
    if (lastIndex < questionText.length) {
      elements.push(
        <span key="text-end">{questionText.substring(lastIndex)}</span>
      );
    }
    
    return elements;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
        Fill in the blanks
      </Typography>
      
      <Box sx={{ fontSize: '1.2rem', lineHeight: 2.5 }}>
        {renderQuestionWithBlanks()}
      </Box>
      
      {blanks.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="caption" color="text.secondary">
            Fill in all {blanks.length} blank{blanks.length > 1 ? 's' : ''} to complete the sentence
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default FillInBlankQuestion;