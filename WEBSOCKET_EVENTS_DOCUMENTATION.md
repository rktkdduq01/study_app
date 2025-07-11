# WebSocket Events Documentation

## Overview

This document provides comprehensive documentation for all WebSocket events in the Quest Educational Platform. The WebSocket server uses Socket.IO for real-time bidirectional communication.

## Connection Configuration

### WebSocket URL
- **Production**: `wss://ws.quest-edu.com`
- **Development**: `ws://localhost:8000`

### Connection Options
```javascript
const socket = io('wss://ws.quest-edu.com', {
  transports: ['websocket'],
  auth: {
    token: 'Bearer <JWT_TOKEN>'
  },
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5
});
```

### Authentication
All WebSocket connections require a valid JWT token passed in the auth object during connection.

## Connection Events

### connect
Fired when the client successfully connects to the server.

**Client listens:**
```javascript
socket.on('connect', () => {
  console.log('Connected with ID:', socket.id);
});
```

### disconnect
Fired when the client disconnects from the server.

**Client listens:**
```javascript
socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason);
  // Reasons: 'io server disconnect', 'io client disconnect', 'ping timeout', 'transport close'
});
```

### error
Fired when an error occurs.

**Client listens:**
```javascript
socket.on('error', (error) => {
  console.error('Socket error:', error);
});
```

## 🎮 Multiplayer Battle Events

### create_room
Create a new battle room.

**Client emits:**
```javascript
socket.emit('create_room', {
  title: "수학 대결",
  subject: "math",
  difficulty: "medium",
  max_participants: 2,
  time_per_question: 30,
  total_rounds: 5,
  is_private: false
});
```

**Server emits:**
```javascript
// Success
socket.emit('room_created', {
  room_id: "room_abc123",
  room_code: "ABC123",
  creator_id: 1,
  settings: {
    subject: "math",
    difficulty: "medium",
    max_participants: 2,
    time_per_question: 30,
    total_rounds: 5
  }
});

// Error
socket.emit('error', {
  event: 'create_room',
  code: 'ROOM_CREATION_FAILED',
  message: '방 생성에 실패했습니다'
});
```

### join_room
Join an existing battle room.

**Client emits:**
```javascript
socket.emit('join_room', {
  room_code: "ABC123"  // or room_id: "room_abc123"
});
```

**Server emits:**
```javascript
// To all room participants
io.to(roomId).emit('user_joined', {
  user_id: 2,
  username: "player2",
  avatar_url: "/avatars/2.png",
  level: 10,
  participants: [
    {id: 1, username: "player1", ready: false},
    {id: 2, username: "player2", ready: false}
  ]
});
```

### leave_room
Leave the current room.

**Client emits:**
```javascript
socket.emit('leave_room');
```

**Server emits:**
```javascript
// To remaining participants
io.to(roomId).emit('user_left', {
  user_id: 2,
  username: "player2",
  remaining_participants: [
    {id: 1, username: "player1", ready: false}
  ]
});
```

### player_ready
Mark player as ready to start.

**Client emits:**
```javascript
socket.emit('player_ready', {
  ready: true
});
```

**Server emits:**
```javascript
// To all participants
io.to(roomId).emit('player_ready_state', {
  user_id: 1,
  ready: true,
  all_ready: false,
  ready_count: 1,
  total_count: 2
});

// When all players are ready
io.to(roomId).emit('battle_starting', {
  countdown: 3,
  start_time: "2024-01-20T10:00:03Z"
});
```

### battle_start
Battle has started.

**Server emits:**
```javascript
io.to(roomId).emit('battle_started', {
  round: 1,
  question: {
    id: "q1",
    text: "12 × 8 = ?",
    options: ["86", "96", "106", "116"],
    time_limit: 30,
    points: 100
  },
  round_start_time: "2024-01-20T10:00:00Z"
});
```

### submit_answer
Submit answer for current question.

**Client emits:**
```javascript
socket.emit('submit_answer', {
  question_id: "q1",
  answer: "96",
  time_taken: 4.5
});
```

**Server emits:**
```javascript
// To the answering player
socket.emit('answer_result', {
  correct: true,
  correct_answer: "96",
  points_earned: 100,
  time_bonus: 20,
  total_score: 120
});

// To all participants
io.to(roomId).emit('player_answered', {
  user_id: 1,
  answered: true,
  correct: true,
  time_taken: 4.5,
  all_answered: false
});

// When all players have answered
io.to(roomId).emit('round_complete', {
  round: 1,
  results: [
    {user_id: 1, correct: true, points: 120, total_score: 120},
    {user_id: 2, correct: false, points: 0, total_score: 0}
  ],
  next_round_in: 3
});
```

### battle_complete
Battle has ended.

**Server emits:**
```javascript
io.to(roomId).emit('battle_complete', {
  winner_id: 1,
  final_scores: [
    {user_id: 1, score: 580, rank: 1},
    {user_id: 2, score: 420, rank: 2}
  ],
  rewards: {
    winner: {experience: 100, gold: 50},
    loser: {experience: 50, gold: 20}
  },
  statistics: {
    total_questions: 5,
    player_stats: [
      {user_id: 1, correct: 4, accuracy: 0.8, avg_time: 5.2},
      {user_id: 2, correct: 3, accuracy: 0.6, avg_time: 6.8}
    ]
  }
});
```

## 👥 Study Group Events

### create_study_group
Create a new study group.

**Client emits:**
```javascript
socket.emit('create_study_group', {
  name: "수학 스터디",
  subject: "math",
  description: "함께 수학 공부해요!",
  max_members: 5,
  is_public: true
});
```

**Server emits:**
```javascript
socket.emit('study_group_created', {
  group_id: "group_123",
  name: "수학 스터디",
  creator_id: 1,
  invite_code: "STD123"
});
```

### join_study_group
Join a study group.

**Client emits:**
```javascript
socket.emit('join_study_group', {
  invite_code: "STD123"  // or group_id: "group_123"
});
```

**Server emits:**
```javascript
// To all group members
io.to(groupId).emit('member_joined', {
  user_id: 2,
  username: "student2",
  level: 8,
  joined_at: "2024-01-20T10:00:00Z",
  total_members: 2
});
```

### study_group_message
Send a message in study group chat.

**Client emits:**
```javascript
socket.emit('study_group_message', {
  group_id: "group_123",
  message: "안녕하세요! 오늘 뭐 공부하실래요?",
  type: "text"  // "text", "image", "file"
});
```

**Server emits:**
```javascript
// To all group members
io.to(groupId).emit('new_group_message', {
  message_id: "msg_456",
  sender_id: 1,
  sender_name: "student1",
  message: "안녕하세요! 오늘 뭐 공부하실래요?",
  type: "text",
  timestamp: "2024-01-20T10:00:00Z"
});
```

### start_group_session
Start a group study session.

**Client emits:**
```javascript
socket.emit('start_group_session', {
  group_id: "group_123",
  topic: "이차방정식",
  duration: 30  // minutes
});
```

**Server emits:**
```javascript
// To all online group members
io.to(groupId).emit('group_session_started', {
  session_id: "session_789",
  topic: "이차방정식",
  duration: 30,
  started_by: 1,
  start_time: "2024-01-20T10:00:00Z"
});
```

## 🏆 Tournament Events

### tournament_registration
Register for a tournament.

**Client emits:**
```javascript
socket.emit('tournament_registration', {
  tournament_id: "tourn_123"
});
```

**Server emits:**
```javascript
socket.emit('registration_confirmed', {
  tournament_id: "tourn_123",
  participant_number: 42,
  total_participants: 64,
  start_time: "2024-01-25T14:00:00Z"
});
```

### tournament_match_ready
Tournament match is ready to begin.

**Server emits:**
```javascript
socket.emit('tournament_match_ready', {
  match_id: "match_456",
  round: 1,
  opponent: {
    id: 15,
    username: "challenger15",
    level: 12,
    rating: 1450
  },
  start_in_seconds: 30
});
```

### tournament_update
Live tournament updates.

**Server emits:**
```javascript
// Bracket update
socket.emit('tournament_bracket_update', {
  tournament_id: "tourn_123",
  round: 2,
  matches: [
    {
      match_id: "match_789",
      player1: {id: 1, username: "player1", score: 3},
      player2: {id: 2, username: "player2", score: 1},
      status: "completed",
      winner_id: 1
    }
  ]
});

// Leaderboard update
socket.emit('tournament_leaderboard', {
  tournament_id: "tourn_123",
  top_players: [
    {rank: 1, user_id: 1, username: "player1", points: 150},
    {rank: 2, user_id: 3, username: "player3", points: 120}
  ],
  your_rank: 8,
  your_points: 90
});
```

## 💬 Real-time Chat Events

### send_message
Send a direct message.

**Client emits:**
```javascript
socket.emit('send_message', {
  recipient_id: 5,
  message: "안녕! 같이 공부할래?",
  type: "text"
});
```

**Server emits:**
```javascript
// To recipient
socket.to(recipientSocketId).emit('new_message', {
  message_id: "msg_123",
  sender_id: 1,
  sender_name: "student1",
  message: "안녕! 같이 공부할래?",
  type: "text",
  timestamp: "2024-01-20T10:00:00Z"
});

// To sender (confirmation)
socket.emit('message_sent', {
  message_id: "msg_123",
  recipient_id: 5,
  sent_at: "2024-01-20T10:00:00Z"
});
```

### typing_indicator
Show typing indicator.

**Client emits:**
```javascript
socket.emit('typing', {
  recipient_id: 5,
  is_typing: true
});
```

**Server emits:**
```javascript
// To recipient
socket.to(recipientSocketId).emit('user_typing', {
  user_id: 1,
  is_typing: true
});
```

### message_read
Mark message as read.

**Client emits:**
```javascript
socket.emit('message_read', {
  message_ids: ["msg_123", "msg_124"]
});
```

**Server emits:**
```javascript
// To sender
socket.to(senderSocketId).emit('message_read_receipt', {
  message_ids: ["msg_123", "msg_124"],
  read_by: 5,
  read_at: "2024-01-20T10:00:00Z"
});
```

## 🔔 Notification Events

### notification
Real-time notifications.

**Server emits:**
```javascript
// Achievement unlocked
socket.emit('notification', {
  id: "notif_123",
  type: "achievement",
  title: "새로운 업적!",
  message: "일주일 연속 학습 달성",
  data: {
    achievement_id: 5,
    achievement_name: "꾸준한 학습자",
    points: 100
  },
  timestamp: "2024-01-20T10:00:00Z"
});

// Friend request
socket.emit('notification', {
  id: "notif_124",
  type: "friend_request",
  title: "친구 요청",
  message: "player2님이 친구 요청을 보냈습니다",
  data: {
    from_user_id: 2,
    from_username: "player2"
  },
  timestamp: "2024-01-20T10:00:00Z"
});

// Level up
socket.emit('notification', {
  id: "notif_125",
  type: "level_up",
  title: "레벨 업!",
  message: "레벨 10 달성! 새로운 기능이 잠금 해제되었습니다",
  data: {
    new_level: 10,
    unlocked_features: ["tournaments", "advanced_quests"]
  },
  timestamp: "2024-01-20T10:00:00Z"
});
```

## 📊 Live Analytics Events

### analytics_subscribe
Subscribe to real-time analytics.

**Client emits:**
```javascript
socket.emit('analytics_subscribe', {
  type: "user",  // "user", "global", "content"
  filters: {
    subject: "math",
    date_range: "today"
  }
});
```

**Server emits:**
```javascript
// Initial data
socket.emit('analytics_data', {
  type: "user",
  data: {
    active_users: 1234,
    sessions_today: 5678,
    average_session_time: 25.5,
    top_subjects: [
      {subject: "math", sessions: 2345},
      {subject: "science", sessions: 1890}
    ]
  },
  timestamp: "2024-01-20T10:00:00Z"
});

// Live updates
socket.emit('analytics_update', {
  type: "user",
  metric: "active_users",
  value: 1235,
  change: 1,
  timestamp: "2024-01-20T10:00:30Z"
});
```

## 🎯 Quest Progress Events

### quest_progress
Real-time quest progress updates.

**Server emits:**
```javascript
socket.emit('quest_progress', {
  quest_id: 123,
  quest_name: "수학 마스터",
  current_progress: 7,
  total_required: 10,
  percentage: 70,
  message: "3문제만 더 풀면 완료!"
});
```

### quest_completed
Quest completion notification.

**Server emits:**
```javascript
socket.emit('quest_completed', {
  quest_id: 123,
  quest_name: "수학 마스터",
  rewards: {
    experience: 100,
    gold: 50,
    items: ["math_badge"],
    unlocked_content: ["advanced_math_course"]
  },
  completion_time: "2024-01-20T10:00:00Z"
});
```

## 🎮 Game State Sync Events

### sync_character
Sync character state.

**Client emits:**
```javascript
socket.emit('sync_character', {
  character_id: 1,
  position: {x: 100, y: 200},
  animation_state: "idle",
  equipment: {
    hat: "wizard_hat",
    outfit: "school_uniform"
  }
});
```

**Server emits:**
```javascript
// To other players in the same area
socket.broadcast.emit('character_update', {
  user_id: 1,
  character_id: 1,
  position: {x: 100, y: 200},
  animation_state: "idle",
  equipment: {
    hat: "wizard_hat",
    outfit: "school_uniform"
  }
});
```

## 🔧 Connection Management Events

### ping
Keep-alive ping.

**Client emits:**
```javascript
socket.emit('ping');
```

**Server emits:**
```javascript
socket.emit('pong', {
  timestamp: "2024-01-20T10:00:00Z",
  latency: 45  // ms
});
```

### reconnect
Handle reconnection.

**Client listens:**
```javascript
socket.on('reconnect', (attemptNumber) => {
  console.log('Reconnected after', attemptNumber, 'attempts');
  // Re-subscribe to rooms/channels
  socket.emit('restore_session', {
    room_ids: ['room_123'],
    group_ids: ['group_456']
  });
});
```

## Error Handling

### Error Event Structure
```javascript
socket.on('error', {
  event: 'join_room',  // The event that caused the error
  code: 'ROOM_FULL',   // Error code
  message: '방이 가득 찼습니다',  // User-friendly message
  details: {           // Optional additional details
    room_id: 'room_123',
    max_participants: 2,
    current_participants: 2
  }
});
```

### Common Error Codes
- `AUTH_FAILED`: Authentication failed
- `UNAUTHORIZED`: Not authorized for this action
- `ROOM_NOT_FOUND`: Room does not exist
- `ROOM_FULL`: Room is at capacity
- `ALREADY_IN_ROOM`: User is already in a room
- `INVALID_DATA`: Invalid data format
- `RATE_LIMIT`: Too many requests
- `SERVER_ERROR`: Internal server error

## Best Practices

### 1. Connection Management
```javascript
// Implement reconnection logic
socket.on('disconnect', (reason) => {
  if (reason === 'io server disconnect') {
    // Server disconnected, manually reconnect
    socket.connect();
  }
});

// Handle connection errors
socket.on('connect_error', (error) => {
  console.error('Connection error:', error.message);
});
```

### 2. Event Acknowledgments
```javascript
// Client sends with acknowledgment
socket.emit('join_room', {room_code: 'ABC123'}, (response) => {
  if (response.success) {
    console.log('Joined room:', response.room_id);
  } else {
    console.error('Failed to join:', response.error);
  }
});
```

### 3. Room Management
```javascript
// Clean up on disconnect
socket.on('disconnect', () => {
  // Server automatically removes from rooms
  // But client should clean up local state
  clearLocalRoomState();
});
```

### 4. Error Recovery
```javascript
// Implement retry logic for critical events
async function emitWithRetry(event, data, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await socket.emitWithAck(event, data);
      if (response.success) return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

## Testing WebSocket Events

### Using Socket.IO Client (Development)
```javascript
// Connect with auth token
const socket = io('http://localhost:8000', {
  auth: {
    token: 'Bearer YOUR_JWT_TOKEN'
  }
});

// Test events
socket.on('connect', () => {
  console.log('Connected!');
  
  // Create a room
  socket.emit('create_room', {
    title: 'Test Room',
    subject: 'math',
    difficulty: 'easy'
  });
});

socket.on('room_created', (data) => {
  console.log('Room created:', data);
});
```

### Using wscat (Command Line)
```bash
# Install wscat
npm install -g wscat

# Connect (note: wscat doesn't support Socket.IO, use for raw WebSocket testing)
wscat -c ws://localhost:8000/socket.io/?transport=websocket
```

## Performance Considerations

1. **Event Throttling**: Implement client-side throttling for high-frequency events
2. **Data Compression**: Enable compression for large payloads
3. **Room Limits**: Limit number of participants per room
4. **Message Size**: Limit message size to prevent abuse
5. **Connection Pooling**: Reuse connections when possible

## Security Considerations

1. **Authentication**: Always validate JWT tokens
2. **Authorization**: Check permissions for each event
3. **Input Validation**: Validate all incoming data
4. **Rate Limiting**: Implement per-user rate limits
5. **Data Sanitization**: Sanitize user-generated content
6. **SSL/TLS**: Always use encrypted connections in production