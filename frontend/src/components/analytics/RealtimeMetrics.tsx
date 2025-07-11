import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Box, Grid, Chip, Avatar } from '@mui/material';
import { 
  FiberManualRecord as DotIcon,
  Person as PersonIcon,
  TrendingUp as ActivityIcon,
  Event as EventIcon
} from '@mui/icons-material';
import { analyticsService } from '../../services/analytics';

interface RealtimeData {
  global_activity: Record<string, number>;
  active_users: number;
  recent_events: Array<{
    event_name: string;
    event_category: string;
    user_id?: number;
    timestamp: string;
    properties?: any;
  }>;
}

const RealtimeMetrics: React.FC = () => {
  const [data, setData] = useState<RealtimeData | null>(null);
  const [isLive, setIsLive] = useState(true);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    const fetchRealtimeData = async () => {
      try {
        const response = await analyticsService.getRealtimeMetrics();
        setData(response.data);
      } catch (error) {
        console.error('Failed to fetch realtime data:', error);
      }
    };

    fetchRealtimeData();

    if (isLive) {
      interval = setInterval(fetchRealtimeData, 5000); // Update every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isLive]);

  const getEventColor = (category: string) => {
    const colors: Record<string, string> = {
      learning: '#4CAF50',
      quest: '#2196F3',
      achievement: '#FFC107',
      social: '#9C27B0',
      system: '#757575'
    };
    return colors[category] || '#757575';
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">Real-time Analytics</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <DotIcon 
              sx={{ 
                color: isLive ? '#4CAF50' : '#757575',
                animation: isLive ? 'pulse 2s infinite' : 'none',
                mr: 1
              }} 
            />
            <Typography variant="body2" color={isLive ? 'success.main' : 'text.secondary'}>
              {isLive ? 'Live' : 'Paused'}
            </Typography>
          </Box>
        </Box>

        <Grid container spacing={3}>
          {/* Active Users */}
          <Grid size={{ xs: 12, md: 3 }}>
            <Box 
              sx={{ 
                textAlign: 'center',
                p: 3,
                borderRadius: 2,
                backgroundColor: 'primary.main',
                color: 'primary.contrastText'
              }}
            >
              <PersonIcon sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {data?.active_users || 0}
              </Typography>
              <Typography variant="body2">
                Active Users Now
              </Typography>
            </Box>
          </Grid>

          {/* Activity Counters */}
          <Grid size={{ xs: 12, md: 5 }}>
            <Typography variant="subtitle2" gutterBottom>
              Today's Activities
            </Typography>
            <Grid container spacing={1}>
              {Object.entries(data?.global_activity || {}).map(([activity, count]) => (
                <Grid size={6} key={activity}>
                  <Box 
                    sx={{ 
                      p: 2,
                      borderRadius: 1,
                      backgroundColor: 'grey.100',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                      {activity.replace('_', ' ')}
                    </Typography>
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {count}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Grid>

          {/* Recent Events */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="subtitle2" gutterBottom>
              Recent Events
            </Typography>
            <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
              {data?.recent_events?.map((event, index) => (
                <Box 
                  key={index} 
                  sx={{ 
                    display: 'flex',
                    alignItems: 'center',
                    mb: 1,
                    p: 1,
                    borderRadius: 1,
                    backgroundColor: 'grey.50',
                    '&:hover': {
                      backgroundColor: 'grey.100'
                    }
                  }}
                >
                  <Avatar
                    sx={{ 
                      width: 32,
                      height: 32,
                      backgroundColor: getEventColor(event.event_category),
                      mr: 1
                    }}
                  >
                    <EventIcon sx={{ fontSize: 16 }} />
                  </Avatar>
                  <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        textOverflow: 'ellipsis',
                        overflow: 'hidden',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {event.event_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatTimestamp(event.timestamp)}
                    </Typography>
                  </Box>
                  <Chip 
                    label={event.event_category}
                    size="small"
                    sx={{ 
                      ml: 1,
                      backgroundColor: `${getEventColor(event.event_category)}20`,
                      color: getEventColor(event.event_category)
                    }}
                  />
                </Box>
              ))}
            </Box>
          </Grid>
        </Grid>

        <style>
          {`
            @keyframes pulse {
              0% {
                opacity: 1;
              }
              50% {
                opacity: 0.5;
              }
              100% {
                opacity: 1;
              }
            }
          `}
        </style>
      </CardContent>
    </Card>
  );
};

export default RealtimeMetrics;