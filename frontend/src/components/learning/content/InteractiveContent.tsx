import React from 'react';
import { Box, Typography } from '@mui/material';

interface InteractiveContentProps {
  url?: string;
  data?: any;
  onComplete: () => void;
}

const InteractiveContent: React.FC<InteractiveContentProps> = ({ onComplete }) => {
  return (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      <Typography variant="h6">Interactive Content</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        Interactive content viewer coming soon...
      </Typography>
    </Box>
  );
};

export default InteractiveContent;