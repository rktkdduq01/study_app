import React, { useState, useEffect, useMemo } from 'react';
import {
  Drawer,
  Box,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Avatar,
  Button,
  Tabs,
  Tab,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Badge,
  Alert,
  CircularProgress,
  Skeleton,
  Fade,
  Zoom,
  Collapse,
  Card,
  CardContent,
  CardActions,
  Divider,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
} from '@mui/material';
import {
  Close,
  Notifications,
  NotificationsActive,
  Search,
  FilterList,
  MarkEmailRead,
  Clear,
  Settings,
  Refresh,
  MoreVert,
  EmojiEvents,
  Group,
  ShoppingBag,
  School,
  Info,
  Person,
  Check,
  Delete,
  Visibility,
  VisibilityOff,
  KeyboardArrowDown,
  KeyboardArrowUp,
  Circle,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import {
  setNotificationPanelOpen,
  setSelectedCategory,
  setSearchQuery,
  setFilterPriority,
  markAsRead,
  markAllAsRead,
  dismissNotification,
  clearAllNotifications,
  fetchNotifications,
  toggleNotificationPanel,
} from '../../store/slices/notificationSlice';
import type {
  Notification,
} from '../../types/notification';
import {
  NotificationCategory,
  NotificationPriority,
  NotificationType,
} from '../../types/notification';
import { flexBox, touchStyles } from '../../utils/responsive';

interface NotificationPanelProps {
  anchor?: 'left' | 'right';
  width?: number;
}

const NotificationPanel: React.FC<NotificationPanelProps> = ({ 
  anchor = 'right', 
  width = 400 
}) => {
  const dispatch = useAppDispatch();
  const {
    notificationPanelOpen,
    notifications,
    loading,
    unreadCount,
    totalCount,
    categoryStats,
    selectedCategory,
    searchQuery,
    filterPriority,
    isConnected,
    connectionError,
  } = useAppSelector((state) => state.notifications);

  const [selectedTab, setSelectedTab] = useState(0);
  const [expandedNotifications, setExpandedNotifications] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'list' | 'grouped'>('list');

  // Category configurations
  const categoryConfig = {
    [NotificationCategory.ACHIEVEMENT]: {
      label: '업적',
      icon: <EmojiEvents />,
      color: '#FFD700',
    },
    [NotificationCategory.SOCIAL]: {
      label: '소셜',
      icon: <Group />,
      color: '#2196F3',
    },
    [NotificationCategory.COMPETITION]: {
      label: '경쟁',
      icon: <EmojiEvents />,
      color: '#FF5722',
    },
    [NotificationCategory.SHOP]: {
      label: '상점',
      icon: <ShoppingBag />,
      color: '#4CAF50',
    },
    [NotificationCategory.LEARNING]: {
      label: '학습',
      icon: <School />,
      color: '#9C27B0',
    },
    [NotificationCategory.SYSTEM]: {
      label: '시스템',
      icon: <Info />,
      color: '#607D8B',
    },
    [NotificationCategory.PARENT]: {
      label: '부모',
      icon: <Person />,
      color: '#795548',
    },
  };

  const priorityConfig = {
    [NotificationPriority.LOW]: { label: '낮음', color: '#4CAF50' },
    [NotificationPriority.MEDIUM]: { label: '보통', color: '#FF9800' },
    [NotificationPriority.HIGH]: { label: '높음', color: '#F44336' },
    [NotificationPriority.URGENT]: { label: '긴급', color: '#E91E63' },
  };

  // Filter notifications based on search and filters
  const filteredNotifications = useMemo(() => {
    let filtered = notifications;

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(n => n.category === selectedCategory);
    }

    // Filter by priority
    if (filterPriority) {
      filtered = filtered.filter(n => n.priority === filterPriority);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(n => 
        n.title.toLowerCase().includes(query) ||
        n.message.toLowerCase().includes(query)
      );
    }

    // Filter by tab (0: all, 1: unread)
    if (selectedTab === 1) {
      filtered = filtered.filter(n => !n.is_read);
    }

    return filtered;
  }, [notifications, selectedCategory, filterPriority, searchQuery, selectedTab]);

  // Load notifications on panel open
  useEffect(() => {
    if (notificationPanelOpen && notifications.length === 0) {
      dispatch(fetchNotifications({}));
    }
  }, [notificationPanelOpen, notifications.length, dispatch]);

  const handleClose = () => {
    dispatch(setNotificationPanelOpen(false));
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleCategoryFilter = (category: NotificationCategory | null) => {
    dispatch(setSelectedCategory(category));
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setSearchQuery(event.target.value));
  };

  const handlePriorityFilter = (priority: NotificationPriority | null) => {
    dispatch(setFilterPriority(priority));
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (!notification.is_read) {
      await dispatch(markAsRead(notification.id));
    }

    // Handle notification actions
    if (notification.actions && notification.actions.length > 0) {
      const primaryAction = notification.actions[0];
      if (primaryAction.action === 'navigate' && primaryAction.data?.path) {
        // Navigate to specified path
        window.location.href = primaryAction.data.path;
      }
    }
  };

  const handleMarkAllRead = async () => {
    await dispatch(markAllAsRead(selectedCategory || undefined));
  };

  const handleClearAll = async () => {
    if (window.confirm('모든 알림을 삭제하시겠습니까?')) {
      await dispatch(clearAllNotifications(selectedCategory || undefined));
    }
  };

  const handleRefresh = () => {
    dispatch(fetchNotifications({}));
  };

  const toggleExpanded = (notificationId: string) => {
    const newExpanded = new Set(expandedNotifications);
    if (newExpanded.has(notificationId)) {
      newExpanded.delete(notificationId);
    } else {
      newExpanded.add(notificationId);
    }
    setExpandedNotifications(newExpanded);
  };

  const getNotificationIcon = (notification: Notification) => {
    const config = categoryConfig[notification.category];
    return (
      <Avatar
        sx={{
          bgcolor: config.color,
          width: 40,
          height: 40,
          fontSize: '1.25rem',
        }}
      >
        {notification.icon || config.icon}
      </Avatar>
    );
  };

  const getTimeAgo = (timestamp: string) => {
    return formatDistanceToNow(new Date(timestamp), {
      addSuffix: true,
      locale: ko,
    });
  };

  const renderNotificationItem = (notification: Notification, index: number) => {
    const isExpanded = expandedNotifications.has(notification.id);
    const hasActions = notification.actions && notification.actions.length > 0;

    return (
      <motion.div
        key={notification.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.2, delay: index * 0.05 }}
      >
        <Card
          sx={{
            mb: 1,
            border: notification.is_read ? 'none' : '2px solid',
            borderColor: notification.is_read ? 'transparent' : 'primary.main',
            bgcolor: notification.is_read ? 'background.paper' : 'primary.light',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: 4,
            },
          }}
          onClick={() => handleNotificationClick(notification)}
        >
          <CardContent sx={{ pb: hasActions ? 1 : 2 }}>
            <Box sx={{ ...flexBox.spaceBetween, alignItems: 'flex-start' }}>
              <Box sx={{ ...flexBox.alignCenter, gap: 2, flex: 1 }}>
                {getNotificationIcon(notification)}
                
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ ...flexBox.spaceBetween, alignItems: 'flex-start' }}>
                    <Typography
                      variant="subtitle2"
                      sx={{
                        fontWeight: notification.is_read ? 400 : 600,
                        color: notification.is_read ? 'text.secondary' : 'text.primary',
                      }}
                    >
                      {notification.title}
                    </Typography>
                    
                    <Box sx={{ ...flexBox.alignCenter, gap: 0.5 }}>
                      <Chip
                        label={priorityConfig[notification.priority].label}
                        size="small"
                        sx={{
                          bgcolor: priorityConfig[notification.priority].color,
                          color: 'white',
                          fontSize: '0.7rem',
                          height: 20,
                        }}
                      />
                      
                      {!notification.is_read && (
                        <Circle sx={{ fontSize: 8, color: 'primary.main', ml: 0.5 }} />
                      )}
                    </Box>
                  </Box>
                  
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      mt: 0.5,
                      display: '-webkit-box',
                      WebkitLineClamp: isExpanded ? 'none' : 2,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}
                  >
                    {notification.message}
                  </Typography>
                  
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ mt: 1, display: 'block' }}
                  >
                    {getTimeAgo(notification.created_at)}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ ...flexBox.alignCenter, gap: 0.5, ml: 1 }}>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleExpanded(notification.id);
                  }}
                  sx={{ ...touchStyles.touchTarget }}
                >
                  {isExpanded ? <KeyboardArrowUp /> : <KeyboardArrowDown />}
                </IconButton>
                
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    dispatch(dismissNotification(notification.id));
                  }}
                  sx={{ ...touchStyles.touchTarget }}
                >
                  <Close />
                </IconButton>
              </Box>
            </Box>
          </CardContent>
          
          <Collapse in={isExpanded}>
            <CardContent sx={{ pt: 0 }}>
              {notification.data && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    추가 정보:
                  </Typography>
                  <Box sx={{ mt: 0.5, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                    <pre style={{ fontSize: '0.75rem', margin: 0, overflow: 'auto' }}>
                      {JSON.stringify(notification.data, null, 2)}
                    </pre>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Collapse>
          
          {hasActions && (
            <CardActions sx={{ pt: 0 }}>
              <Stack direction="row" spacing={1} sx={{ width: '100%' }}>
                {notification.actions!.slice(0, 2).map((action) => (
                  <Button
                    key={action.id}
                    size="small"
                    variant={action.style === 'primary' ? 'contained' : 'outlined'}
                    color={action.style === 'success' ? 'success' : 
                           action.style === 'error' ? 'error' : 'primary'}
                    onClick={(e) => {
                      e.stopPropagation();
                      // Handle action
                      console.log('Action clicked:', action);
                    }}
                    sx={{ ...touchStyles.touchTarget }}
                  >
                    {action.label}
                  </Button>
                ))}
              </Stack>
            </CardActions>
          )}
        </Card>
      </motion.div>
    );
  };

  const renderEmptyState = () => (
    <Box sx={{ ...flexBox.center, flexDirection: 'column', py: 8, px: 2 }}>
      <Notifications sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
      <Typography variant="h6" color="text.secondary" align="center">
        {selectedTab === 1 ? '읽지 않은 알림이 없습니다' : '알림이 없습니다'}
      </Typography>
      <Typography variant="body2" color="text.disabled" align="center" sx={{ mt: 1 }}>
        {selectedTab === 1 
          ? '모든 알림을 확인했습니다!'
          : '새로운 알림이 있으면 여기에 표시됩니다'
        }
      </Typography>
    </Box>
  );

  return (
    <Drawer
      anchor={anchor}
      open={notificationPanelOpen}
      onClose={handleClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: { xs: '100vw', sm: width },
          maxWidth: '100vw',
        },
      }}
    >
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ ...flexBox.alignCenter, gap: 1 }}>
              <Badge badgeContent={unreadCount} color="error" max={99}>
                <NotificationsActive />
              </Badge>
              알림
            </Typography>
            
            <Box sx={{ ...flexBox.alignCenter, gap: 0.5 }}>
              <Tooltip title="새로고침">
                <IconButton 
                  size="small" 
                  onClick={handleRefresh}
                  disabled={loading}
                  sx={{ ...touchStyles.touchTarget }}
                >
                  <Refresh />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="모두 읽음 표시">
                <IconButton
                  size="small"
                  onClick={handleMarkAllRead}
                  disabled={unreadCount === 0}
                  sx={{ ...touchStyles.touchTarget }}
                >
                  <MarkEmailRead />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="모두 삭제">
                <IconButton
                  size="small"
                  onClick={handleClearAll}
                  disabled={totalCount === 0}
                  sx={{ ...touchStyles.touchTarget }}
                >
                  <Clear />
                </IconButton>
              </Tooltip>
              
              <IconButton 
                size="small" 
                onClick={handleClose}
                sx={{ ...touchStyles.touchTarget }}
              >
                <Close />
              </IconButton>
            </Box>
          </Box>

          {/* Connection Status */}
          {connectionError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              연결 오류: {connectionError}
            </Alert>
          )}
          
          {!isConnected && !connectionError && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              실시간 알림이 연결되지 않았습니다.
            </Alert>
          )}

          {/* Tabs */}
          <Tabs
            value={selectedTab}
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{ mb: 2 }}
          >
            <Tab 
              label={`전체 (${totalCount})`}
              sx={{ ...touchStyles.touchTarget }}
            />
            <Tab 
              label={`읽지 않음 (${unreadCount})`}
              sx={{ ...touchStyles.touchTarget }}
            />
          </Tabs>

          {/* Search and Filters */}
          <TextField
            fullWidth
            size="small"
            placeholder="알림 검색..."
            value={searchQuery}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />

          {/* Category Filter */}
          <Box sx={{ ...flexBox.spaceBetween, gap: 1, mb: 1 }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>카테고리</InputLabel>
              <Select
                value={selectedCategory || ''}
                label="카테고리"
                onChange={(e) => handleCategoryFilter(e.target.value as NotificationCategory || null)}
              >
                <MenuItem value="">전체</MenuItem>
                {Object.entries(categoryConfig).map(([category, config]) => (
                  <MenuItem key={category} value={category}>
                    <Box sx={{ ...flexBox.alignCenter, gap: 1 }}>
                      {config.icon}
                      {config.label} ({categoryStats[category as NotificationCategory]?.total || 0})
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>우선순위</InputLabel>
              <Select
                value={filterPriority || ''}
                label="우선순위"
                onChange={(e) => handlePriorityFilter(e.target.value as NotificationPriority || null)}
              >
                <MenuItem value="">전체</MenuItem>
                {Object.entries(priorityConfig).map(([priority, config]) => (
                  <MenuItem key={priority} value={priority}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

        {/* Content */}
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {loading && notifications.length === 0 ? (
            <Box>
              {Array.from({ length: 5 }).map((_, index) => (
                <Card key={index} sx={{ mb: 1 }}>
                  <CardContent>
                    <Box sx={{ ...flexBox.alignCenter, gap: 2 }}>
                      <Skeleton variant="circular" width={40} height={40} />
                      <Box sx={{ flex: 1 }}>
                        <Skeleton variant="text" width="60%" />
                        <Skeleton variant="text" width="80%" />
                        <Skeleton variant="text" width="40%" />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          ) : filteredNotifications.length > 0 ? (
            <AnimatePresence>
              {filteredNotifications.map((notification, index) =>
                renderNotificationItem(notification, index)
              )}
            </AnimatePresence>
          ) : (
            renderEmptyState()
          )}

          {loading && notifications.length > 0 && (
            <Box sx={{ ...flexBox.center, py: 2 }}>
              <CircularProgress size={24} />
            </Box>
          )}
        </Box>
      </Box>
    </Drawer>
  );
};

export default NotificationPanel;