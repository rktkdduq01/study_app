import React from 'react';
import { Box, Typography } from '@mui/material';

interface SimulationPlayerProps {
  config?: any;
  onComplete: () => void;
}

const SimulationPlayer: React.FC<SimulationPlayerProps> = ({ onComplete }) => {
  return (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      <Typography variant="h6">Simulation Player</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        Simulation player coming soon...
      </Typography>
    </Box>
  );
};

export default SimulationPlayer;