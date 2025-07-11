import React from 'react';
import { Box, Typography } from '@mui/material';
import { Question } from '../../../types/learning';

interface OrderingQuestionProps {
  question: Question;
  answer: any;
  onAnswerChange: (answer: any) => void;
  disabled?: boolean;
}

const OrderingQuestion: React.FC<OrderingQuestionProps> = ({ question }) => {
  return (
    <Box>
      <Typography variant="h6">{question.question}</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        Ordering question interface coming soon...
      </Typography>
    </Box>
  );
};

export default OrderingQuestion;