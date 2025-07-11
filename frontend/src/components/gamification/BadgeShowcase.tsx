import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  Avatar,
  LinearProgress,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Badge as MuiBadge,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  EmojiEvents as TrophyIcon,
  Star as StarIcon,
  Lock as LockIcon,
  Visibility as ViewIcon,
  Category as CategoryIcon,
  AutoAwesome as AutoAwesomeIcon,
  School as SchoolIcon,
  Group as GroupIcon,
  Event as EventIcon,
  Flag as FlagIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { gamificationService, Badge } from '../../services/gamificationService';

interface BadgeShowcaseProps {
  userId?: string;
  compact?: boolean;
  onBadgeClick?: (badge: Badge) => void;
}

const BadgeShowcase: React.FC<BadgeShowcaseProps> = ({
  userId,
  compact = false,
  onBadgeClick,
}) => {
  const [badges, setBadges] = useState<Badge[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedBadge, setSelectedBadge] = useState<Badge | null>(null);
  const [totalBadges, setTotalBadges] = useState(0);
  const [earnedBadges, setEarnedBadges] = useState(0);

  const categoryIcons = {
    academic: <SchoolIcon />,
    social: <GroupIcon />,
    special: <AutoAwesomeIcon />,
    seasonal: <EventIcon />,
    milestone: <FlagIcon />,
  };

  const rarityColors = {
    common: '#9E9E9E',
    uncommon: '#4CAF50',
    rare: '#2196F3',
    epic: '#9C27B0',
    legendary: '#FF9800',
  };

  useEffect(() => {
    loadBadges();
  }, [selectedCategory]);

  const loadBadges = async () => {
    try {
      setLoading(true);
      const category = selectedCategory === 'all' ? undefined : selectedCategory;
      const data = await gamificationService.getBadges(category);
      setBadges(data.badges);
      setTotalBadges(data.total_badges);
      setEarnedBadges(data.earned_badges);
    } catch (error) {
      console.error('Failed to load badges:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBadgeClick = (badge: Badge) => {
    if (badge.is_secret && !badge.earned) return;
    
    setSelectedBadge(badge);
    if (onBadgeClick) {
      onBadgeClick(badge);
    }
  };

  const filteredBadges = badges.filter(badge => 
    selectedCategory === 'all' || badge.category === selectedCategory
  );

  const earnedPercentage = totalBadges > 0 ? (earnedBadges / totalBadges) * 100 : 0;

  if (compact) {
    const displayBadges = badges.filter(b => b.earned).slice(0, 6);
    
    return (
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        {displayBadges.map((badge) => (
          <Tooltip key={badge.id} title={badge.name}>
            <Avatar
              src={badge.icon_url}
              sx={{
                width: 32,
                height: 32,
                bgcolor: rarityColors[badge.rarity as keyof typeof rarityColors],
                cursor: 'pointer',
              }}
              onClick={() => handleBadgeClick(badge)}
            >
              <TrophyIcon sx={{ fontSize: 20 }} />
            </Avatar>
          </Tooltip>
        ))}
        {earnedBadges > 6 && (
          <Chip
            label={`+${earnedBadges - 6}`}
            size="small"
            color="primary"
          />
        )}
      </Box>
    );
  }

  return (
    <>
      <Paper sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                <TrophyIcon />
              </Avatar>
              <Box>
                <Typography variant="h5">Badge Collection</Typography>
                <Typography variant="body2" color="text.secondary">
                  {earnedBadges} of {totalBadges} badges earned
                </Typography>
              </Box>
            </Box>
            <Button
              variant="outlined"
              startIcon={<AutoAwesomeIcon />}
              onClick={() => gamificationService.checkAndAwardBadges()}
            >
              Check New Badges
            </Button>
          </Box>
          
          <LinearProgress
            variant="determinate"
            value={earnedPercentage}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(0,0,0,0.1)',
            }}
          />
        </Box>

        {/* Category Tabs */}
        <Tabs
          value={selectedCategory}
          onChange={(e, value) => setSelectedCategory(value)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ mb: 3 }}
        >
          <Tab label="All" value="all" icon={<CategoryIcon />} iconPosition="start" />
          {Object.entries(categoryIcons).map(([category, icon]) => (
            <Tab
              key={category}
              label={category.charAt(0).toUpperCase() + category.slice(1)}
              value={category}
              icon={icon}
              iconPosition="start"
            />
          ))}
        </Tabs>

        {/* Badges Grid */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={2}>
            {filteredBadges.map((badge) => (
              <Grid size={{ xs: 6, sm: 4, md: 3 }} key={badge.id}>
                <motion.div
                  whileHover={{ scale: badge.earned || !badge.is_secret ? 1.05 : 1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Paper
                    sx={{
                      p: 2,
                      textAlign: 'center',
                      cursor: badge.earned || !badge.is_secret ? 'pointer' : 'default',
                      opacity: badge.earned ? 1 : 0.6,
                      position: 'relative',
                      border: badge.earned ? 2 : 1,
                      borderColor: badge.earned 
                        ? rarityColors[badge.rarity as keyof typeof rarityColors]
                        : 'divider',
                      background: badge.earned
                        ? `linear-gradient(135deg, ${rarityColors[badge.rarity as keyof typeof rarityColors]}22 0%, transparent 100%)`
                        : 'none',
                    }}
                    onClick={() => handleBadgeClick(badge)}
                  >
                    {badge.is_secret && !badge.earned ? (
                      <>
                        <Avatar
                          sx={{
                            width: 64,
                            height: 64,
                            mx: 'auto',
                            mb: 1,
                            bgcolor: 'grey.300',
                          }}
                        >
                          <LockIcon />
                        </Avatar>
                        <Typography variant="subtitle2">???</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Secret Badge
                        </Typography>
                      </>
                    ) : (
                      <>
                        <MuiBadge
                          badgeContent={badge.earned ? '✓' : null}
                          color="success"
                        >
                          <Avatar
                            src={badge.icon_url}
                            sx={{
                              width: 64,
                              height: 64,
                              mx: 'auto',
                              mb: 1,
                              bgcolor: rarityColors[badge.rarity as keyof typeof rarityColors],
                            }}
                          >
                            <TrophyIcon />
                          </Avatar>
                        </MuiBadge>
                        <Typography variant="subtitle2" noWrap>
                          {badge.name}
                        </Typography>
                        <Chip
                          label={badge.rarity}
                          size="small"
                          sx={{
                            mt: 0.5,
                            color: 'white',
                            bgcolor: rarityColors[badge.rarity as keyof typeof rarityColors],
                          }}
                        />
                      </>
                    )}
                    
                    {badge.progress > 0 && badge.progress < 100 && !badge.earned && (
                      <LinearProgress
                        variant="determinate"
                        value={badge.progress}
                        sx={{
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          height: 4,
                        }}
                      />
                    )}
                  </Paper>
                </motion.div>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* Badge Detail Dialog */}
      <Dialog
        open={!!selectedBadge}
        onClose={() => setSelectedBadge(null)}
        maxWidth="sm"
        fullWidth
      >
        {selectedBadge && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Avatar
                  src={selectedBadge.icon_url}
                  sx={{
                    width: 64,
                    height: 64,
                    bgcolor: rarityColors[selectedBadge.rarity as keyof typeof rarityColors],
                  }}
                >
                  <TrophyIcon sx={{ fontSize: 40 }} />
                </Avatar>
                <Box>
                  <Typography variant="h6">{selectedBadge.name}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                    <Chip
                      label={selectedBadge.category}
                      size="small"
                      icon={categoryIcons[selectedBadge.category as keyof typeof categoryIcons]}
                    />
                    <Chip
                      label={selectedBadge.rarity}
                      size="small"
                      sx={{
                        color: 'white',
                        bgcolor: rarityColors[selectedBadge.rarity as keyof typeof rarityColors],
                      }}
                    />
                  </Box>
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" paragraph>
                {selectedBadge.description}
              </Typography>
              
              {selectedBadge.earned ? (
                <Alert severity="success" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    Earned on {new Date(selectedBadge.earned_at!).toLocaleDateString()}
                  </Typography>
                </Alert>
              ) : (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Progress: {Math.round(selectedBadge.progress)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={selectedBadge.progress}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              )}
              
              {/* Badge Stats */}
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Rarity: {selectedBadge.rarity.charAt(0).toUpperCase() + selectedBadge.rarity.slice(1)}
                </Typography>
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedBadge(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </>
  );
};

export default BadgeShowcase;