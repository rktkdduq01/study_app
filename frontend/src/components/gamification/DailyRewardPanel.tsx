import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Chip,
  Avatar,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CalendarToday as CalendarIcon,
  LocalFireDepartment as FireIcon,
  EmojiEvents as TrophyIcon,
  CardGiftcard as GiftIcon,
  Close as CloseIcon,
  CheckCircle as CheckIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import { gamificationService, DailyRewardStatus } from '../../services/gamificationService';

interface DailyRewardPanelProps {
  onClose?: () => void;
  onRewardClaimed?: (rewards: any) => void;
}

const DailyRewardPanel: React.FC<DailyRewardPanelProps> = ({
  onClose,
  onRewardClaimed,
}) => {
  const [status, setStatus] = useState<DailyRewardStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRewardDialog, setShowRewardDialog] = useState(false);
  const [claimedRewards, setClaimedRewards] = useState<any>(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      setLoading(true);
      const data = await gamificationService.getDailyRewardStatus();
      setStatus(data);
    } catch (err) {
      setError('Failed to load daily reward status');
    } finally {
      setLoading(false);
    }
  };

  const handleClaimReward = async () => {
    if (!status?.can_claim) return;

    try {
      setClaiming(true);
      const result = await gamificationService.claimDailyReward();
      
      if (result.success) {
        // Trigger confetti
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        });

        setClaimedRewards(result);
        setShowRewardDialog(true);
        
        // Reload status
        await loadStatus();
        
        if (onRewardClaimed) {
          onRewardClaimed(result);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to claim reward');
    } finally {
      setClaiming(false);
    }
  };

  const getDayRewards = () => {
    // Mock rewards for 30 days
    const rewards = [];
    for (let day = 1; day <= 30; day++) {
      let reward = { type: 'gold', amount: 50 + (day * 10), icon: '💰' };
      
      if (day % 7 === 0) {
        reward = { type: 'item', amount: 1, icon: '🎁' };
      } else if (day % 5 === 0) {
        reward = { type: 'exp', amount: 100 * day, icon: '⭐' };
      }
      
      rewards.push({
        day,
        reward,
        claimed: status ? day <= status.current_streak : false,
        current: status ? day === status.current_streak + 1 : false,
      });
    }
    return rewards;
  };

  if (loading) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Loading daily rewards...</Typography>
      </Paper>
    );
  }

  if (error) {
    return (
      <Alert severity="error" onClose={() => setError(null)}>
        {error}
      </Alert>
    );
  }

  const dayRewards = getDayRewards();
  const currentStreak = status?.current_streak || 0;

  return (
    <>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
              <CalendarIcon />
            </Avatar>
            <Box>
              <Typography variant="h5">Daily Rewards</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                <FireIcon color="error" />
                <Typography variant="body2" color="text.secondary">
                  {currentStreak} day streak
                </Typography>
                {status?.longest_streak && status.longest_streak > 0 && (
                  <Chip
                    label={`Best: ${status.longest_streak} days`}
                    size="small"
                    color="secondary"
                  />
                )}
              </Box>
            </Box>
          </Box>
          {onClose && (
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          )}
        </Box>

        {/* Calendar Grid */}
        <Grid container spacing={1} sx={{ mb: 3 }}>
          {dayRewards.map((dayReward) => (
            <Grid size={2} key={dayReward.day}>
              <motion.div
                whileHover={{ scale: dayReward.current ? 1.1 : 1 }}
                whileTap={{ scale: 0.95 }}
              >
                <Paper
                  sx={{
                    p: 1,
                    textAlign: 'center',
                    position: 'relative',
                    bgcolor: dayReward.claimed
                      ? 'success.light'
                      : dayReward.current
                      ? 'primary.light'
                      : 'background.paper',
                    border: dayReward.current ? 2 : 1,
                    borderColor: dayReward.current ? 'primary.main' : 'divider',
                    cursor: dayReward.current ? 'pointer' : 'default',
                    opacity: !dayReward.claimed && !dayReward.current ? 0.6 : 1,
                  }}
                  onClick={dayReward.current ? handleClaimReward : undefined}
                >
                  <Typography variant="caption" color="text.secondary">
                    Day {dayReward.day}
                  </Typography>
                  <Typography variant="h4" sx={{ my: 0.5 }}>
                    {dayReward.reward.icon}
                  </Typography>
                  <Typography variant="caption">
                    {dayReward.reward.amount}
                  </Typography>
                  
                  {dayReward.claimed && (
                    <CheckIcon
                      sx={{
                        position: 'absolute',
                        top: 4,
                        right: 4,
                        fontSize: 16,
                        color: 'success.main',
                      }}
                    />
                  )}
                  
                  {!dayReward.claimed && !dayReward.current && (
                    <LockIcon
                      sx={{
                        position: 'absolute',
                        top: 4,
                        right: 4,
                        fontSize: 16,
                        color: 'text.disabled',
                      }}
                    />
                  )}
                  
                  {dayReward.current && (
                    <motion.div
                      animate={{
                        opacity: [0.5, 1, 0.5],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                      }}
                      style={{
                        position: 'absolute',
                        inset: -2,
                        border: '2px solid',
                        borderColor: 'primary.main',
                        borderRadius: 'inherit',
                      }}
                    />
                  )}
                </Paper>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        {/* Claim Button */}
        <Box sx={{ textAlign: 'center' }}>
          {status?.can_claim ? (
            <Button
              variant="contained"
              size="large"
              startIcon={<GiftIcon />}
              onClick={handleClaimReward}
              disabled={claiming}
              sx={{
                background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
                boxShadow: '0 3px 5px 2px rgba(255, 105, 135, .3)',
              }}
            >
              {claiming ? 'Claiming...' : 'Claim Daily Reward'}
            </Button>
          ) : (
            <Alert severity="info" sx={{ display: 'inline-flex' }}>
              Come back tomorrow to claim your next reward!
            </Alert>
          )}
        </Box>

        {/* Milestone Rewards */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Milestone Rewards
          </Typography>
          <Grid container spacing={2}>
            {[7, 14, 30].map((milestone) => (
              <Grid size={4} key={milestone}>
                <Paper
                  sx={{
                    p: 2,
                    textAlign: 'center',
                    bgcolor: currentStreak >= milestone ? 'success.light' : 'background.paper',
                    opacity: currentStreak >= milestone ? 1 : 0.6,
                  }}
                >
                  <TrophyIcon
                    sx={{
                      fontSize: 40,
                      color: currentStreak >= milestone ? 'success.main' : 'text.disabled',
                    }}
                  />
                  <Typography variant="subtitle2">{milestone} Days</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {milestone === 7 && 'Weekly Boost'}
                    {milestone === 14 && '500 Gold'}
                    {milestone === 30 && 'Special Badge'}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Paper>

      {/* Reward Dialog */}
      <Dialog open={showRewardDialog} onClose={() => setShowRewardDialog(false)}>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrophyIcon color="primary" />
            Rewards Claimed!
          </Box>
        </DialogTitle>
        <DialogContent>
          <AnimatePresence>
            {claimedRewards && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Day {currentStreak} Rewards
                  </Typography>
                  
                  {claimedRewards.rewards?.map((reward: any, index: number) => (
                    <Chip
                      key={index}
                      label={`+${reward.amount} ${reward.type}`}
                      color="primary"
                      sx={{ m: 0.5 }}
                    />
                  ))}
                  
                  {claimedRewards.bonus_rewards && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="subtitle2" color="secondary">
                        Bonus Rewards!
                      </Typography>
                      {claimedRewards.bonus_rewards.map((reward: any, index: number) => (
                        <Chip
                          key={index}
                          label={`+${reward.amount || 1} ${reward.type}`}
                          color="secondary"
                          sx={{ m: 0.5 }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              </motion.div>
            )}
          </AnimatePresence>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowRewardDialog(false)}>
            Awesome!
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default DailyRewardPanel;