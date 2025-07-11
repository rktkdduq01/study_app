import React, { useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Chip,
  IconButton,
  Slide,
  Grow,
} from '@mui/material';
import {
  Close as CloseIcon,
  EmojiEvents as TrophyIcon,
  Star as StarIcon,
  CardGiftcard as GiftIcon,
  LocalFireDepartment as FireIcon,
  AutoAwesome as AutoAwesomeIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';

export interface RewardData {
  type: 'level_up' | 'badge' | 'item' | 'quest_complete' | 'daily_reward' | 'achievement';
  title: string;
  description: string;
  icon?: string;
  rewards?: Array<{
    type: string;
    amount?: number;
    name?: string;
    icon?: string;
  }>;
  rarity?: string;
}

interface RewardNotificationProps {
  reward: RewardData;
  onClose: () => void;
  duration?: number;
}

const RewardNotification: React.FC<RewardNotificationProps> = ({
  reward,
  onClose,
  duration = 5000,
}) => {
  const typeIcons = {
    level_up: <StarIcon sx={{ fontSize: 40 }} />,
    badge: <TrophyIcon sx={{ fontSize: 40 }} />,
    item: <GiftIcon sx={{ fontSize: 40 }} />,
    quest_complete: <AutoAwesomeIcon sx={{ fontSize: 40 }} />,
    daily_reward: <FireIcon sx={{ fontSize: 40 }} />,
    achievement: <TrophyIcon sx={{ fontSize: 40 }} />,
  };

  const typeColors = {
    level_up: '#FFD700',
    badge: '#9C27B0',
    item: '#2196F3',
    quest_complete: '#4CAF50',
    daily_reward: '#FF5722',
    achievement: '#FF9800',
  };

  const rarityColors = {
    common: '#9E9E9E',
    uncommon: '#4CAF50',
    rare: '#2196F3',
    epic: '#9C27B0',
    legendary: '#FF9800',
  };

  useEffect(() => {
    // Trigger confetti for special rewards
    if (reward.type === 'level_up' || reward.type === 'achievement' || reward.rarity === 'legendary') {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.3 },
        colors: [typeColors[reward.type] || '#FFD700'],
      });
    }

    // Auto close after duration
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [reward, duration, onClose]);

  return (
    <AnimatePresence>
      <Slide direction="down" in={true} mountOnEnter unmountOnExit>
        <Paper
          sx={{
            position: 'fixed',
            top: 20,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 2000,
            minWidth: 350,
            maxWidth: 500,
            overflow: 'hidden',
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          }}
        >
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Background Gradient */}
            <Box
              sx={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: `linear-gradient(135deg, ${typeColors[reward.type]}22 0%, transparent 100%)`,
                zIndex: 0,
              }}
            />

            {/* Content */}
            <Box sx={{ position: 'relative', p: 3 }}>
              <IconButton
                size="small"
                onClick={onClose}
                sx={{
                  position: 'absolute',
                  top: 8,
                  right: 8,
                  zIndex: 1,
                }}
              >
                <CloseIcon />
              </IconButton>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <motion.div
                  animate={{
                    rotate: [0, 10, -10, 10, 0],
                    scale: [1, 1.1, 1],
                  }}
                  transition={{
                    duration: 0.5,
                    ease: "easeInOut",
                  }}
                >
                  <Avatar
                    sx={{
                      width: 64,
                      height: 64,
                      bgcolor: typeColors[reward.type],
                      boxShadow: `0 0 20px ${typeColors[reward.type]}`,
                    }}
                  >
                    {reward.icon ? (
                      <img src={reward.icon} alt={reward.title} style={{ width: '80%', height: '80%' }} />
                    ) : (
                      typeIcons[reward.type]
                    )}
                  </Avatar>
                </motion.div>

                <Box sx={{ flex: 1 }}>
                  <Typography variant="h6" fontWeight="bold">
                    {reward.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {reward.description}
                  </Typography>
                </Box>
              </Box>

              {/* Rewards List */}
              {reward.rewards && reward.rewards.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Rewards:
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {reward.rewards.map((r, index) => (
                      <Grow key={index} in={true} timeout={300 * (index + 1)}>
                        <Chip
                          icon={r.icon ? <img src={r.icon} alt="" style={{ width: 20, height: 20 }} /> : undefined}
                          label={r.name || `+${r.amount} ${r.type}`}
                          color="primary"
                          size="small"
                          sx={{
                            fontWeight: 'bold',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                          }}
                        />
                      </Grow>
                    ))}
                  </Box>
                </Box>
              )}

              {/* Rarity Indicator */}
              {reward.rarity && (
                <Box sx={{ mt: 2, textAlign: 'center' }}>
                  <Chip
                    label={reward.rarity.toUpperCase()}
                    size="small"
                    sx={{
                      color: 'white',
                      bgcolor: rarityColors[reward.rarity as keyof typeof rarityColors],
                      fontWeight: 'bold',
                      boxShadow: `0 0 10px ${rarityColors[reward.rarity as keyof typeof rarityColors]}`,
                    }}
                  />
                </Box>
              )}

              {/* Progress Bar Animation */}
              <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 4 }}>
                <motion.div
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: duration / 1000, ease: "linear" }}
                  style={{
                    height: '100%',
                    backgroundColor: typeColors[reward.type],
                    transformOrigin: 'left',
                  }}
                />
              </Box>
            </Box>
          </motion.div>
        </Paper>
      </Slide>
    </AnimatePresence>
  );
};

export default RewardNotification;