import React, { useState, useEffect } from 'react';
import {
  Snackbar,
  Alert,
  AlertTitle,
  Box,
  Typography,
  Avatar,
  IconButton,
  Button,
  Chip,
  Fade,
  Slide,
  Zoom,
  Card,
  CardContent,
  Stack,
} from '@mui/material';
import {
  Close,
  EmojiEvents,
  Group,
  ShoppingBag,
  School,
  Info,
  Person,
  TrendingUp,
  Visibility,
  CheckCircle,
  PlayArrow,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import {
  markAsRead,
  dismissNotification,
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

interface NotificationPopupProps {
  notification: Notification | null;
  onClose: () => void;
  autoHideDuration?: number;
  position?: {
    vertical: 'top' | 'bottom';
    horizontal: 'left' | 'center' | 'right';
  };
}

const NotificationPopup: React.FC<NotificationPopupProps> = ({
  notification,
  onClose,
  autoHideDuration = 5000,
  position = { vertical: 'top', horizontal: 'right' }
}) => {
  const dispatch = useAppDispatch();
  const [open, setOpen] = useState(false);
  const [timeLeft, setTimeLeft] = useState(autoHideDuration / 1000);

  // Category configurations
  const categoryConfig = {
    [NotificationCategory.ACHIEVEMENT]: {
      icon: <EmojiEvents />,
      color: '#FFD700',
      backgroundColor: '#FFF8E1',
    },
    [NotificationCategory.SOCIAL]: {
      icon: <Group />,
      color: '#2196F3',
      backgroundColor: '#E3F2FD',
    },
    [NotificationCategory.COMPETITION]: {
      icon: <EmojiEvents />,
      color: '#FF5722',
      backgroundColor: '#FBE9E7',
    },
    [NotificationCategory.SHOP]: {
      icon: <ShoppingBag />,
      color: '#4CAF50',
      backgroundColor: '#E8F5E8',
    },
    [NotificationCategory.LEARNING]: {
      icon: <School />,
      color: '#9C27B0',
      backgroundColor: '#F3E5F5',
    },
    [NotificationCategory.SYSTEM]: {
      icon: <Info />,
      color: '#607D8B',
      backgroundColor: '#ECEFF1',
    },
    [NotificationCategory.PARENT]: {
      icon: <Person />,
      color: '#795548',
      backgroundColor: '#EFEBE9',
    },
  };

  const priorityConfig = {
    [NotificationPriority.LOW]: { 
      severity: 'info' as const,
      color: '#4CAF50',
    },
    [NotificationPriority.MEDIUM]: { 
      severity: 'warning' as const,
      color: '#FF9800',
    },
    [NotificationPriority.HIGH]: { 
      severity: 'error' as const,
      color: '#F44336',
    },
    [NotificationPriority.URGENT]: { 
      severity: 'error' as const,
      color: '#E91E63',
    },
  };

  // Open popup when notification changes
  useEffect(() => {
    if (notification?.show_popup) {
      setOpen(true);
      setTimeLeft(autoHideDuration / 1000);
    }
  }, [notification, autoHideDuration]);

  // Auto hide timer
  useEffect(() => {
    if (!open || !notification?.auto_dismiss_after) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          handleClose();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [open, notification?.auto_dismiss_after]);

  const handleClose = () => {
    setOpen(false);
    onClose();
  };

  const handleNotificationClick = async () => {
    if (!notification) return;

    // Mark as read
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

    handleClose();
  };

  const handleActionClick = async (actionId: string) => {
    if (!notification) return;

    const action = notification.actions?.find(a => a.id === actionId);
    if (!action) return;

    switch (action.action) {
      case 'navigate':
        if (action.data?.path) {
          window.location.href = action.data.path;
        }
        break;
      case 'api_call':
        // Handle API call
        console.log('API call:', action.data);
        break;
      case 'external_link':
        if (action.data?.url) {
          window.open(action.data.url, '_blank');
        }
        break;
      case 'dismiss':
        await dispatch(dismissNotification(notification.id));
        break;
    }

    handleClose();
  };

  const getNotificationIcon = (notification: Notification) => {
    const config = categoryConfig[notification.category];
    return (
      <Avatar
        sx={{
          bgcolor: config.color,
          width: 48,
          height: 48,
          fontSize: '1.5rem',
        }}
      >
        {notification.icon || config.icon}
      </Avatar>
    );
  };

  const getAnimationProps = () => {
    switch (notification?.type) {
      case NotificationType.ACHIEVEMENT_UNLOCKED:
      case NotificationType.LEVEL_UP:
        return {
          initial: { scale: 0, rotate: -180 },
          animate: { scale: 1, rotate: 0 },
          exit: { scale: 0, rotate: 180 },
          transition: { type: "spring", stiffness: 300, damping: 20 }
        };
      case NotificationType.FRIEND_REQUEST:
      case NotificationType.GUILD_INVITATION:
        return {
          initial: { x: 300, opacity: 0 },
          animate: { x: 0, opacity: 1 },
          exit: { x: 300, opacity: 0 },
          transition: { type: "spring", stiffness: 200, damping: 25 }
        };
      default:
        return {
          initial: { y: -100, opacity: 0 },
          animate: { y: 0, opacity: 1 },
          exit: { y: -100, opacity: 0 },
          transition: { duration: 0.3 }
        };
    }
  };

  if (!notification) return null;

  const config = categoryConfig[notification.category];
  const priorityConf = priorityConfig[notification.priority];

  return (
    <AnimatePresence>
      {open && (
        <Box
          sx={{
            position: 'fixed',
            top: position.vertical === 'top' ? 24 : 'auto',
            bottom: position.vertical === 'bottom' ? 24 : 'auto',
            left: position.horizontal === 'left' ? 24 : 
                  position.horizontal === 'center' ? '50%' : 'auto',
            right: position.horizontal === 'right' ? 24 : 'auto',
            transform: position.horizontal === 'center' ? 'translateX(-50%)' : 'none',
            zIndex: 9999,
            maxWidth: { xs: 'calc(100vw - 32px)', sm: 400 },
            width: { xs: 'calc(100vw - 32px)', sm: 'auto' },
          }}
        >
          <motion.div {...getAnimationProps() as any}>
            <Card
              sx={{
                overflow: 'visible',
                cursor: 'pointer',
                border: `2px solid ${config.color}`,
                borderRadius: 3,
                boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
                position: 'relative',
                background: `linear-gradient(135deg, ${config.backgroundColor} 0%, rgba(255,255,255,0.9) 100%)`,
                '&:hover': {
                  transform: 'scale(1.02)',
                  boxShadow: '0 12px 40px rgba(0,0,0,0.15)',
                },
                transition: 'all 0.3s ease',
              }}
              onClick={handleNotificationClick}
            >
              {/* Priority Indicator */}
              {notification.priority === NotificationPriority.URGENT && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: -8,
                    right: -8,
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    bgcolor: priorityConf.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    animation: 'pulse 2s infinite',
                    '@keyframes pulse': {
                      '0%': { boxShadow: `0 0 0 0 ${priorityConf.color}66` },
                      '70%': { boxShadow: `0 0 0 10px ${priorityConf.color}00` },
                      '100%': { boxShadow: `0 0 0 0 ${priorityConf.color}00` },
                    },
                  }}
                >
                  <Typography variant="caption" sx={{ color: 'white', fontSize: '0.7rem', fontWeight: 'bold' }}>
                    !
                  </Typography>
                </Box>
              )}

              <CardContent sx={{ p: 2, pb: 1 }}>
                <Box sx={{ ...flexBox.spaceBetween, alignItems: 'flex-start', mb: 1 }}>
                  <Box sx={{ ...flexBox.alignCenter, gap: 1.5, flex: 1 }}>
                    {getNotificationIcon(notification)}
                    
                    <Box sx={{ flex: 1 }}>
                      <Typography
                        variant="subtitle1"
                        sx={{
                          fontWeight: 600,
                          color: 'text.primary',
                          fontSize: '0.95rem',
                          lineHeight: 1.2,
                        }}
                      >
                        {notification.title}
                      </Typography>
                      
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          mt: 0.5,
                          lineHeight: 1.4,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {notification.message}
                      </Typography>
                    </Box>
                  </Box>

                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleClose();
                    }}
                    sx={{
                      ml: 1,
                      color: 'text.secondary',
                      ...touchStyles.touchTarget,
                    }}
                  >
                    <Close fontSize="small" />
                  </IconButton>
                </Box>

                {/* Progress Bar for Auto Dismiss */}
                {notification.auto_dismiss_after && timeLeft > 0 && (
                  <Box
                    sx={{
                      position: 'absolute',
                      bottom: 0,
                      left: 0,
                      right: 0,
                      height: 3,
                      bgcolor: 'rgba(0,0,0,0.1)',
                      borderRadius: '0 0 12px 12px',
                      overflow: 'hidden',
                    }}
                  >
                    <Box
                      sx={{
                        height: '100%',
                        bgcolor: config.color,
                        width: `${(timeLeft / (autoHideDuration / 1000)) * 100}%`,
                        transition: 'width 1s linear',
                      }}
                    />
                  </Box>
                )}

                {/* Additional Data Display */}
                {notification.data && (
                  <Box sx={{ mt: 1 }}>
                    {notification.data.experience_gained && (
                      <Chip
                        icon={<TrendingUp />}
                        label={`+${notification.data.experience_gained} XP`}
                        size="small"
                        sx={{
                          bgcolor: '#4CAF50',
                          color: 'white',
                          fontSize: '0.75rem',
                          mr: 0.5,
                        }}
                      />
                    )}
                    
                    {notification.data.level && (
                      <Chip
                        label={`Level ${notification.data.level}`}
                        size="small"
                        sx={{
                          bgcolor: '#FF9800',
                          color: 'white',
                          fontSize: '0.75rem',
                          mr: 0.5,
                        }}
                      />
                    )}
                    
                    {notification.data.currency_amount && notification.data.currency_type && (
                      <Chip
                        label={`+${notification.data.currency_amount} ${notification.data.currency_type}`}
                        size="small"
                        sx={{
                          bgcolor: '#2196F3',
                          color: 'white',
                          fontSize: '0.75rem',
                        }}
                      />
                    )}
                  </Box>
                )}

                {/* Action Buttons */}
                {notification.actions && notification.actions.length > 0 && (
                  <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
                    {notification.actions.slice(0, 2).map((action) => (
                      <Button
                        key={action.id}
                        size="small"
                        variant={action.style === 'primary' ? 'contained' : 'outlined'}
                        color={action.style === 'success' ? 'success' : 
                               action.style === 'error' ? 'error' : 'primary'}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleActionClick(action.id);
                        }}
                        sx={{
                          fontSize: '0.75rem',
                          ...touchStyles.touchTarget,
                          minHeight: 32,
                        }}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </Box>
      )}
    </AnimatePresence>
  );
};

export default NotificationPopup;