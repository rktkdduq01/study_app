import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Avatar,
  Chip,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useNavigate } from 'react-router-dom';

interface Invitation {
  inviter_id: string;
  inviter_name: string;
  game_type: 'quest' | 'challenge' | 'collaborative';
  room_id: string;
  timestamp: string;
}

const MultiplayerInviteHandler: React.FC = () => {
  const { subscribe } = useWebSocket();
  const navigate = useNavigate();
  const [invitation, setInvitation] = useState<Invitation | null>(null);

  useEffect(() => {
    const unsubscribe = subscribe('multiplayer_invitation', (data: Invitation) => {
      console.log('Received multiplayer invitation:', data);
      setInvitation(data);
    });

    return () => {
      unsubscribe();
    };
  }, [subscribe]);

  const handleAccept = () => {
    if (invitation) {
      // Navigate to multiplayer room
      navigate(`/student/multiplayer/${invitation.room_id}`, {
        state: { gameType: invitation.game_type }
      });
      setInvitation(null);
    }
  };

  const handleDecline = () => {
    setInvitation(null);
  };

  const getGameTypeLabel = (type: string) => {
    switch (type) {
      case 'quest':
        return 'Quest Battle';
      case 'challenge':
        return 'Speed Challenge';
      case 'collaborative':
        return 'Team Learning';
      default:
        return 'Multiplayer Game';
    }
  };

  const getGameTypeColor = (type: string): 'primary' | 'secondary' | 'success' => {
    switch (type) {
      case 'quest':
        return 'primary';
      case 'challenge':
        return 'secondary';
      case 'collaborative':
        return 'success';
      default:
        return 'primary';
    }
  };

  return (
    <Dialog 
      open={!!invitation} 
      onClose={handleDecline}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PlayIcon color="primary" />
          Multiplayer Invitation
        </Box>
      </DialogTitle>
      <DialogContent>
        {invitation && (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Avatar 
              sx={{ 
                width: 80, 
                height: 80, 
                mx: 'auto', 
                mb: 2,
                bgcolor: 'primary.main' 
              }}
            >
              {invitation.inviter_name[0]}
            </Avatar>
            <Typography variant="h6" gutterBottom>
              {invitation.inviter_name} invited you to play!
            </Typography>
            <Chip
              label={getGameTypeLabel(invitation.game_type)}
              color={getGameTypeColor(invitation.game_type)}
              size="large"
              sx={{ mt: 1 }}
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Join the game room to compete and learn together!
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions sx={{ p: 2, gap: 1 }}>
        <Button
          onClick={handleDecline}
          color="inherit"
          startIcon={<CancelIcon />}
        >
          Decline
        </Button>
        <Button
          onClick={handleAccept}
          variant="contained"
          startIcon={<PlayIcon />}
        >
          Join Game
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MultiplayerInviteHandler;