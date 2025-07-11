import React, { memo } from 'react';
import { Card, CardContent, Typography, Box, Avatar } from '@mui/material';
import { flexBox } from '../../utils/responsive';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  onClick?: () => void;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  subtitle?: string;
}

const StatsCard: React.FC<StatsCardProps> = memo(({
  title,
  value,
  icon,
  color,
  onClick,
  trend,
  subtitle,
}) => {
  return (
    <Card 
      sx={{ 
        height: '100%', 
        textAlign: 'center', 
        p: 2,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.3s ease',
        '&:hover': onClick ? {
          transform: 'translateY(-4px)',
          boxShadow: 4,
        } : {},
      }}
      onClick={onClick}
    >
      <CardContent sx={{ p: 0 }}>
        <Box sx={{ ...flexBox.center, mb: 2 }}>
          <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 'bold', color }}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
            {subtitle}
          </Typography>
        )}
        {trend && (
          <Box sx={{ ...flexBox.center, mt: 1 }}>
            <Typography
              variant="caption"
              sx={{
                color: trend.direction === 'up' ? 'success.main' : 
                       trend.direction === 'down' ? 'error.main' : 'text.secondary',
              }}
            >
              {trend.direction === 'up' ? '↑' : trend.direction === 'down' ? '↓' : '→'}
              {Math.abs(trend.value)}%
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
});

StatsCard.displayName = 'StatsCard';

export default StatsCard;