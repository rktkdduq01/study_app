import React, { useState, useEffect, useMemo } from 'react';
import { GridContainer } from '../../components/layout';
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
  Badge,
  Tab,
  Tabs,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  InputAdornment,
} from '@mui/material';
import StatsCard from '../../components/common/StatsCard';
import LoadingSkeleton from '../../components/common/LoadingSkeleton';
import {
  Person,
  PersonAdd,
  Group,
  Chat,
  Search,
  FilterList,
  MoreVert,
  Check,
  Close,
  EmojiEvents,
  TrendingUp,
  Star,
  FiberManualRecord,
  Circle,
  Refresh,
  AutoAwesome,
  Celebration,
  Psychology,
  Schedule,
  ExpandMore,
  VisibilityOff,
  ThumbUp,
  ThumbUpOutlined,
  Comment,
  Share,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import {
  fetchFriends,
  fetchFriendRequests,
  fetchFriendSuggestions,
  fetchFriendActivities,
  sendFriendRequest,
  respondToFriendRequest,
  likeFriendActivity,
  setSelectedTab,
  setSearchQuery,
  setFriendFilters,
  dismissSuggestion,
  removeFriend,
  updateActivityLike,
} from '../../store/slices/friendSlice';
import {
  Friend,
  FriendRequest,
  FriendSuggestion,
  FriendActivity,
  FriendStatus,
  OnlineStatus,
  ActivityType,
  FriendSearchFilters,
} from '../../types/friend';
import { flexBox, touchStyles } from '../../utils/responsive';

const Friends: React.FC = () => {
  const dispatch = useAppDispatch();
  const {
    friends,
    friendsLoading,
    friendsError,
    sentRequests,
    receivedRequests,
    requestsLoading,
    suggestions,
    suggestionsLoading,
    activities,
    activitiesLoading,
    selectedTab,
    searchQuery,
    friendFilters,
    onlineFriends,
  } = useAppSelector((state) => state.friends);

  const [friendRequestDialog, setFriendRequestDialog] = useState<{
    open: boolean;
    userId?: string;
    userName?: string;
  }>({ open: false });
  const [requestMessage, setRequestMessage] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Load data on component mount
  useEffect(() => {
    dispatch(fetchFriends({}));
    dispatch(fetchFriendRequests());
    dispatch(fetchFriendSuggestions());
    dispatch(fetchFriendActivities({}));
  }, [dispatch]);

  // Filter friends based on search and filters
  const filteredFriends = useMemo(() => {
    let filtered = friends;

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(friend =>
        friend.friend_character.name.toLowerCase().includes(query) ||
        friend.friend_character.class.toLowerCase().includes(query) ||
        friend.friend_character.title?.toLowerCase().includes(query)
      );
    }

    // Online status filter
    if (friendFilters.online_status) {
      filtered = filtered.filter(friend => friend.online_status === friendFilters.online_status);
    }

    // Activity type filter
    if (friendFilters.activity_type) {
      filtered = filtered.filter(friend => friend.current_activity === friendFilters.activity_type);
    }

    // Level range filter
    if (friendFilters.level_range) {
      filtered = filtered.filter(friend => 
        friend.friend_character.total_level >= (friendFilters.level_range?.min || 0) &&
        friend.friend_character.total_level <= (friendFilters.level_range?.max || 999)
      );
    }

    return filtered;
  }, [friends, searchQuery, friendFilters]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: string) => {
    dispatch(setSelectedTab(newValue as any));
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setSearchQuery(event.target.value));
  };

  const handleSendFriendRequest = async () => {
    if (friendRequestDialog.userId) {
      try {
        await dispatch(sendFriendRequest({
          userId: friendRequestDialog.userId,
          message: requestMessage.trim() || undefined
        }));
        setFriendRequestDialog({ open: false });
        setRequestMessage('');
      } catch (error) {
        console.error('Failed to send friend request:', error);
      }
    }
  };

  const handleRespondToRequest = async (requestId: string, accept: boolean) => {
    try {
      await dispatch(respondToFriendRequest({ requestId, accept }));
    } catch (error) {
      console.error('Failed to respond to friend request:', error);
    }
  };

  const handleLikeActivity = async (activityId: string, currentlyLiked: boolean) => {
    try {
      if (currentlyLiked) {
        // Unlike logic would go here
        dispatch(updateActivityLike({ activityId, liked: false }));
      } else {
        await dispatch(likeFriendActivity(activityId));
      }
    } catch (error) {
      console.error('Failed to like activity:', error);
    }
  };

  const getOnlineStatusIcon = (status: OnlineStatus) => {
    const statusConfig = {
      [OnlineStatus.ONLINE]: { color: '#4CAF50', icon: <Circle sx={{ fontSize: 12 }} /> },
      [OnlineStatus.AWAY]: { color: '#FF9800', icon: <Circle sx={{ fontSize: 12 }} /> },
      [OnlineStatus.BUSY]: { color: '#F44336', icon: <Circle sx={{ fontSize: 12 }} /> },
      [OnlineStatus.OFFLINE]: { color: '#9E9E9E', icon: <Circle sx={{ fontSize: 12 }} /> },
      [OnlineStatus.INVISIBLE]: { color: '#9E9E9E', icon: <VisibilityOff sx={{ fontSize: 12 }} /> },
    };

    const config = statusConfig[status];
    return (
      <Box sx={{ ...flexBox.alignCenter, gap: 0.5 }}>
        <Box sx={{ color: config.color }}>{config.icon}</Box>
        <Typography variant="caption" sx={{ color: config.color, textTransform: 'capitalize' }}>
          {status === OnlineStatus.ONLINE ? '온라인' :
           status === OnlineStatus.AWAY ? '자리비움' :
           status === OnlineStatus.BUSY ? '바쁨' :
           status === OnlineStatus.OFFLINE ? '오프라인' : '숨김'}
        </Typography>
      </Box>
    );
  };

  const getActivityIcon = (activity?: ActivityType) => {
    if (!activity) return null;

    const activityConfig = {
      [ActivityType.STUDYING]: { icon: <Psychology />, color: '#9C27B0', label: '공부 중' },
      [ActivityType.QUEST]: { icon: <EmojiEvents />, color: '#FF5722', label: '퀘스트 중' },
      [ActivityType.SHOPPING]: { icon: <Star />, color: '#4CAF50', label: '쇼핑 중' },
      [ActivityType.ACHIEVEMENT]: { icon: <TrendingUp />, color: '#FFD700', label: '업적 달성' },
      [ActivityType.IDLE]: { icon: <Schedule />, color: '#9E9E9E', label: '대기 중' },
      [ActivityType.GAMING]: { icon: <Celebration />, color: '#E91E63', label: '게임 중' },
    };

    const config = activityConfig[activity];
    return (
      <Chip
        icon={config.icon}
        label={config.label}
        size="small"
        sx={{
          bgcolor: config.color,
          color: 'white',
          fontSize: '0.7rem',
          height: 20,
        }}
      />
    );
  };

  const renderFriendCard = (friend: Friend) => (
    <motion.div
      key={friend.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        sx={{
          height: '100%',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          border: onlineFriends.has(friend.friend_user_id) ? '2px solid #4CAF50' : 'none',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: 6,
          },
        }}
      >
        <CardContent sx={{ pb: 1 }}>
          <Box sx={{ ...flexBox.spaceBetween, alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ ...flexBox.alignCenter, gap: 2 }}>
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                badgeContent={
                  <Box
                    sx={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      bgcolor: friend.online_status === OnlineStatus.ONLINE ? '#4CAF50' : '#9E9E9E',
                      border: '2px solid white',
                    }}
                  />
                }
              >
                <Avatar
                  src={friend.friend_character.avatar_url}
                  sx={{ width: 56, height: 56 }}
                >
                  <Person />
                </Avatar>
              </Badge>
              
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {friend.friend_character.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Lv.{friend.friend_character.total_level} {friend.friend_character.class}
                </Typography>
                {friend.friend_character.title && (
                  <Chip
                    label={friend.friend_character.title}
                    size="small"
                    sx={{ mt: 0.5, fontSize: '0.7rem' }}
                  />
                )}
              </Box>
            </Box>
            
            <IconButton size="small" sx={{ ...touchStyles.touchTarget }}>
              <MoreVert />
            </IconButton>
          </Box>

          <Box sx={{ mb: 2 }}>
            {getOnlineStatusIcon(friend.online_status)}
            {friend.current_activity && friend.show_activity && (
              <Box sx={{ mt: 1 }}>
                {getActivityIcon(friend.current_activity)}
                {friend.activity_details && (
                  <Typography variant="caption" sx={{ display: 'block', mt: 0.5, color: 'text.secondary' }}>
                    {friend.activity_details}
                  </Typography>
                )}
              </Box>
            )}
          </Box>

          <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                친구점수: {friend.friendship_points.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                공통 친구: {friend.mutual_friends_count}명
              </Typography>
            </Box>
            
            <Typography variant="caption" color="text.secondary">
              {friend.last_seen && formatDistanceToNow(new Date(friend.last_seen), {
                addSuffix: true,
                locale: ko,
              })}
            </Typography>
          </Box>
        </CardContent>
        
        <CardActions sx={{ p: 2, pt: 0 }}>
          <Button
            size="small"
            startIcon={<Chat />}
            variant="outlined"
            sx={{ ...touchStyles.touchTarget }}
          >
            채팅
          </Button>
          <Button
            size="small"
            startIcon={<PersonAdd />}
            variant="outlined"
            sx={{ ...touchStyles.touchTarget }}
          >
            프로필
          </Button>
        </CardActions>
      </Card>
    </motion.div>
  );

  const renderFriendRequest = (request: FriendRequest) => (
    <Card key={request.id} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
          <Box sx={{ ...flexBox.alignCenter, gap: 2 }}>
            <Avatar src={request.from_character.avatar_url} sx={{ width: 48, height: 48 }}>
              <Person />
            </Avatar>
            
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {request.from_character.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Lv.{request.from_character.total_level} {request.from_character.class}
              </Typography>
              {request.mutual_friends_count > 0 && (
                <Typography variant="caption" color="text.secondary">
                  공통 친구 {request.mutual_friends_count}명
                </Typography>
              )}
            </Box>
          </Box>
          
          <Box sx={{ ...flexBox.alignCenter, gap: 1 }}>
            <Button
              size="small"
              variant="contained"
              color="success"
              startIcon={<Check />}
              onClick={() => handleRespondToRequest(request.id, true)}
              sx={{ ...touchStyles.touchTarget }}
            >
              수락
            </Button>
            <Button
              size="small"
              variant="outlined"
              color="error"
              startIcon={<Close />}
              onClick={() => handleRespondToRequest(request.id, false)}
              sx={{ ...touchStyles.touchTarget }}
            >
              거절
            </Button>
          </Box>
        </Box>
        
        {request.message && (
          <Box sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100', borderRadius: 1 }}>
            <Typography variant="body2">
              "{request.message}"
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderFriendSuggestion = (suggestion: FriendSuggestion) => (
    <Card key={suggestion.id} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
          <Box sx={{ ...flexBox.alignCenter, gap: 2 }}>
            <Avatar src={suggestion.character.avatar_url} sx={{ width: 48, height: 48 }}>
              <Person />
            </Avatar>
            
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {suggestion.character.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Lv.{suggestion.character.total_level} {suggestion.character.class}
              </Typography>
              <Chip
                label={
                  suggestion.reason === 'mutual_friends' ? '공통 친구' :
                  suggestion.reason === 'same_school' ? '같은 학교' :
                  suggestion.reason === 'similar_interests' ? '비슷한 관심사' :
                  suggestion.reason === 'nearby' ? '근처 위치' : '추천'
                }
                size="small"
                sx={{ mt: 0.5, fontSize: '0.7rem' }}
              />
            </Box>
          </Box>
          
          <Box sx={{ ...flexBox.alignCenter, gap: 1 }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<PersonAdd />}
              onClick={() => setFriendRequestDialog({
                open: true,
                userId: suggestion.suggested_user_id,
                userName: suggestion.character.name
              })}
              sx={{ ...touchStyles.touchTarget }}
            >
              친구 추가
            </Button>
            <IconButton
              size="small"
              onClick={() => dispatch(dismissSuggestion(suggestion.id))}
              sx={{ ...touchStyles.touchTarget }}
            >
              <Close />
            </IconButton>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const renderActivity = (activity: FriendActivity) => (
    <Card key={activity.id} sx={{ mb: 2 }}>
      <CardContent>
        <Box sx={{ ...flexBox.spaceBetween, alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ ...flexBox.alignCenter, gap: 2 }}>
            <Avatar sx={{ width: 40, height: 40 }}>
              <Person />
            </Avatar>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {activity.activity_data.title}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatDistanceToNow(new Date(activity.created_at), {
                  addSuffix: true,
                  locale: ko,
                })}
              </Typography>
            </Box>
          </Box>
          
          <IconButton size="small" sx={{ ...touchStyles.touchTarget }}>
            <MoreVert />
          </IconButton>
        </Box>
        
        <Typography variant="body2" sx={{ mb: 2 }}>
          {activity.activity_data.description}
        </Typography>
        
        {activity.activity_data.image_url && (
          <Box
            component="img"
            src={activity.activity_data.image_url}
            sx={{
              width: '100%',
              maxHeight: 200,
              objectFit: 'cover',
              borderRadius: 1,
              mb: 2,
            }}
          />
        )}
        
        <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
          <Box sx={{ ...flexBox.alignCenter, gap: 2 }}>
            <Button
              size="small"
              startIcon={activity.user_liked ? <ThumbUp /> : <ThumbUpOutlined />}
              color={activity.user_liked ? 'primary' : 'inherit'}
              onClick={() => handleLikeActivity(activity.id, activity.user_liked)}
              sx={{ ...touchStyles.touchTarget }}
            >
              {activity.likes_count}
            </Button>
            <Button
              size="small"
              startIcon={<Comment />}
              sx={{ ...touchStyles.touchTarget }}
            >
              {activity.comments_count}
            </Button>
            <Button
              size="small"
              startIcon={<Share />}
              sx={{ ...touchStyles.touchTarget }}
            >
              공유
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const renderFilters = () => (
    <Accordion expanded={showFilters} onChange={() => setShowFilters(!showFilters)}>
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Typography variant="subtitle2">필터 옵션</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <GridContainer spacing={2}>
          <Box sx={{ width: { xs: '100%', sm: '50%' }, px: 1 }}>
            <FormControl fullWidth size="small">
              <InputLabel>온라인 상태</InputLabel>
              <Select
                value={friendFilters.online_status || ''}
                label="온라인 상태"
                onChange={(e) => dispatch(setFriendFilters({
                  ...friendFilters,
                  online_status: e.target.value as OnlineStatus || undefined
                }))}
              >
                <MenuItem value="">전체</MenuItem>
                <MenuItem value={OnlineStatus.ONLINE}>온라인</MenuItem>
                <MenuItem value={OnlineStatus.AWAY}>자리비움</MenuItem>
                <MenuItem value={OnlineStatus.BUSY}>바쁨</MenuItem>
                <MenuItem value={OnlineStatus.OFFLINE}>오프라인</MenuItem>
              </Select>
            </FormControl>
          </Box>
          
          <Box sx={{ width: { xs: '100%', sm: '50%' }, px: 1 }}>
            <FormControl fullWidth size="small">
              <InputLabel>활동 상태</InputLabel>
              <Select
                value={friendFilters.activity_type || ''}
                label="활동 상태"
                onChange={(e) => dispatch(setFriendFilters({
                  ...friendFilters,
                  activity_type: e.target.value as ActivityType || undefined
                }))}
              >
                <MenuItem value="">전체</MenuItem>
                <MenuItem value={ActivityType.STUDYING}>공부 중</MenuItem>
                <MenuItem value={ActivityType.QUEST}>퀘스트 중</MenuItem>
                <MenuItem value={ActivityType.SHOPPING}>쇼핑 중</MenuItem>
                <MenuItem value={ActivityType.GAMING}>게임 중</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </GridContainer>
      </AccordionDetails>
    </Accordion>
  );

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
          친구
        </Typography>
        <Typography variant="body1" color="text.secondary">
          친구들과 함께 공부하고 성장하세요
        </Typography>
      </Box>

      {/* Stats Cards */}
      <GridContainer spacing={3} sx={{ mb: 3 }}>
        <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1.5 }}>
          <StatsCard 
            title="전체 친구" 
            value={friends.length} 
            icon={<Person />} 
            color="primary.main"
          />
        </Box>
        <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1.5 }}>
          <StatsCard 
            title="온라인 친구" 
            value={onlineFriends.size} 
            icon={<FiberManualRecord />} 
            color="success.main"
          />
        </Box>
        <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1.5 }}>
          <StatsCard 
            title="친구 요청" 
            value={receivedRequests.length} 
            icon={<PersonAdd />} 
            color="warning.main"
          />
        </Box>
        <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1.5 }}>
          <StatsCard 
            title="추천 친구" 
            value={suggestions.length} 
            icon={<AutoAwesome />} 
            color="info.main"
          />
        </Box>
      </GridContainer>

      {/* Search and Controls */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center', mb: 2 }}>
          <TextField
            placeholder="친구 검색..."
            value={searchQuery}
            onChange={handleSearchChange}
            size="small"
            sx={{ width: { xs: '100%', sm: 300 } }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
          
          <Box sx={{ ...flexBox.alignCenter, gap: 1 }}>
            <ToggleButtonGroup
              value={viewMode}
              exclusive
              onChange={(e, newMode) => newMode && setViewMode(newMode)}
              size="small"
            >
              <ToggleButton value="grid" sx={{ ...touchStyles.touchTarget }}>
                <Group />
              </ToggleButton>
              <ToggleButton value="list" sx={{ ...touchStyles.touchTarget }}>
                <Group />
              </ToggleButton>
            </ToggleButtonGroup>
            
            <IconButton
              onClick={() => setShowFilters(!showFilters)}
              sx={{ ...touchStyles.touchTarget }}
            >
              <FilterList />
            </IconButton>
            
            <IconButton
              onClick={() => dispatch(fetchFriends({}))}
              disabled={friendsLoading}
              sx={{ ...touchStyles.touchTarget }}
            >
              <Refresh />
            </IconButton>
          </Box>
        </Box>
        
        {renderFilters()}
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={selectedTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab
            label={`친구 목록 (${filteredFriends.length})`}
            value="friends"
            sx={{ ...touchStyles.touchTarget }}
          />
          <Tab
            label={`친구 요청 (${receivedRequests.length})`}
            value="requests"
            sx={{ ...touchStyles.touchTarget }}
          />
          <Tab
            label={`추천 친구 (${suggestions.length})`}
            value="suggestions"
            sx={{ ...touchStyles.touchTarget }}
          />
          <Tab
            label="친구 활동"
            value="activities"
            sx={{ ...touchStyles.touchTarget }}
          />
        </Tabs>
      </Paper>

      {/* Content */}
      <Box>
        {selectedTab === 'friends' && (
          <>
            {friendsLoading && friends.length === 0 ? (
              <LoadingSkeleton 
                type="card" 
                count={8} 
                columns={{ xs: 1, sm: 2, md: 3, lg: 4 }}
              />
            ) : filteredFriends.length > 0 ? (
              <GridContainer spacing={3}>
                <AnimatePresence>
                  {filteredFriends.map((friend) => (
                    <Box sx={{ width: { xs: '100%', sm: '50%', md: '33.333%', lg: '25%' }, px: 1.5, mb: 3 }} key={friend.id}>
                      {renderFriendCard(friend)}
                    </Box>
                  ))}
                </AnimatePresence>
              </GridContainer>
            ) : (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <Person sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  {searchQuery ? '검색 결과가 없습니다' : '아직 친구가 없습니다'}
                </Typography>
                <Typography variant="body2" color="text.disabled" sx={{ mt: 1 }}>
                  {searchQuery ? '다른 키워드로 검색해보세요' : '추천 친구에서 새로운 친구를 찾아보세요!'}
                </Typography>
              </Box>
            )}
          </>
        )}

        {selectedTab === 'requests' && (
          <Box>
            {requestsLoading ? (
              <CircularProgress />
            ) : receivedRequests.length > 0 ? (
              receivedRequests.map(renderFriendRequest)
            ) : (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <PersonAdd sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  새로운 친구 요청이 없습니다
                </Typography>
              </Box>
            )}
          </Box>
        )}

        {selectedTab === 'suggestions' && (
          <Box>
            {suggestionsLoading ? (
              <CircularProgress />
            ) : suggestions.length > 0 ? (
              suggestions.map(renderFriendSuggestion)
            ) : (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <AutoAwesome sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  추천할 친구가 없습니다
                </Typography>
              </Box>
            )}
          </Box>
        )}

        {selectedTab === 'activities' && (
          <Box>
            {activitiesLoading ? (
              <CircularProgress />
            ) : activities.length > 0 ? (
              activities.map(renderActivity)
            ) : (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <TrendingUp sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  친구 활동이 없습니다
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </Box>

      {/* Friend Request Dialog */}
      <Dialog
        open={friendRequestDialog.open}
        onClose={() => setFriendRequestDialog({ open: false })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {friendRequestDialog.userName}님에게 친구 요청 보내기
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={3}
            placeholder="친구 요청과 함께 보낼 메시지를 입력하세요 (선택사항)"
            value={requestMessage}
            onChange={(e) => setRequestMessage(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setFriendRequestDialog({ open: false })}
            sx={{ ...touchStyles.touchTarget }}
          >
            취소
          </Button>
          <Button
            variant="contained"
            onClick={handleSendFriendRequest}
            sx={{ ...touchStyles.touchTarget }}
          >
            요청 보내기
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Friends;
