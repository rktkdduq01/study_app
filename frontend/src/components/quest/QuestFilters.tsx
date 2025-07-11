import React from 'react';
import {
  Paper,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Box,
  Chip,
  InputAdornment,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { QuestType, QuestDifficulty } from '../../types/quest';
import { QuestFilters as QuestFiltersType } from '../../hooks/useQuestFilters';
import { 
  QUEST_TYPE_LABELS, 
  QUEST_DIFFICULTY_LABELS, 
  SUBJECT_LABELS 
} from '../../constants/quest';

interface QuestFiltersProps {
  filters: QuestFiltersType;
  activeFilterCount: number;
  onFilterChange: <K extends keyof QuestFiltersType>(
    key: K,
    value: QuestFiltersType[K]
  ) => void;
  onResetFilters: () => void;
}

const QuestFilters: React.FC<QuestFiltersProps> = ({
  filters,
  activeFilterCount,
  onFilterChange,
  onResetFilters,
}) => {
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange('searchQuery', event.target.value);
  };

  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Search Bar */}
        <TextField
          fullWidth
          placeholder="Search quests..."
          value={filters.searchQuery}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />

        {/* Filter Controls */}
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {/* Quest Type Filter */}
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel id="quest-type-label">Type</InputLabel>
            <Select
              labelId="quest-type-label"
              value={filters.type}
              label="Type"
              onChange={(e) => onFilterChange('type', e.target.value as QuestType | 'all')}
            >
              <MenuItem value="all">All Types</MenuItem>
              {Object.entries(QUEST_TYPE_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Difficulty Filter */}
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel id="difficulty-label">Difficulty</InputLabel>
            <Select
              labelId="difficulty-label"
              value={filters.difficulty}
              label="Difficulty"
              onChange={(e) => onFilterChange('difficulty', e.target.value as QuestDifficulty | 'all')}
            >
              <MenuItem value="all">All Difficulties</MenuItem>
              {Object.entries(QUEST_DIFFICULTY_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Subject Filter */}
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel id="subject-label">Subject</InputLabel>
            <Select
              labelId="subject-label"
              value={filters.subject}
              label="Subject"
              onChange={(e) => onFilterChange('subject', e.target.value)}
            >
              <MenuItem value="all">All Subjects</MenuItem>
              {Object.entries(SUBJECT_LABELS).map(([value, label]) => (
                <MenuItem key={value} value={value}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Filter Actions */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 'auto' }}>
            {activeFilterCount > 0 && (
              <>
                <Chip
                  icon={<FilterIcon />}
                  label={`${activeFilterCount} active`}
                  size="small"
                  color="primary"
                />
                <Button
                  startIcon={<ClearIcon />}
                  onClick={onResetFilters}
                  size="small"
                >
                  Clear Filters
                </Button>
              </>
            )}
          </Box>
        </Box>
      </Box>
    </Paper>
  );
};

export default QuestFilters;