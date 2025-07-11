import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { 
  SearchOff as SearchOffIcon,
  Assignment as QuestIcon,
} from '@mui/icons-material';

interface EmptyQuestListProps {
  hasFilters: boolean;
  onResetFilters: () => void;
}

const EmptyQuestList: React.FC<EmptyQuestListProps> = ({
  hasFilters,
  onResetFilters,
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 8,
        textAlign: 'center',
      }}
    >
      {hasFilters ? (
        <>
          <SearchOffIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            No quests found
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Try adjusting your filters to see more quests.
          </Typography>
          <Button 
            variant="contained" 
            onClick={onResetFilters}
            sx={{ mt: 2 }}
          >
            Clear Filters
          </Button>
        </>
      ) : (
        <>
          <QuestIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            No quests available
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Check back later for new quests!
          </Typography>
        </>
      )}
    </Box>
  );
};

export default EmptyQuestList;