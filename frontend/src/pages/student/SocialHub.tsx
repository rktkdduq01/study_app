import React, { useState, useEffect } from 'react';
import { GridContainer } from '../../components/layout';
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  Avatar,
  IconButton,
  Badge,
  Tab,
  Tabs,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Alert,
  LinearProgress,
} from '@mui/material';
import StatsCard from '../../components/common/StatsCard';
import {
  Person,
  Chat,
  School,
  PersonAdd,
  GroupAdd,
  QuestionAnswer,
  TrendingUp,
  Star,
  Groups,
  LocalFireDepartment,
  FiberManualRecord,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import {
  fetchFriends,
  fetchFriendRequests,
  fetchFriendSuggestions,
  fetchFriendActivities,
  fetchChatRooms,
  fetchGuilds,
  fetchStudyGroups,
  fetchFriendshipStats,
  setSelectedTab,
  setChatPanelOpen,
  setFriendsPanelOpen,
} from '../../store/slices/friendSlice';
import { flexBox, touchStyles } from '../../utils/responsive';
import ChatPanel from '../../components/chat/ChatPanel';
import Friends from './Friends';

const SocialHub: React.FC = () => {
  const dispatch = useAppDispatch();
  const {
    friends,
    friendsLoading,
    receivedRequests,
    suggestions,
    activities,
    chatRooms,
    myGuilds,
    myStudyGroups,
    friendshipStats,
    onlineFriends,
    selectedTab,
    friendsPanelOpen,
    chatPanelOpen,
  } = useAppSelector((state) => state.friends);

  const [speedDialOpen, setSpeedDialOpen] = useState(false);
  const [selectedQuickTab, setSelectedQuickTab] = useState(0);

  // Load initial data
  useEffect(() => {
    dispatch(fetchFriends({}));
    dispatch(fetchFriendRequests());
    dispatch(fetchFriendSuggestions());
    dispatch(fetchFriendActivities({}));
    dispatch(fetchChatRooms());
    dispatch(fetchGuilds());
    dispatch(fetchStudyGroups());
    dispatch(fetchFriendshipStats());
  }, [dispatch]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedQuickTab(newValue);
  };

  const handleOpenFriends = () => {
    dispatch(setSelectedTab('friends'));
    dispatch(setFriendsPanelOpen(true));
  };

  const handleOpenChat = () => {
    dispatch(setChatPanelOpen(true));
  };

  const speedDialActions = [
    {
      icon: <PersonAdd />,
      name: '친구 추가',
      onClick: () => {
        dispatch(setSelectedTab('suggestions'));
        dispatch(setFriendsPanelOpen(true));
      }
    },
    {
      icon: <GroupAdd />,
      name: '그룹 생성',
      onClick: () => {
        // Handle group creation
      }
    },
    {
      icon: <QuestionAnswer />,
      name: '새 채팅',
      onClick: handleOpenChat
    },
    {
      icon: <School />,
      name: '스터디 그룹',
      onClick: () => {
        // Handle study group creation
      }
    }
  ];


  const renderOnlineFriends = () => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2, ...flexBox.alignCenter, gap: 1 }}>
          <FiberManualRecord sx={{ color: '#4CAF50' }} />
          온라인 친구 ({onlineFriends.size})
        </Typography>
        
        {friends.filter(f => onlineFriends.has(f.friend_user_id)).slice(0, 5).map((friend) => (
          <Box key={friend.id} sx={{ ...flexBox.alignCenter, gap: 2, mb: 2 }}>
            <Badge
              overlap="circular"
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              badgeContent={<Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#4CAF50', border: '2px solid white' }} />}
            >
              <Avatar src={friend.friend_character.avatar_url} sx={{ width: 40, height: 40 }}>
                <Person />
              </Avatar>
            </Badge>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {friend.friend_character.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {friend.current_activity && friend.show_activity
                  ? friend.activity_details || friend.current_activity
                  : '온라인'
                }
              </Typography>
            </Box>
            <IconButton size="small" onClick={handleOpenChat} sx={{ ...touchStyles.touchTarget }}>
              <Chat />
            </IconButton>
          </Box>
        ))}
        
        {friends.filter(f => onlineFriends.has(f.friend_user_id)).length > 5 && (
          <Button
            fullWidth
            variant="outlined"
            size="small"
            onClick={handleOpenFriends}
            sx={{ mt: 1, ...touchStyles.touchTarget }}
          >
            더 보기 (+{friends.filter(f => onlineFriends.has(f.friend_user_id)).length - 5})
          </Button>
        )}
        
        {onlineFriends.size === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Person sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              현재 온라인인 친구가 없습니다
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderRecentActivities = () => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2, ...flexBox.alignCenter, gap: 1 }}>
          <TrendingUp />
          최근 활동
        </Typography>
        
        {activities.slice(0, 4).map((activity) => (
          <Box key={activity.id} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
            <Box sx={{ ...flexBox.alignCenter, gap: 2, mb: 1 }}>
              <Avatar sx={{ width: 32, height: 32 }}>
                <Person />
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {activity.activity_data.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {activity.activity_data.description}
                </Typography>
              </Box>
            </Box>
            
            <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
              <Box sx={{ ...flexBox.alignCenter, gap: 1 }}>
                <IconButton size="small" sx={{ ...touchStyles.touchTarget }}>
                  <Star />
                </IconButton>
                <Typography variant="caption">{activity.likes_count}</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                방금 전
              </Typography>
            </Box>
          </Box>
        ))}
        
        <Button
          fullWidth
          variant="outlined"
          size="small"
          onClick={() => {
            dispatch(setSelectedTab('activities'));
            dispatch(setFriendsPanelOpen(true));
          }}
          sx={{ ...touchStyles.touchTarget }}
        >
          모든 활동 보기
        </Button>
      </CardContent>
    </Card>
  );

  const renderMyGroups = () => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" sx={{ mb: 2, ...flexBox.alignCenter, gap: 1 }}>
          <Groups />
          내 그룹
        </Typography>
        
        <Tabs
          value={selectedQuickTab}
          onChange={handleTabChange}
          variant="fullWidth"
          sx={{ mb: 2 }}
        >
          <Tab label="길드" sx={{ ...touchStyles.touchTarget }} />
          <Tab label="스터디" sx={{ ...touchStyles.touchTarget }} />
        </Tabs>
        
        {selectedQuickTab === 0 && (
          <Box>
            {myGuilds.slice(0, 3).map((guild) => (
              <Box key={guild.id} sx={{ ...flexBox.alignCenter, gap: 2, mb: 2 }}>
                <Avatar src={guild.avatar_url} sx={{ width: 40, height: 40 }}>
                  <Groups />
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {guild.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {guild.members_count}명 • Lv.{guild.level}
                  </Typography>
                </Box>
                <Chip 
                  label={guild.type === 'public' ? '공개' : '비공개'} 
                  size="small" 
                  variant="outlined"
                />
              </Box>
            ))}
            
            {myGuilds.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Groups sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  가입한 길드가 없습니다
                </Typography>
                <Button variant="outlined" size="small" sx={{ mt: 1, ...touchStyles.touchTarget }}>
                  길드 찾기
                </Button>
              </Box>
            )}
          </Box>
        )}
        
        {selectedQuickTab === 1 && (
          <Box>
            {myStudyGroups.slice(0, 3).map((group) => (
              <Box key={group.id} sx={{ ...flexBox.alignCenter, gap: 2, mb: 2 }}>
                <Avatar sx={{ bgcolor: '#9C27B0', width: 40, height: 40 }}>
                  <School />
                </Avatar>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {group.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {group.subject} • {group.members.length}명
                  </Typography>
                </Box>
                <Chip 
                  label={group.level} 
                  size="small" 
                  sx={{ bgcolor: '#9C27B0', color: 'white' }}
                />
              </Box>
            ))}
            
            {myStudyGroups.length === 0 && (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <School sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  참여한 스터디 그룹이 없습니다
                </Typography>
                <Button variant="outlined" size="small" sx={{ mt: 1, ...touchStyles.touchTarget }}>
                  스터디 그룹 찾기
                </Button>
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const renderPendingRequests = () => {
    if (receivedRequests.length === 0) return null;

    return (
      <Alert 
        severity="info" 
        sx={{ mb: 3 }}
        action={
          <Button 
            size="small" 
            onClick={() => {
              dispatch(setSelectedTab('requests'));
              dispatch(setFriendsPanelOpen(true));
            }}
            sx={{ ...touchStyles.touchTarget }}
          >
            확인
          </Button>
        }
      >
        {receivedRequests.length}개의 새로운 친구 요청이 있습니다!
      </Alert>
    );
  };

  const renderFriendshipProgress = () => {
    if (!friendshipStats) return null;

    const progressData = [
      {
        label: '이번 주 새 친구',
        current: friendshipStats.friends_added_this_week,
        max: 10,
        color: '#4CAF50'
      },
      {
        label: '이번 주 상호작용',
        current: friendshipStats.interactions_this_week,
        max: 50,
        color: '#2196F3'
      }
    ];

    return (
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, ...flexBox.alignCenter, gap: 1 }}>
            <LocalFireDepartment sx={{ color: '#FF6B35' }} />
            이번 주 소셜 활동
          </Typography>
          
          {progressData.map((item) => (
            <Box key={item.label} sx={{ mb: 2 }}>
              <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center', mb: 1 }}>
                <Typography variant="body2">{item.label}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {item.current}/{item.max}
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={(item.current / item.max) * 100}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    bgcolor: item.color,
                    borderRadius: 4,
                  }
                }}
              />
            </Box>
          ))}
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
          소셜 허브
        </Typography>
        <Typography variant="body1" color="text.secondary">
          친구들과 함께하는 학습 여정
        </Typography>
      </Box>

      {/* Pending Requests Alert */}
      {renderPendingRequests()}

      {/* Stats Cards */}
      <GridContainer spacing={3} sx={{ mb: 3 }}>
        <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1.5, mb: 3 }}>
          <StatsCard 
            title="친구" 
            value={friends.length} 
            icon={<Person />} 
            color="#2196F3"
          />
        </Box>
        <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1.5, mb: 3 }}>
          <StatsCard 
            title="온라인" 
            value={onlineFriends.size} 
            icon={<FiberManualRecord />} 
            color="#4CAF50"
          />
        </Box>
        <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1.5, mb: 3 }}>
          <StatsCard 
            title="길드" 
            value={myGuilds.length} 
            icon={<Groups />} 
            color="#9C27B0"
          />
        </Box>
        <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1.5, mb: 3 }}>
          <StatsCard 
            title="스터디" 
            value={myStudyGroups.length} 
            icon={<School />} 
            color="#FF9800"
          />
        </Box>
      </GridContainer>

      {/* Friendship Progress */}
      {renderFriendshipProgress()}

      {/* Main Content */}
      <GridContainer spacing={3}>
        {/* Online Friends */}
        <Box sx={{ width: { xs: '100%', md: '50%', lg: '33.333%' }, px: 1.5, mb: 3 }}>
          {renderOnlineFriends()}
        </Box>

        {/* Recent Activities */}
        <Box sx={{ width: { xs: '100%', md: '50%', lg: '33.333%' }, px: 1.5, mb: 3 }}>
          {renderRecentActivities()}
        </Box>

        {/* My Groups */}
        <Box sx={{ width: { xs: '100%', lg: '33.333%' }, px: 1.5, mb: 3 }}>
          {renderMyGroups()}
        </Box>
      </GridContainer>

      {/* Quick Actions */}
      <Box sx={{ mb: 3 }}>
        <GridContainer spacing={2}>
          <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1, mb: 2 }}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Person />}
              onClick={handleOpenFriends}
              sx={{ py: 2, ...touchStyles.touchTarget }}
            >
              친구 관리
            </Button>
          </Box>
          <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1, mb: 2 }}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Chat />}
              onClick={handleOpenChat}
              sx={{ py: 2, ...touchStyles.touchTarget }}
            >
              채팅
            </Button>
          </Box>
          <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1, mb: 2 }}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Groups />}
              sx={{ py: 2, ...touchStyles.touchTarget }}
            >
              길드
            </Button>
          </Box>
          <Box sx={{ width: { xs: '50%', sm: '25%' }, px: 1, mb: 2 }}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<School />}
              sx={{ py: 2, ...touchStyles.touchTarget }}
            >
              스터디 그룹
            </Button>
          </Box>
        </GridContainer>
      </Box>

      {/* Speed Dial */}
      <SpeedDial
        ariaLabel="소셜 액션"
        sx={{ position: 'fixed', bottom: 24, right: 24 }}
        icon={<SpeedDialIcon />}
        open={speedDialOpen}
        onOpen={() => setSpeedDialOpen(true)}
        onClose={() => setSpeedDialOpen(false)}
      >
        {speedDialActions.map((action) => (
          <SpeedDialAction
            key={action.name}
            icon={action.icon}
            tooltipTitle={action.name}
            onClick={() => {
              action.onClick();
              setSpeedDialOpen(false);
            }}
          />
        ))}
      </SpeedDial>

      {/* Chat Panel */}
      <ChatPanel />

      {/* Friends Panel */}
      {friendsPanelOpen && <Friends />}
    </Container>
  );
};

export default SocialHub;
