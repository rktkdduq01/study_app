import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Drawer,
  Box,
  Typography,
  TextField,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Avatar,
  Badge,
  Button,
  Chip,
  Paper,
  Divider,
  Menu,
  MenuItem,
  InputAdornment,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Card,
  CardContent,
  Stack,
  Skeleton,
  Alert,
} from '@mui/material';
import {
  Close,
  Send,
  AttachFile,
  EmojiEmotions,
  MoreVert,
  Search,
  Add,
  Person,
  Group,
  Circle,
  Schedule,
  CheckCircle,
  DoneAll,
  Reply,
  Edit,
  Delete,
  Flag,
  VolumeOff,
  Notifications,
  NotificationsOff,
  Image,
  FileCopy,
  KeyboardArrowDown,
  KeyboardArrowUp,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow, format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import {
  fetchChatRooms,
  fetchChatMessages,
  sendChatMessage,
  setActiveRoom,
  setChatPanelOpen,
  markMessagesAsRead,
  addChatMessage,
  updateTypingUsers,
} from '../../store/slices/friendSlice';
import {
  ChatRoom,
  ChatMessage,
  ChatParticipant,
  MessageReaction,
} from '../../types/friend';
import { flexBox, touchStyles } from '../../utils/responsive';

interface ChatPanelProps {
  anchor?: 'left' | 'right';
  width?: number;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ 
  anchor = 'right', 
  width = 400 
}) => {
  const dispatch = useAppDispatch();
  const {
    chatPanelOpen,
    chatRooms,
    activeRoomId,
    chatMessages,
    chatLoading,
    typingUsers,
  } = useAppSelector((state) => state.friends);

  const [messageInput, setMessageInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRoom, setSelectedRoom] = useState<ChatRoom | null>(null);
  const [showCreateGroup, setShowCreateGroup] = useState(false);
  const [replyToMessage, setReplyToMessage] = useState<ChatMessage | null>(null);
  const [editingMessage, setEditingMessage] = useState<ChatMessage | null>(null);
  const [messageMenuAnchor, setMessageMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedMessage, setSelectedMessage] = useState<ChatMessage | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageInputRef = useRef<HTMLInputElement>(null);

  // Load chat rooms on panel open
  useEffect(() => {
    if (chatPanelOpen && chatRooms.length === 0) {
      dispatch(fetchChatRooms());
    }
  }, [chatPanelOpen, chatRooms.length, dispatch]);

  // Load messages when active room changes
  useEffect(() => {
    if (activeRoomId && chatPanelOpen) {
      dispatch(fetchChatMessages({ roomId: activeRoomId }));
      setSelectedRoom(chatRooms.find(room => room.id === activeRoomId) || null);
    }
  }, [activeRoomId, chatPanelOpen, dispatch, chatRooms]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, activeRoomId]);

  // Auto-focus message input when room changes
  useEffect(() => {
    if (activeRoomId && messageInputRef.current) {
      messageInputRef.current.focus();
    }
  }, [activeRoomId]);

  const activeMessages = useMemo(() => {
    return activeRoomId ? chatMessages[activeRoomId] || [] : [];
  }, [chatMessages, activeRoomId]);

  const filteredRooms = useMemo(() => {
    if (!searchQuery.trim()) return chatRooms;
    
    const query = searchQuery.toLowerCase();
    return chatRooms.filter(room => {
      // Search by room name or participant names
      if (room.name?.toLowerCase().includes(query)) return true;
      
      return room.participants.some(participant =>
        participant.character_name.toLowerCase().includes(query)
      );
    });
  }, [chatRooms, searchQuery]);

  const currentTypingUsers = useMemo(() => {
    if (!activeRoomId) return [];
    return typingUsers[activeRoomId] || [];
  }, [typingUsers, activeRoomId]);

  const handleClose = () => {
    dispatch(setChatPanelOpen(false));
  };

  const handleRoomSelect = (room: ChatRoom) => {
    dispatch(setActiveRoom(room.id));
    setSelectedRoom(room);
  };

  const handleSendMessage = async () => {
    if (!messageInput.trim() || !activeRoomId) return;

    try {
      const messageData = {
        roomId: activeRoomId,
        content: messageInput.trim(),
        type: 'text' as const,
        metadata: replyToMessage ? { reply_to: replyToMessage.id } : undefined,
      };

      await dispatch(sendChatMessage(messageData));
      setMessageInput('');
      setReplyToMessage(null);
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleMessageMenuOpen = (event: React.MouseEvent<HTMLElement>, message: ChatMessage) => {
    setMessageMenuAnchor(event.currentTarget);
    setSelectedMessage(message);
  };

  const handleMessageMenuClose = () => {
    setMessageMenuAnchor(null);
    setSelectedMessage(null);
  };

  const handleReplyToMessage = (message: ChatMessage) => {
    setReplyToMessage(message);
    setMessageMenuAnchor(null);
    messageInputRef.current?.focus();
  };

  const handleEditMessage = (message: ChatMessage) => {
    setEditingMessage(message);
    setMessageInput(message.content);
    setMessageMenuAnchor(null);
    messageInputRef.current?.focus();
  };

  const getRoomDisplayName = (room: ChatRoom) => {
    if (room.type === 'direct') {
      // For direct chats, show the other participant's name
      const otherParticipant = room.participants.find(p => p.user_id !== 'user1'); // Current user ID
      return otherParticipant?.character_name || 'Unknown';
    }
    return room.name || 'Group Chat';
  };

  const getRoomAvatar = (room: ChatRoom) => {
    if (room.type === 'direct') {
      const otherParticipant = room.participants.find(p => p.user_id !== 'user1');
      return otherParticipant?.avatar_url;
    }
    return room.avatar_url;
  };

  const getMessageStatus = (message: ChatMessage) => {
    const totalParticipants = selectedRoom?.participants.length || 0;
    const readCount = message.read_by.length;
    const deliveredCount = message.delivered_to.length;

    if (readCount >= totalParticipants) {
      return { icon: <DoneAll sx={{ fontSize: 16, color: '#4CAF50' }} />, label: '읽음' };
    } else if (deliveredCount >= totalParticipants) {
      return { icon: <DoneAll sx={{ fontSize: 16, color: '#9E9E9E' }} />, label: '전달됨' };
    } else {
      return { icon: <CheckCircle sx={{ fontSize: 16, color: '#9E9E9E' }} />, label: '전송됨' };
    }
  };

  const renderRoomItem = (room: ChatRoom) => (
    <ListItem
      key={room.id}
      disablePadding
      sx={{
        borderRadius: 2,
        mb: 0.5,
        '&:hover': { bgcolor: 'action.hover' },
        '&.Mui-selected': { 
          bgcolor: 'primary.light',
          '&:hover': { bgcolor: 'primary.light' }
        },
        ...touchStyles.touchListItem,
      }}
    >
      <ListItemButton
        selected={room.id === activeRoomId}
        onClick={() => handleRoomSelect(room)}
      >
        <ListItemIcon>
        <Badge
          overlap="circular"
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          badgeContent={
            room.type === 'direct' && room.participants.some(p => p.is_online) ? (
              <Circle sx={{ fontSize: 12, color: '#4CAF50' }} />
            ) : null
          }
        >
          <Avatar src={getRoomAvatar(room)} sx={{ width: 48, height: 48 }}>
            {room.type === 'group' ? <Group /> : <Person />}
          </Avatar>
        </Badge>
      </ListItemIcon>
      
      <ListItemText
        primary={
          <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
            <Typography variant="subtitle2" noWrap sx={{ fontWeight: 600 }}>
              {getRoomDisplayName(room)}
            </Typography>
            {room.last_message && (
              <Typography variant="caption" color="text.secondary">
                {formatDistanceToNow(new Date(room.last_message.created_at), {
                  addSuffix: true,
                  locale: ko,
                })}
              </Typography>
            )}
          </Box>
        }
        secondary={
          <Box>
            {room.last_message && (
              <Typography 
                variant="body2" 
                color="text.secondary" 
                noWrap
                sx={{ maxWidth: 200 }}
              >
                {room.last_message.sender_name}: {room.last_message.content}
              </Typography>
            )}
            {room.type === 'group' && (
              <Typography variant="caption" color="text.secondary">
                {room.participants.length}명
              </Typography>
            )}
          </Box>
        }
      />
      </ListItemButton>
      
      <ListItemSecondaryAction>
        <Box sx={{ ...flexBox.center, flexDirection: 'column', gap: 0.5 }}>
          {room.unread_count > 0 && (
            <Badge
              badgeContent={room.unread_count}
              color="error"
              max={99}
              sx={{
                '& .MuiBadge-badge': {
                  fontSize: '0.7rem',
                  minWidth: 18,
                  height: 18,
                }
              }}
            />
          )}
          {room.is_muted && (
            <VolumeOff sx={{ fontSize: 16, color: 'text.disabled' }} />
          )}
        </Box>
      </ListItemSecondaryAction>
    </ListItem>
  );

  const renderMessage = (message: ChatMessage, index: number) => {
    const isOwnMessage = message.sender_id === 'user1'; // Current user ID
    const isFirstInGroup = index === 0 || activeMessages[index - 1].sender_id !== message.sender_id;
    const showAvatar = !isOwnMessage && isFirstInGroup;
    const status = isOwnMessage ? getMessageStatus(message) : null;

    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        <Box
          sx={{
            display: 'flex',
            justifyContent: isOwnMessage ? 'flex-end' : 'flex-start',
            mb: 1,
            mx: 1,
          }}
        >
          {showAvatar && (
            <Avatar
              src={message.sender_avatar}
              sx={{ width: 32, height: 32, mr: 1, mt: 0.5 }}
            >
              <Person />
            </Avatar>
          )}
          
          <Box
            sx={{
              maxWidth: '70%',
              ml: !isOwnMessage && !showAvatar ? 5 : 0,
            }}
          >
            {isFirstInGroup && !isOwnMessage && (
              <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                {message.sender_name}
              </Typography>
            )}
            
            {message.reply_to && (
              <Paper
                sx={{
                  p: 1,
                  mb: 0.5,
                  bgcolor: 'action.hover',
                  borderLeft: '3px solid',
                  borderColor: 'primary.main',
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  Replying to: {/* Original message content would go here */}
                </Typography>
              </Paper>
            )}
            
            <Paper
              sx={{
                p: 1.5,
                bgcolor: isOwnMessage ? 'primary.main' : 'background.paper',
                color: isOwnMessage ? 'primary.contrastText' : 'text.primary',
                borderRadius: 2,
                position: 'relative',
                cursor: 'pointer',
                '&:hover': {
                  '& .message-actions': {
                    opacity: 1,
                  }
                }
              }}
              onClick={(e) => handleMessageMenuOpen(e, message)}
            >
              <Typography variant="body2" sx={{ wordBreak: 'break-word' }}>
                {message.content}
              </Typography>
              
              {message.message_type === 'image' && message.metadata?.image_url && (
                <Box
                  component="img"
                  src={message.metadata.image_url}
                  sx={{
                    maxWidth: '100%',
                    maxHeight: 200,
                    borderRadius: 1,
                    mt: 1,
                  }}
                />
              )}
              
              <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center', mt: 0.5 }}>
                <Typography variant="caption" sx={{ opacity: 0.7 }}>
                  {format(new Date(message.created_at), 'HH:mm')}
                  {message.is_edited && ' (수정됨)'}
                </Typography>
                
                {isOwnMessage && status && (
                  <Tooltip title={status.label}>
                    <Box>{status.icon}</Box>
                  </Tooltip>
                )}
              </Box>
              
              {/* Reactions */}
              {message.reactions.length > 0 && (
                <Box sx={{ ...flexBox.alignCenter, gap: 0.5, mt: 1 }}>
                  {message.reactions.map((reaction) => (
                    <Chip
                      key={reaction.emoji}
                      label={`${reaction.emoji} ${reaction.count}`}
                      size="small"
                      variant={reaction.user_reacted ? "filled" : "outlined"}
                      sx={{ height: 20, fontSize: '0.7rem' }}
                    />
                  ))}
                </Box>
              )}
            </Paper>
          </Box>
        </Box>
      </motion.div>
    );
  };

  const renderTypingIndicator = () => {
    if (currentTypingUsers.length === 0) return null;

    return (
      <Box sx={{ p: 2, ...flexBox.alignCenter, gap: 1 }}>
        <Avatar sx={{ width: 24, height: 24 }}>
          <Person />
        </Avatar>
        <Typography variant="caption" color="text.secondary">
          {currentTypingUsers.length === 1
            ? `${currentTypingUsers[0]}님이 입력 중...`
            : `${currentTypingUsers.length}명이 입력 중...`
          }
        </Typography>
        <Box sx={{ ...flexBox.alignCenter, gap: 0.25 }}>
          <Circle sx={{ fontSize: 4, animation: 'pulse 1.5s infinite' }} />
          <Circle sx={{ fontSize: 4, animation: 'pulse 1.5s infinite 0.2s' }} />
          <Circle sx={{ fontSize: 4, animation: 'pulse 1.5s infinite 0.4s' }} />
        </Box>
      </Box>
    );
  };

  return (
    <Drawer
      anchor={anchor}
      open={chatPanelOpen}
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
          <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
            <Typography variant="h6">
              채팅
            </Typography>
            <Box sx={{ ...flexBox.alignCenter, gap: 0.5 }}>
              <IconButton 
                size="small" 
                onClick={() => setShowCreateGroup(true)}
                sx={{ ...touchStyles.touchTarget }}
              >
                <Add />
              </IconButton>
              <IconButton 
                size="small" 
                onClick={handleClose}
                sx={{ ...touchStyles.touchTarget }}
              >
                <Close />
              </IconButton>
            </Box>
          </Box>
          
          <TextField
            fullWidth
            size="small"
            placeholder="채팅방 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ mt: 2 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
          />
        </Box>

        {!activeRoomId ? (
          /* Room List */
          <Box sx={{ flex: 1, overflow: 'auto' }}>
            {chatLoading ? (
              <Box sx={{ p: 2 }}>
                {Array.from({ length: 5 }).map((_, index) => (
                  <Box key={index} sx={{ ...flexBox.alignCenter, gap: 2, mb: 2 }}>
                    <Skeleton variant="circular" width={48} height={48} />
                    <Box sx={{ flex: 1 }}>
                      <Skeleton variant="text" width="60%" />
                      <Skeleton variant="text" width="40%" />
                    </Box>
                  </Box>
                ))}
              </Box>
            ) : filteredRooms.length > 0 ? (
              <List sx={{ p: 1 }}>
                {filteredRooms.map(renderRoomItem)}
              </List>
            ) : (
              <Box sx={{ ...flexBox.center, flexDirection: 'column', py: 8, px: 2 }}>
                <Group sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" align="center">
                  {searchQuery ? '검색 결과가 없습니다' : '채팅방이 없습니다'}
                </Typography>
                <Typography variant="body2" color="text.disabled" align="center" sx={{ mt: 1 }}>
                  {searchQuery ? '다른 키워드로 검색해보세요' : '친구와 채팅을 시작해보세요!'}
                </Typography>
              </Box>
            )}
          </Box>
        ) : (
          /* Chat View */
          <>
            {/* Chat Header */}
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
                <Box sx={{ ...flexBox.alignCenter, gap: 2 }}>
                  <IconButton 
                    size="small" 
                    onClick={() => dispatch(setActiveRoom(null))}
                    sx={{ ...touchStyles.touchTarget }}
                  >
                    <KeyboardArrowDown />
                  </IconButton>
                  <Avatar src={selectedRoom ? getRoomAvatar(selectedRoom) : undefined}>
                    {selectedRoom?.type === 'group' ? <Group /> : <Person />}
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      {selectedRoom ? getRoomDisplayName(selectedRoom) : ''}
                    </Typography>
                    {selectedRoom?.type === 'group' && (
                      <Typography variant="caption" color="text.secondary">
                        {selectedRoom.participants.length}명
                      </Typography>
                    )}
                  </Box>
                </Box>
                <IconButton size="small" sx={{ ...touchStyles.touchTarget }}>
                  <MoreVert />
                </IconButton>
              </Box>
            </Box>

            {/* Messages */}
            <Box sx={{ flex: 1, overflow: 'auto', py: 1 }}>
              <AnimatePresence>
                {activeMessages.map((message, index) => renderMessage(message, index))}
              </AnimatePresence>
              {renderTypingIndicator()}
              <div ref={messagesEndRef} />
            </Box>

            {/* Reply Preview */}
            {replyToMessage && (
              <Box sx={{ p: 1, bgcolor: 'action.hover', borderLeft: '3px solid', borderColor: 'primary.main' }}>
                <Box sx={{ ...flexBox.spaceBetween, alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Replying to {replyToMessage.sender_name}: {replyToMessage.content}
                  </Typography>
                  <IconButton size="small" onClick={() => setReplyToMessage(null)}>
                    <Close />
                  </IconButton>
                </Box>
              </Box>
            )}

            {/* Message Input */}
            <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
              <Box sx={{ ...flexBox.alignCenter, gap: 1 }}>
                <TextField
                  ref={messageInputRef}
                  fullWidth
                  multiline
                  maxRows={4}
                  placeholder="메시지를 입력하세요..."
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  variant="outlined"
                  size="small"
                />
                
                <Box sx={{ ...flexBox.alignCenter, gap: 0.5 }}>
                  <IconButton size="small" sx={{ ...touchStyles.touchTarget }}>
                    <AttachFile />
                  </IconButton>
                  <IconButton size="small" sx={{ ...touchStyles.touchTarget }}>
                    <EmojiEmotions />
                  </IconButton>
                  <IconButton
                    size="small"
                    color="primary"
                    disabled={!messageInput.trim()}
                    onClick={handleSendMessage}
                    sx={{ ...touchStyles.touchTarget }}
                  >
                    <Send />
                  </IconButton>
                </Box>
              </Box>
            </Box>
          </>
        )}
      </Box>

      {/* Message Context Menu */}
      <Menu
        anchorEl={messageMenuAnchor}
        open={Boolean(messageMenuAnchor)}
        onClose={handleMessageMenuClose}
      >
        <MenuItem onClick={() => selectedMessage && handleReplyToMessage(selectedMessage)}>
          <ListItemIcon><Reply /></ListItemIcon>
          <ListItemText>답장</ListItemText>
        </MenuItem>
        {selectedMessage?.sender_id === 'user1' && (
          <MenuItem onClick={() => selectedMessage && handleEditMessage(selectedMessage)}>
            <ListItemIcon><Edit /></ListItemIcon>
            <ListItemText>수정</ListItemText>
          </MenuItem>
        )}
        <MenuItem onClick={handleMessageMenuClose}>
          <ListItemIcon><FileCopy /></ListItemIcon>
          <ListItemText>복사</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleMessageMenuClose}>
          <ListItemIcon><Flag /></ListItemIcon>
          <ListItemText>신고</ListItemText>
        </MenuItem>
        {selectedMessage?.sender_id === 'user1' && (
          <MenuItem onClick={handleMessageMenuClose} sx={{ color: 'error.main' }}>
            <ListItemIcon><Delete sx={{ color: 'error.main' }} /></ListItemIcon>
            <ListItemText>삭제</ListItemText>
          </MenuItem>
        )}
      </Menu>
    </Drawer>
  );
};

export default ChatPanel;