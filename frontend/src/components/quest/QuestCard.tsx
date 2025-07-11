import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Chip,
  Button,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  Timer as TimerIcon,
  Star as StarIcon,
  Lock as LockIcon,
  PlayArrow as PlayIcon,
  NewReleases as NewIcon,
} from '@mui/icons-material';
import { Quest, QuestProgress, QuestType } from '../../types/quest';
import { 
  getDifficultyColor, 
  calculateQuestDuration, 
  getRewardSummary,
  canStartQuest,
  isQuestNew,
} from '../../utils/questHelpers';
import { QUEST_TYPE_LABELS, SUBJECT_LABELS } from '../../constants/quest';

interface QuestCardProps {
  quest: Quest;
  userLevel: number;
  progress?: QuestProgress;
  onStartQuest: (questId: number) => void;
  onViewDetails: (questId: number) => void;
}

const QuestCard: React.FC<QuestCardProps> = ({
  quest,
  userLevel,
  progress,
  onStartQuest,
  onViewDetails,
}) => {
  const isLocked = !canStartQuest(quest, userLevel);
  const isNew = isQuestNew(quest);
  const rewards = getRewardSummary(quest);
  
  const getProgressPercentage = (): number => {
    if (!progress || !progress.progress) return 0;
    // This would depend on the actual progress structure
    // For now, returning a mock value
    return 0;
  };

  const renderQuestStatus = () => {
    if (progress) {
      switch (progress.status) {
        case 'completed':
          return <Chip label="Completed" color="success" size="small" />;
        case 'in_progress':
          return (
            <Box sx={{ width: '100%' }}>
              <LinearProgress 
                variant="determinate" 
                value={getProgressPercentage()} 
                sx={{ height: 6, borderRadius: 3 }}
              />
            </Box>
          );
        case 'failed':
          return <Chip label="Failed" color="error" size="small" />;
        default:
          return null;
      }
    }
    return null;
  };

  return (
    <Card 
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        opacity: isLocked ? 0.7 : 1,
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: isLocked ? 'none' : 'translateY(-4px)',
          boxShadow: isLocked ? 1 : 6,
        },
      }}
    >
      {/* New Badge */}
      {isNew && (
        <Box
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            zIndex: 1,
          }}
        >
          <Tooltip title="New Quest!">
            <NewIcon color="secondary" />
          </Tooltip>
        </Box>
      )}

      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        {/* Title */}
        <Typography 
          variant="h6" 
          component="h3" 
          gutterBottom
          sx={{ 
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            minHeight: '3.6em',
          }}
        >
          {quest.title}
        </Typography>

        {/* Quest Type and Subject */}
        <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
          <Chip 
            label={QUEST_TYPE_LABELS[quest.type || quest.quest_type || QuestType.DAILY]} 
            size="small" 
            variant="outlined"
          />
          {quest.subject && (
            <Chip 
              label={SUBJECT_LABELS[quest.subject] || quest.subject} 
              size="small" 
              variant="outlined"
            />
          )}
        </Box>

        {/* Description */}
        <Typography 
          variant="body2" 
          color="text.secondary"
          sx={{
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            mb: 2,
            minHeight: '2.8em',
          }}
        >
          {quest.description}
        </Typography>

        {/* Quest Info */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {/* Difficulty */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Difficulty:
            </Typography>
            <Chip
              label={quest.difficulty}
              size="small"
              color={getDifficultyColor(quest.difficulty)}
            />
          </Box>

          {/* Time Limit */}
          {quest.time_limit_minutes && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <TimerIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {calculateQuestDuration(quest.time_limit_minutes)}
              </Typography>
            </Box>
          )}

          {/* Level Requirement */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {isLocked ? <LockIcon fontSize="small" color="error" /> : <StarIcon fontSize="small" color="action" />}
            <Typography 
              variant="body2" 
              color={isLocked ? 'error' : 'text.secondary'}
            >
              Level {quest.min_level} required
            </Typography>
          </Box>

          {/* Rewards */}
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            {rewards.map((reward, index) => (
              <Chip
                key={index}
                label={reward}
                size="small"
                sx={{ fontSize: '0.75rem' }}
              />
            ))}
          </Box>
        </Box>

        {/* Progress Status */}
        {renderQuestStatus()}
      </CardContent>

      <CardActions sx={{ px: 2, pb: 2 }}>
        <Button
          size="small"
          onClick={() => onViewDetails(quest.id)}
        >
          View Details
        </Button>
        <Button
          size="small"
          variant="contained"
          startIcon={<PlayIcon />}
          onClick={() => onStartQuest(quest.id)}
          disabled={isLocked || progress?.status === 'completed'}
          sx={{ ml: 'auto' }}
        >
          {progress?.status === 'in_progress' ? 'Continue' : 'Start'}
        </Button>
      </CardActions>
    </Card>
  );
};

export default QuestCard;