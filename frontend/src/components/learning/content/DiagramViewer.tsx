import React from 'react';
import { Box, Typography } from '@mui/material';

interface DiagramViewerProps {
  data?: any;
  onComplete: () => void;
}

const DiagramViewer: React.FC<DiagramViewerProps> = ({ onComplete }) => {
  return (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      <Typography variant="h6">Diagram Viewer</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        Diagram viewer coming soon...
      </Typography>
    </Box>
  );
};

export default DiagramViewer;