import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Badge,
  Stack,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  ExitToApp as ExitIcon,
  PlayArrow as PlayIcon,
  People as PeopleIcon,
  EmojiEvents as TrophyIcon,
  Timer as TimerIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useAppSelector } from '../../hooks/useAppSelector';

interface Player {
  id: string;
  name: string;
  avatar: string;
  level: number;
  score: number;
  status: 'ready' | 'playing' | 'waiting';
}

interface MultiplayerRoomProps {
  roomId: string;
  gameType: 'quest' | 'challenge' | 'collaborative';
  onLeave: () => void;
}

const MultiplayerRoom: React.FC<MultiplayerRoomProps> = ({ roomId, gameType, onLeave }) => {
  const { user } = useAppSelector((state) => state.auth);
  const { websocketService, subscribe } = useWebSocket();
  const [players, setPlayers] = useState<Player[]>([]);
  const [isHost, setIsHost] = useState(false);
  const [gameStarted, setGameStarted] = useState(false);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteUsername, setInviteUsername] = useState('');
  const [gameStatus, setGameStatus] = useState<'waiting' | 'ready' | 'playing' | 'finished'>('waiting');
  const [timer, setTimer] = useState(0);

  useEffect(() => {
    // Join the room
    if (user) {
      websocketService.joinMultiplayerRoom(roomId, user.username);
    }

    // Subscribe to multiplayer events
    const unsubscribeJoin = subscribe('player_joined', (data) => {
      console.log('Player joined:', data);
      // Add player to the room
      setPlayers(prev => {
        const exists = prev.some(p => p.id === data.user_id);
        if (!exists) {
          return [...prev, {
            id: data.user_id,
            name: data.user_name,
            avatar: '',
            level: 1,
            score: 0,
            status: 'waiting'
          }];
        }
        return prev;
      });
    });

    const unsubscribeUpdate = subscribe('multiplayer_update', (data) => {
      console.log('Multiplayer update:', data);
      // Handle game state updates
      if (data.type === 'player_ready') {
        setPlayers(prev => prev.map(p => 
          p.id === data.player_id ? { ...p, status: 'ready' } : p
        ));
      } else if (data.type === 'game_start') {
        setGameStarted(true);
        setGameStatus('playing');
      } else if (data.type === 'score_update') {
        setPlayers(prev => prev.map(p => 
          p.id === data.player_id ? { ...p, score: data.score } : p
        ));
      } else if (data.type === 'game_end') {
        setGameStatus('finished');
      }
    });

    return () => {
      unsubscribeJoin();
      unsubscribeUpdate();
      // Leave room on unmount
      websocketService.leaveRoom(`multiplayer_${roomId}`);
    };
  }, [roomId, user, websocketService, subscribe]);

  // Timer for game duration
  useEffect(() => {
    if (gameStatus === 'playing') {
      const interval = setInterval(() => {
        setTimer(prev => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [gameStatus]);

  const handleInvitePlayer = () => {
    if (inviteUsername && user) {
      websocketService.sendMultiplayerInvite(
        inviteUsername,
        user.username,
        gameType,
        roomId
      );
      setInviteDialogOpen(false);
      setInviteUsername('');
    }
  };

  const handleReady = () => {
    websocketService.sendMultiplayerAction(roomId, {
      type: 'player_ready',
      player_id: user?.id
    });
  };

  const handleStartGame = () => {
    if (isHost) {
      websocketService.sendMultiplayerAction(roomId, {
        type: 'game_start'
      });
    }
  };

  const handleLeaveRoom = () => {
    websocketService.sendMultiplayerAction(roomId, {
      type: 'player_leave',
      player_id: user?.id
    });
    onLeave();
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const allPlayersReady = players.every(p => p.status === 'ready');

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="h5">
              {gameType === 'quest' ? 'Quest Room' : 
               gameType === 'challenge' ? 'Challenge Room' : 
               'Collaborative Learning'}
            </Typography>
            <Chip
              icon={<PeopleIcon />}
              label={`${players.length} Players`}
              color="primary"
            />
            {gameStatus === 'playing' && (
              <Chip
                icon={<TimerIcon />}
                label={formatTime(timer)}
                color="secondary"
              />
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              startIcon={<PersonAddIcon />}
              onClick={() => setInviteDialogOpen(true)}
              disabled={gameStarted}
            >
              Invite
            </Button>
            <Button
              startIcon={<ExitIcon />}
              onClick={handleLeaveRoom}
              color="error"
            >
              Leave
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Main Content */}
      <Box sx={{ flex: 1, display: 'flex', gap: 2 }}>
        {/* Players Panel */}
        <Paper sx={{ flex: 1, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Players
          </Typography>
          <List>
            {players.map((player, index) => (
              <ListItem key={player.id}>
                <ListItemAvatar>
                  <Badge
                    overlap="circular"
                    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                    badgeContent={
                      player.status === 'ready' ? 
                        <CheckIcon sx={{ width: 16, height: 16, color: 'success.main' }} /> :
                        player.status === 'playing' ?
                        <PlayIcon sx={{ width: 16, height: 16, color: 'primary.main' }} /> :
                        null
                    }
                  >
                    <Avatar src={player.avatar}>
                      {player.name[0]}
                    </Avatar>
                  </Badge>
                </ListItemAvatar>
                <ListItemText
                  primary={player.name}
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip size="small" label={`Lv ${player.level}`} />
                      {gameStatus === 'playing' && (
                        <Typography variant="body2" color="primary">
                          Score: {player.score}
                        </Typography>
                      )}
                    </Box>
                  }
                />
                {index === 0 && (
                  <Chip
                    size="small"
                    label="Host"
                    color="secondary"
                  />
                )}
              </ListItem>
            ))}
          </List>

          {/* Ready/Start Button */}
          {gameStatus === 'waiting' && (
            <Box sx={{ mt: 2 }}>
              {!isHost ? (
                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleReady}
                  disabled={players.find(p => p.id === user?.id?.toString())?.status === 'ready'}
                >
                  {players.find(p => p.id === user?.id?.toString())?.status === 'ready' ? 'Ready!' : 'Ready Up'}
                </Button>
              ) : (
                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleStartGame}
                  disabled={!allPlayersReady || players.length < 2}
                  startIcon={<PlayIcon />}
                >
                  Start Game
                </Button>
              )}
            </Box>
          )}
        </Paper>

        {/* Game Area */}
        <Paper sx={{ flex: 2, p: 3, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {gameStatus === 'waiting' && (
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                Waiting for players...
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {allPlayersReady ? 
                  'All players ready! Host can start the game.' : 
                  'Waiting for all players to be ready.'}
              </Typography>
            </Box>
          )}

          {gameStatus === 'playing' && (
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" gutterBottom>
                Game in Progress
              </Typography>
              <CircularProgress size={60} />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Complete the challenges to earn points!
              </Typography>
            </Box>
          )}

          {gameStatus === 'finished' && (
            <Box sx={{ textAlign: 'center' }}>
              <TrophyIcon sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                Game Complete!
              </Typography>
              <Typography variant="h6" color="primary">
                Winner: {players.reduce((a, b) => a.score > b.score ? a : b)?.name}
              </Typography>
            </Box>
          )}
        </Paper>
      </Box>

      {/* Invite Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)}>
        <DialogTitle>Invite Friend</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Friend's Username"
            fullWidth
            variant="outlined"
            value={inviteUsername}
            onChange={(e) => setInviteUsername(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleInvitePlayer} variant="contained">
            Send Invite
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MultiplayerRoom;