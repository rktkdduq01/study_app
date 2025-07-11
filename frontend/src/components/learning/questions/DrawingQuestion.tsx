import React from 'react';
import { Box, Typography } from '@mui/material';
import { Question } from '../../../types/learning';

interface DrawingQuestionProps {
  question: Question;
  answer: any;
  onAnswerChange: (answer: any) => void;
  disabled?: boolean;
}

const DrawingQuestion: React.FC<DrawingQuestionProps> = ({ question }) => {
  return (
    <Box>
      <Typography variant="h6">{question.question}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        Drawing question interface coming soon...
      </Typography>
    </Box>
  );
};

export default DrawingQuestion;