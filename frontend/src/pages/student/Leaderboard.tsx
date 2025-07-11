import React, { useState, useEffect } from 'react';
import { GridContainer, FlexContainer, FlexRow } from '../../components/layout';
import { LoadingErrorWrapper } from '../../components/common/LoadingErrorWrapper';
import {
  Container,
  
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
  Badge,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  CircularProgress,
  LinearProgress,
  Zoom,
  Fade,
  Slide,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import {
  EmojiEvents,
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Star,
  EmojiEvents as Crown,
  Diamond,
  Group,
  Person,
  School,
  Science,
  MenuBook,
  History,
  Speed,
  LocalFireDepartment,
  WorkspacePremium,
  MilitaryTech,
  DiamondOutlined,
  Groups,
  CalendarToday,
  Timer,
  CheckCircle,
  Lock,
  Visibility,
  Refresh,
  FilterList,
  Search,
  Add,
  PersonAdd,
  Flag,
  Celebration,
  AccountBox,
  Leaderboard as LeaderboardIcon,
  Schedule,
  AutoAwesome,
  Shield,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import {
  LeaderboardType,
  LeaderboardResponse,
  LeaderboardEntry,
  RankTier,
  CompetitionEvent,
  Guild,
  FriendsLeaderboard,
  LeaderboardStats
} from '../../types/leaderboard';
import leaderboardService from '../../services/leaderboardService';
import { format, formatDistanceToNow } from 'date-fns';
import { 
  flexBox, 
  gridLayout, 
  containerStyles, 
  componentStyles, 
  touchStyles,
  responsiveValues 
} from '../../utils/responsive';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
  </div>
);

const LeaderboardPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { character } = useAppSelector((state) => state.character);

  const [tabValue, setTabValue] = useState(0);
  const [selectedLeaderboardType, setSelectedLeaderboardType] = useState<LeaderboardType>(LeaderboardType.OVERALL);
  const [leaderboardData, setLeaderboardData] = useState<LeaderboardResponse | null>(null);
  const [competitions, setCompetitions] = useState<CompetitionEvent[]>([]);
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [friendsLeaderboard, setFriendsLeaderboard] = useState<FriendsLeaderboard | null>(null);
  const [userStats, setUserStats] = useState<LeaderboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [selectedCompetition, setSelectedCompetition] = useState<CompetitionEvent | null>(null);
  const [showCompetitionDialog, setShowCompetitionDialog] = useState(false);
  const [timeFilter, setTimeFilter] = useState('all_time');

  useEffect(() => {
    loadLeaderboardData();
  }, [selectedLeaderboardType]);

  useEffect(() => {
    if (tabValue === 0) {
      loadLeaderboardData();
    } else if (tabValue === 1) {
      loadCompetitions();
    } else if (tabValue === 2) {
      loadGuilds();
    } else if (tabValue === 3) {
      loadFriendsData();
    }
  }, [tabValue]);

  const loadLeaderboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [leaderboard, stats] = await Promise.all([
        leaderboardService.mockGetLeaderboard(selectedLeaderboardType),
        leaderboardService.mockGetLeaderboardStats()
      ]);
      setLeaderboardData(leaderboard);
      setUserStats(stats);
    } catch (error) {
      console.error('Failed to load leaderboard data:', error);
      setError(error as Error);
    } finally {
      setLoading(false);
    }
  };

  const loadCompetitions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await leaderboardService.mockGetActiveCompetitions();
      setCompetitions(data);
    } catch (error) {
      console.error('Failed to load competitions:', error);
      setError(error as Error);
    } finally {
      setLoading(false);
    }
  };

  const loadGuilds = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await leaderboardService.mockGetGuilds();
      setGuilds(data);
    } catch (error) {
      console.error('Failed to load guilds:', error);
      setError(error as Error);
    } finally {
      setLoading(false);
    }
  };

  const loadFriendsData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await leaderboardService.mockGetFriendsLeaderboard();
      setFriendsLeaderboard(data);
    } catch (error) {
      console.error('Failed to load friends data:', error);
      setError(error as Error);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (tabValue === 0) {
      loadLeaderboardData();
    } else if (tabValue === 1) {
      loadCompetitions();
    } else if (tabValue === 2) {
      loadGuilds();
    } else if (tabValue === 3) {
      loadFriendsData();
    }
  };

  const getTierColor = (tier: RankTier) => {
    switch (tier) {
      case RankTier.BRONZE:
        return '#CD7F32';
      case RankTier.SILVER:
        return '#C0C0C0';
      case RankTier.GOLD:
        return '#FFD700';
      case RankTier.PLATINUM:
        return '#E5E4E2';
      case RankTier.DIAMOND:
        return '#B9F2FF';
      case RankTier.MASTER:
        return '#9966CC';
      case RankTier.GRANDMASTER:
        return '#FF1493';
      default:
        return '#9e9e9e';
    }
  };

  const getTierIcon = (tier: RankTier) => {
    switch (tier) {
      case RankTier.BRONZE:
      case RankTier.SILVER:
      case RankTier.GOLD:
        return <Star />;
      case RankTier.PLATINUM:
        return <WorkspacePremium />;
      case RankTier.DIAMOND:
        return <DiamondOutlined />;
      case RankTier.MASTER:
        return <MilitaryTech />;
      case RankTier.GRANDMASTER:
        return <Crown />;
      default:
        return <Star />;
    }
  };

  const getLeaderboardTypeIcon = (type: LeaderboardType) => {
    switch (type) {
      case LeaderboardType.OVERALL:
        return <EmojiEvents />;
      case LeaderboardType.SUBJECT_MATH:
        return <School />;
      case LeaderboardType.SUBJECT_SCIENCE:
        return <Science />;
      case LeaderboardType.SUBJECT_ENGLISH:
        return <MenuBook />;
      case LeaderboardType.SUBJECT_HISTORY:
        return <History />;
      case LeaderboardType.STREAK:
        return <LocalFireDepartment />;
      case LeaderboardType.ACHIEVEMENTS:
        return <WorkspacePremium />;
      case LeaderboardType.QUESTS_COMPLETED:
        return <Flag />;
      default:
        return <LeaderboardIcon />;
    }
  };

  const getRankMedal = (rank: number) => {
    if (rank === 1) return { icon: '🥇', color: '#FFD700' };
    if (rank === 2) return { icon: '🥈', color: '#C0C0C0' };
    if (rank === 3) return { icon: '🥉', color: '#CD7F32' };
    return null;
  };

  const getTrendIcon = (trend?: 'up' | 'down' | 'stable', positionChange?: number) => {
    if (!trend) return null;
    
    const iconProps = { fontSize: 'small' as const };
    
    switch (trend) {
      case 'up':
        return <TrendingUp {...iconProps} color="success" />;
      case 'down':
        return <TrendingDown {...iconProps} color="error" />;
      case 'stable':
        return <TrendingFlat {...iconProps} color="disabled" />;
    }
  };

  const handleRegisterCompetition = async (competition: CompetitionEvent) => {
    try {
      // Mock registration
      await new Promise(resolve => setTimeout(resolve, 500));
      setCompetitions(prev => prev.map(comp => 
        comp.id === competition.id 
          ? { ...comp, is_registered: true, participants_count: comp.participants_count + 1 }
          : comp
      ));
      setShowCompetitionDialog(false);
    } catch (error) {
      console.error('Failed to register for competition:', error);
    }
  };

  const renderLeaderboardEntry = (entry: LeaderboardEntry, index: number) => {
    const medal = getRankMedal(entry.rank);
    const isCurrentUser = entry.user_id === 'user2'; // Current user ID
    
    return (
      <motion.div
        key={entry.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
      >
        <Card
          sx={{
            mb: { xs: 1.5, sm: 2 },
            border: isCurrentUser ? '2px solid' : '1px solid',
            borderColor: isCurrentUser ? 'primary.main' : 'divider',
            backgroundColor: isCurrentUser ? 'primary.50' : 'background.paper',
            borderRadius: 2,
            ...componentStyles.card,
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: 4,
            },
            '&:active': {
              transform: 'scale(0.98)',
            }
          }}
        >
          <CardContent sx={{ 
            py: { xs: 1.5, sm: 2 },
            px: { xs: 2, sm: 3 }
          }}>
            {/* Mobile Layout */}
            <Box sx={{ display: { xs: 'block', md: 'none' } }}>
              <Box sx={{ ...flexBox.spaceBetween, mb: 1 }}>
                {/* Rank + Medal */}
                <Box sx={{ ...flexBox.center, gap: 1 }}>
                  {medal ? (
                    <Typography variant="h5" sx={{ color: medal.color }}>
                      {medal.icon}
                    </Typography>
                  ) : (
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      #{entry.rank}
                    </Typography>
                  )}
                </Box>
                
                {/* Trend */}
                <Box sx={{ ...flexBox.center, gap: 0.5 }}>
                  {getTrendIcon(entry.trend, entry.position_change)}
                  {entry.position_change !== undefined && entry.position_change !== 0 && (
                    <Typography
                      variant="caption"
                      sx={{
                        color: entry.trend === 'up' ? 'success.main' : entry.trend === 'down' ? 'error.main' : 'text.disabled',
                        fontWeight: 'bold',
                        fontSize: '0.75rem'
                      }}
                    >
                      {entry.position_change > 0 ? `+${entry.position_change}` : entry.position_change}
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* Character Info */}
              <Box sx={{ ...flexBox.center, gap: 1.5, mb: 1.5 }}>
                <Badge
                  badgeContent={entry.prestige_level || 0}
                  color="secondary"
                  sx={{
                    '& .MuiBadge-badge': {
                      backgroundColor: getTierColor(entry.tier),
                      color: 'white',
                      fontSize: '0.6rem',
                      minWidth: 16,
                      height: 16
                    },
                  }}
                >
                  <Avatar
                    src={entry.avatar_url}
                    sx={{
                      width: { xs: 40, sm: 48 },
                      height: { xs: 40, sm: 48 },
                      border: `2px solid ${getTierColor(entry.tier)}`,
                    }}
                  >
                    <Person />
                  </Avatar>
                </Badge>
                
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Box sx={{ ...flexBox.center, gap: 0.5, mb: 0.5 }}>
                    <Typography 
                      variant="subtitle1" 
                      sx={{ 
                        fontWeight: 'bold',
                        fontSize: '1rem',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {entry.character_name}
                    </Typography>
                    {entry.badge_icon && (
                      <span style={{ fontSize: '1rem' }}>{entry.badge_icon}</span>
                    )}
                    {isCurrentUser && (
                      <Chip label="You" size="small" color="primary" />
                    )}
                  </Box>
                  
                  <Box sx={{ ...flexBox.wrap, gap: 0.5 }}>
                    <Chip
                      icon={getTierIcon(entry.tier)}
                      label={entry.tier.charAt(0).toUpperCase() + entry.tier.slice(1)}
                      size="small"
                      sx={{
                        backgroundColor: getTierColor(entry.tier),
                        color: 'white',
                        fontSize: '0.7rem',
                        height: 24
                      }}
                    />
                    
                    {entry.title && (
                      <Chip
                        label={entry.title}
                        size="small"
                        sx={{
                          backgroundColor: entry.title_color || 'primary.main',
                          color: 'white',
                          fontSize: '0.7rem',
                          height: 24
                        }}
                      />
                    )}
                  </Box>
                </Box>
              </Box>

              {/* Stats Grid */}
              <GridContainer spacing={1}>
                <Box sx={{ flex: '1 1 50%' }}>
                  <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Level
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem' }}>
                      {entry.level}
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ flex: '1 1 50%' }}>
                  <Box sx={{ textAlign: 'center', p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Score
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold', fontSize: '1rem' }}>
                      {entry.score.toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </GridContainer>

              <Typography 
                variant="caption" 
                color="text.secondary" 
                sx={{ 
                  display: 'block', 
                  textAlign: 'center', 
                  mt: 1,
                  fontSize: '0.7rem'
                }}
              >
                {formatDistanceToNow(new Date(entry.last_active))} ago
              </Typography>
            </Box>

            {/* Desktop Layout */}
            <GridContainer alignItems="center" spacing={2} sx={{ display: { xs: 'none', md: 'flex' } }}>
              {/* Rank */}
              <Box sx={{ flex: '0 0 8.333%' }}>
                <Box sx={{ textAlign: 'center' }}>
                  {medal ? (
                    <Typography variant="h4" sx={{ color: medal.color }}>
                      {medal.icon}
                    </Typography>
                  ) : (
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      #{entry.rank}
                    </Typography>
                  )}
                </Box>
              </Box>

              {/* Character Info */}
              <Box sx={{ flex: '0 0 50%' }}>
                <Box sx={{ ...flexBox.center, gap: 2 }}>
                  <Badge
                    badgeContent={entry.prestige_level || 0}
                    color="secondary"
                    sx={{
                      '& .MuiBadge-badge': {
                        backgroundColor: getTierColor(entry.tier),
                        color: 'white',
                      },
                    }}
                  >
                    <Avatar
                      src={entry.avatar_url}
                      sx={{
                        width: 48,
                        height: 48,
                        border: `2px solid ${getTierColor(entry.tier)}`,
                      }}
                    >
                      <Person />
                    </Avatar>
                  </Badge>
                  
                  <Box>
                    <Box sx={{ ...flexBox.center, gap: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {entry.character_name}
                      </Typography>
                      {entry.badge_icon && (
                        <span style={{ fontSize: '1.2rem' }}>{entry.badge_icon}</span>
                      )}
                      {isCurrentUser && (
                        <Chip label="You" size="small" color="primary" />
                      )}
                    </Box>
                    
                    <Box sx={{ ...flexBox.center, gap: 1 }}>
                      <Chip
                        icon={getTierIcon(entry.tier)}
                        label={entry.tier.charAt(0).toUpperCase() + entry.tier.slice(1)}
                        size="small"
                        sx={{
                          backgroundColor: getTierColor(entry.tier),
                          color: 'white',
                        }}
                      />
                      
                      {entry.title && (
                        <Chip
                          label={entry.title}
                          size="small"
                          sx={{
                            backgroundColor: entry.title_color || 'primary.main',
                            color: 'white',
                          }}
                        />
                      )}
                    </Box>
                  </Box>
                </Box>
              </Box>

              {/* Stats */}
              <Box sx={{ flex: '0 0 25%' }}>
                <GridContainer spacing={1}>
                  <Box sx={{ flex: '1 1 50%' }}>
                    <Typography variant="body2" color="text.secondary">
                      Level
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {entry.level}
                    </Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 50%' }}>
                    <Typography variant="body2" color="text.secondary">
                      Score
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {entry.score.toLocaleString()}
                    </Typography>
                  </Box>
                </GridContainer>
              </Box>

              {/* Trend */}
              <Box sx={{ flex: '0 0 16.666%' }}>
                <Box sx={{ textAlign: 'right' }}>
                  <Box sx={{ ...flexBox.center, justifyContent: 'flex-end', gap: 0.5 }}>
                    {getTrendIcon(entry.trend, entry.position_change)}
                    {entry.position_change !== undefined && entry.position_change !== 0 && (
                      <Typography
                        variant="caption"
                        sx={{
                          color: entry.trend === 'up' ? 'success.main' : entry.trend === 'down' ? 'error.main' : 'text.disabled',
                          fontWeight: 'bold',
                        }}
                      >
                        {entry.position_change > 0 ? `+${entry.position_change}` : entry.position_change}
                      </Typography>
                    )}
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {formatDistanceToNow(new Date(entry.last_active))} ago
                  </Typography>
                </Box>
              </Box>
            </GridContainer>
          </CardContent>
        </Card>
      </motion.div>
    );
  };

  const renderMainLeaderboard = () => (
    <Box>
      {/* Leaderboard Type Selector */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <GridContainer spacing={2} alignItems="center">
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 50%' } }}>
            <FormControl fullWidth>
              <InputLabel>Leaderboard Type</InputLabel>
              <Select
                value={selectedLeaderboardType}
                onChange={(e) => setSelectedLeaderboardType(e.target.value as LeaderboardType)}
                startAdornment={getLeaderboardTypeIcon(selectedLeaderboardType)}
              >
                <MenuItem value={LeaderboardType.OVERALL}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <EmojiEvents /> Overall Ranking
                  </Box>
                </MenuItem>
                <MenuItem value={LeaderboardType.WEEKLY}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CalendarToday /> Weekly
                  </Box>
                </MenuItem>
                <MenuItem value={LeaderboardType.SUBJECT_MATH}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <School /> Mathematics
                  </Box>
                </MenuItem>
                <MenuItem value={LeaderboardType.SUBJECT_SCIENCE}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Science /> Science
                  </Box>
                </MenuItem>
                <MenuItem value={LeaderboardType.STREAK}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LocalFireDepartment /> Learning Streak
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Box>
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 50%' } }}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={loadLeaderboardData}
              >
                Refresh
              </Button>
            </Box>
          </Box>
        </GridContainer>
      </Paper>

      {/* Current User Rank Card */}
      {leaderboardData?.current_user_entry && (
        <Alert
          severity="info"
          sx={{
            mb: 3,
            '& .MuiAlert-message': { width: '100%' },
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'between', alignItems: 'center', width: '100%' }}>
            <Typography variant="h6">
              Your Current Rank: #{leaderboardData.current_user_rank}
            </Typography>
            <Chip
              label={`${leaderboardData.current_user_entry.score.toLocaleString()} points`}
              color="primary"
            />
          </Box>
        </Alert>
      )}

      {/* Season Info */}
      {leaderboardData?.season_info && (
        <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AutoAwesome />
            {leaderboardData.season_info.name}
          </Typography>
          <Typography variant="body1" sx={{ mb: 2 }}>
            Current season ends in {formatDistanceToNow(new Date(leaderboardData.season_info.end_date))}
          </Typography>
          <GridContainer spacing={2}>
            {leaderboardData.season_info.rewards.slice(0, 3).map((reward, index) => (
              <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 33.333%' } }} key={index}>
                <Card sx={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
                  <CardContent>
                    <Typography variant="subtitle2" sx={{ color: 'white' }}>
                      Rank {reward.rank_range.min}-{reward.rank_range.max}
                    </Typography>
                    <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                      {reward.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </GridContainer>
        </Paper>
      )}

      {/* Leaderboard Entries */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <LeaderboardIcon color="primary" />
          Top Performers
          <Chip label={`${leaderboardData?.total_participants.toLocaleString()} participants`} size="small" />
        </Typography>

        {leaderboardData?.entries.map((entry, index) => renderLeaderboardEntry(entry, index))}
      </Paper>
    </Box>
  );

  const renderCompetitions = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Timer color="primary" />
        Active Competitions
      </Typography>

      <GridContainer spacing={3}>
        {competitions.map((competition) => (
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 50%' } }} key={competition.id}>
            <Card sx={{ 
              ...componentStyles.card,
              height: '100%'
            }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Box sx={{ 
                  ...flexBox.spaceBetween, 
                  alignItems: 'start', 
                  mb: 2,
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: { xs: 1, sm: 0 }
                }}>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 'bold',
                      fontSize: { xs: '1.125rem', sm: '1.25rem' }
                    }}
                  >
                    {competition.name}
                  </Typography>
                  <Chip
                    label={competition.type.replace('_', ' ').toUpperCase()}
                    size="small"
                    color="primary"
                    variant="outlined"
                    sx={{
                      fontSize: { xs: '0.7rem', sm: '0.75rem' },
                      alignSelf: { xs: 'flex-start', sm: 'center' }
                    }}
                  />
                </Box>

                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  paragraph
                  sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                >
                  {competition.description}
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <Typography 
                    variant="subtitle2" 
                    gutterBottom
                    sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                  >
                    Schedule
                  </Typography>
                  <Typography 
                    variant="body2"
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    Starts: {format(new Date(competition.start_time), 'MMM d, HH:mm')}
                  </Typography>
                  <Typography 
                    variant="body2"
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    Ends: {format(new Date(competition.end_time), 'MMM d, HH:mm')}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography 
                    variant="subtitle2" 
                    gutterBottom
                    sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                  >
                    Participants
                  </Typography>
                  <Box sx={{ ...flexBox.center, gap: 1, justifyContent: 'flex-start' }}>
                    <Groups sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                    <Typography 
                      variant="body2"
                      sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                    >
                      {competition.participants_count}
                      {competition.max_participants && `/${competition.max_participants}`}
                    </Typography>
                  </Box>
                </Box>

                {competition.entry_requirements && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Requirements
                    </Typography>
                    {competition.entry_requirements.min_level && (
                      <Typography variant="body2">
                        Min Level: {competition.entry_requirements.min_level}
                      </Typography>
                    )}
                    {competition.entry_requirements.entry_fee && (
                      <Typography variant="body2">
                        Entry Fee: {Object.entries(competition.entry_requirements.entry_fee).map(([currency, amount]) => 
                          `${amount} ${currency}`
                        ).join(', ')}
                      </Typography>
                    )}
                  </Box>
                )}

                {competition.prizes.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Top Prize
                    </Typography>
                    <Typography variant="body2">
                      {competition.prizes[0].description}
                    </Typography>
                  </Box>
                )}
              </CardContent>

              <CardActions sx={{ p: { xs: 2, sm: 3 }, pt: 0 }}>
                {competition.is_registered ? (
                  <Button
                    fullWidth
                    variant="contained"
                    color="success"
                    startIcon={<CheckCircle />}
                    disabled
                    sx={{
                      ...touchStyles.touchTarget,
                      fontSize: { xs: '0.875rem', sm: '1rem' }
                    }}
                  >
                    Registered
                  </Button>
                ) : (
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={() => {
                      setSelectedCompetition(competition);
                      setShowCompetitionDialog(true);
                    }}
                    disabled={new Date() > new Date(competition.registration_deadline)}
                    sx={{
                      ...touchStyles.touchTarget,
                      fontSize: { xs: '0.875rem', sm: '1rem' }
                    }}
                  >
                    {new Date() > new Date(competition.registration_deadline) ? 'Registration Closed' : 'Register'}
                  </Button>
                )}
              </CardActions>
            </Card>
          </Box>
        ))}
      </GridContainer>
    </Box>
  );

  const renderGuilds = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Shield color="primary" />
        Top Guilds
      </Typography>

      <GridContainer spacing={3}>
        {guilds.map((guild) => (
          <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 50%' } }} key={guild.id}>
            <Card sx={{ 
              ...componentStyles.card,
              height: '100%'
            }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Box sx={{ 
                  ...flexBox.spaceBetween, 
                  alignItems: 'start', 
                  mb: 2,
                  flexDirection: { xs: 'column', sm: 'row' },
                  gap: { xs: 1, sm: 0 }
                }}>
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 'bold',
                      fontSize: { xs: '1.125rem', sm: '1.25rem' }
                    }}
                  >
                    {guild.name}
                  </Typography>
                  <Chip
                    label={`Rank #${guild.rank}`}
                    size="small"
                    color="primary"
                    sx={{
                      fontSize: { xs: '0.7rem', sm: '0.75rem' },
                      alignSelf: { xs: 'flex-start', sm: 'center' }
                    }}
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" paragraph>
                  {guild.description}
                </Typography>

                <GridContainer spacing={2} sx={{ mb: 2 }}>
                  <Box sx={{ flex: '1 1 50%' }}>
                    <Typography variant="subtitle2">Level</Typography>
                    <Typography variant="h6">{guild.guild_level}</Typography>
                  </Box>
                  <Box sx={{ flex: '1 1 50%' }}>
                    <Typography variant="subtitle2">Members</Typography>
                    <Typography variant="h6">{guild.member_count}/{guild.max_members}</Typography>
                  </Box>
                </GridContainer>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Guild Leader
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar
                      src={guild.leader.avatar_url}
                      sx={{ width: 32, height: 32 }}
                    >
                      <Person />
                    </Avatar>
                    <Typography variant="body2">
                      {guild.leader.character_name}
                    </Typography>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Guild Perks
                  </Typography>
                  <List dense>
                    {guild.perks.slice(0, 2).map((perk, index) => (
                      <ListItem key={index} sx={{ px: 0 }}>
                        <ListItemIcon sx={{ minWidth: 20 }}>
                          <CheckCircle fontSize="small" color="success" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={perk}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              </CardContent>

              <CardActions>
                <Button
                  fullWidth
                  variant="contained"
                  startIcon={<PersonAdd />}
                  onClick={() => {/* Handle guild join */}}
                >
                  Apply to Join
                </Button>
              </CardActions>
            </Card>
          </Box>
        ))}
      </GridContainer>
    </Box>
  );

  const renderFriendsLeaderboard = () => (
    <Box>
      {friendsLeaderboard && (
        <>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Groups color="primary" />
              Friends Comparison
            </Typography>
            
            <GridContainer spacing={3} sx={{ textAlign: 'center' }}>
              <Box sx={{ flex: '1 1 33.333%' }}>
                <Typography variant="h4" color="success.main">
                  {friendsLeaderboard.comparison_stats.ahead_of_user}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Friends Behind You
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 33.333%' }}>
                <Typography variant="h4" color="primary.main">
                  {friendsLeaderboard.user_position}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Your Position
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 33.333%' }}>
                <Typography variant="h4" color="warning.main">
                  {friendsLeaderboard.comparison_stats.ahead_of_user}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Friends Ahead
                </Typography>
              </Box>
            </GridContainer>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Friends Ranking
            </Typography>
            {friendsLeaderboard.friends.map((entry, index) => renderLeaderboardEntry(entry, index))}
          </Paper>
        </>
      )}
    </Box>
  );

  return (
    <Container 
      maxWidth="lg" 
      sx={{ 
        ...containerStyles.responsivePadding,
        mt: { xs: 2, sm: 3, md: 4 }, 
        mb: { xs: 2, sm: 3, md: 4 }
      }}
    >
      {/* Header */}
      <Box sx={{ 
        mb: { xs: 2, sm: 3 },
        textAlign: { xs: 'center', sm: 'left' }
      }}>
        <Typography 
          variant="h4" 
          gutterBottom 
          sx={{ 
            ...flexBox.center, 
            gap: 1,
            justifyContent: { xs: 'center', sm: 'flex-start' },
            fontSize: { xs: '1.5rem', sm: '2rem' }
          }}
        >
          <EmojiEvents color="primary" />
          Leaderboard & Rankings
        </Typography>
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
        >
          Compete with other learners and climb the rankings
        </Typography>
      </Box>

      {/* Main Tabs */}
      <Box sx={{ 
        borderBottom: 1, 
        borderColor: 'divider', 
        mb: { xs: 2, sm: 3 }
      }}>
        <Tabs 
          value={tabValue} 
          onChange={(_, value) => setTabValue(value)}
          variant="scrollable"
          scrollButtons="auto"
          allowScrollButtonsMobile
          sx={{
            '& .MuiTab-root': {
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              ...touchStyles.touchTarget,
              minWidth: { xs: 80, sm: 120 }
            }
          }}
        >
          <Tab 
            label="Leaderboard" 
            icon={<LeaderboardIcon />} 
            iconPosition="start"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />
          <Tab 
            icon={<LeaderboardIcon />}
            sx={{ display: { xs: 'flex', sm: 'none' }, minWidth: 48 }}
          />
          
          <Tab 
            label="Competitions" 
            icon={<Timer />} 
            iconPosition="start"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />
          <Tab 
            icon={<Timer />}
            sx={{ display: { xs: 'flex', sm: 'none' }, minWidth: 48 }}
          />
          
          <Tab 
            label="Guilds" 
            icon={<Shield />} 
            iconPosition="start"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />
          <Tab 
            icon={<Shield />}
            sx={{ display: { xs: 'flex', sm: 'none' }, minWidth: 48 }}
          />
          
          <Tab 
            label="Friends" 
            icon={<Groups />} 
            iconPosition="start"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />
          <Tab 
            icon={<Groups />}
            sx={{ display: { xs: 'flex', sm: 'none' }, minWidth: 48 }}
          />
        </Tabs>
      </Box>

      <LoadingErrorWrapper
        loading={loading}
        error={error}
        onRetry={handleRetry}
        loadingComponent={
          <GridContainer spacing={3}>
            {[...Array(6)].map((_, i) => (
              <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 50%', md: '1 1 33.333%' } }} key={i}>
                <Skeleton variant="rectangular" height={200} />
              </Box>
            ))}
          </GridContainer>
        }
      >
        <TabPanel value={tabValue} index={0}>
          {renderMainLeaderboard()}
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          {renderCompetitions()}
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          {renderGuilds()}
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          {renderFriendsLeaderboard()}
        </TabPanel>
      </LoadingErrorWrapper>

      {/* Competition Registration Dialog */}
      <Dialog
        open={showCompetitionDialog}
        onClose={() => setShowCompetitionDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        {selectedCompetition && (
          <>
            <DialogTitle>
              Register for Competition
            </DialogTitle>
            <DialogContent>
              <Typography variant="h6" gutterBottom>
                {selectedCompetition.name}
              </Typography>
              <Typography variant="body1" paragraph>
                {selectedCompetition.description}
              </Typography>
              
              {selectedCompetition.entry_requirements?.entry_fee && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    Entry Fee Required: {Object.entries(selectedCompetition.entry_requirements.entry_fee).map(([currency, amount]) => 
                      `${amount} ${currency}`
                    ).join(', ')}
                  </Typography>
                </Alert>
              )}

              <Typography variant="body2" color="text.secondary">
                By registering, you agree to participate in the competition according to the rules and schedule.
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setShowCompetitionDialog(false)}>
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={() => handleRegisterCompetition(selectedCompetition)}
              >
                Register
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Container>
  );
};

export default LeaderboardPage;
