import React from 'react';
import {
  Box,
  LinearProgress,
  Typography,
  Chip,
  Avatar,
  Paper,
  Tooltip,
} from '@mui/material';
import {
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  EmojiEvents as TrophyIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

interface LevelProgressBarProps {
  level: number;
  currentExp: number;
  requiredExp: number;
  title: string;
  compact?: boolean;
  showAnimation?: boolean;
}

const LevelProgressBar: React.FC<LevelProgressBarProps> = ({
  level,
  currentExp,
  requiredExp,
  title,
  compact = false,
  showAnimation = true,
}) => {
  const progress = (currentExp / requiredExp) * 100;
  const expToNext = requiredExp - currentExp;

  const levelColors = {
    1: '#9E9E9E',    // Gray - Beginner
    10: '#4CAF50',   // Green - Apprentice
    20: '#2196F3',   // Blue - Journeyman
    30: '#9C27B0',   // Purple - Expert
    40: '#FF9800',   // Orange - Master
    50: '#F44336',   // Red - Grand
    60: '#E91E63',   // Pink - Elite
    70: '#FFD700',   // Gold - Legendary
    80: '#FF1744',   // Crimson - Mythic
    90: '#6A1B9A',   // Deep Purple - Transcendent
  };

  const getLevelColor = () => {
    const levels = Object.keys(levelColors).map(Number).sort((a, b) => b - a);
    for (const lvl of levels) {
      if (level >= lvl) {
        return levelColors[lvl as keyof typeof levelColors];
      }
    }
    return levelColors[1];
  };

  const levelColor = getLevelColor();

  if (compact) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Chip
          icon={<StarIcon />}
          label={`Lv ${level}`}
          size="small"
          sx={{ bgcolor: levelColor, color: 'white' }}
        />
        <Box sx={{ flex: 1 }}>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{
              height: 6,
              borderRadius: 3,
              backgroundColor: 'rgba(0,0,0,0.1)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: levelColor,
              },
            }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary">
          {Math.round(progress)}%
        </Typography>
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <motion.div
          animate={showAnimation ? { scale: [1, 1.2, 1] } : {}}
          transition={{ duration: 0.5 }}
        >
          <Avatar
            sx={{
              bgcolor: levelColor,
              width: 48,
              height: 48,
              mr: 2,
              boxShadow: `0 0 20px ${levelColor}`,
            }}
          >
            <Typography variant="h6" fontWeight="bold">
              {level}
            </Typography>
          </Avatar>
        </motion.div>
        
        <Box sx={{ flex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="subtitle1" fontWeight="medium">
              Level {level}
            </Typography>
            <Chip
              label={title}
              size="small"
              icon={<TrophyIcon />}
              color="primary"
              variant="outlined"
            />
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              {currentExp.toLocaleString()} / {requiredExp.toLocaleString()} XP
            </Typography>
            <TrendingUpIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {expToNext.toLocaleString()} to next level
            </Typography>
          </Box>
        </Box>
      </Box>

      <Tooltip title={`${Math.round(progress)}% to Level ${level + 1}`}>
        <Box sx={{ position: 'relative' }}>
          <LinearProgress
            variant="determinate"
            value={progress}
            sx={{
              height: 12,
              borderRadius: 6,
              backgroundColor: 'rgba(0,0,0,0.1)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 6,
                background: `linear-gradient(90deg, ${levelColor} 0%, ${levelColor}CC 100%)`,
              },
            }}
          />
          {showAnimation && progress > 0 && (
            <motion.div
              style={{
                position: 'absolute',
                top: '50%',
                left: `${progress}%`,
                transform: 'translate(-50%, -50%)',
              }}
              animate={{
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
              }}
            >
              <Box
                sx={{
                  width: 4,
                  height: 4,
                  bgcolor: 'white',
                  borderRadius: '50%',
                  boxShadow: '0 0 10px white',
                }}
              />
            </motion.div>
          )}
        </Box>
      </Tooltip>

      {/* Level up animation placeholder */}
      {showAnimation && progress >= 95 && (
        <motion.div
          animate={{
            opacity: [0.5, 1, 0.5],
          }}
          transition={{
            duration: 1,
            repeat: Infinity,
          }}
        >
          <Typography
            variant="caption"
            color="primary"
            sx={{ mt: 1, display: 'block', textAlign: 'center' }}
          >
            🎉 Level up imminent! 🎉
          </Typography>
        </motion.div>
      )}
    </Paper>
  );
};

export default LevelProgressBar;