import React from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Avatar,
} from '@mui/material';
import {
  Star,
  Timer,
  School,
  TrendingUp,
  CheckCircle,
  NavigateNext,
  EmojiEvents,
  Lightbulb,
  LocalFireDepartment,
} from '@mui/icons-material';
import { QuestRecommendation } from '../../types/ai-tutor';

interface QuestRecommendationCardProps {
  recommendation: QuestRecommendation;
  onSelect: () => void;
  compact?: boolean;
}

const QuestRecommendationCard: React.FC<QuestRecommendationCardProps> = ({
  recommendation,
  onSelect,
  compact = false,
}) => {
  const getMatchColor = (score: number) => {
    if (score >= 90) return 'success';
    if (score >= 70) return 'warning';
    return 'error';
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy': return 'success';
      case 'medium': return 'warning';
      case 'hard': return 'error';
      case 'expert': return 'secondary';
      default: return 'default';
    }
  };

  if (compact) {
    return (
      <Card sx={{ mb: 1, cursor: 'pointer' }} onClick={onSelect}>
        <CardContent sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                {recommendation.title}
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                <Chip
                  size="small"
                  label={`${recommendation.matchScore}% match`}
                  color={getMatchColor(recommendation.matchScore)}
                />
                <Chip
                  size="small"
                  label={recommendation.difficulty}
                  color={getDifficultyColor(recommendation.difficulty)}
                />
                <Chip
                  size="small"
                  icon={<Timer />}
                  label={`${recommendation.estimatedTime}m`}
                />
              </Box>
            </Box>
            <NavigateNext />
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ mb: 2, position: 'relative', overflow: 'visible' }}>
      {/* Match Score Badge */}
      <Box
        sx={{
          position: 'absolute',
          top: -10,
          right: 16,
          bgcolor: 'background.paper',
          borderRadius: 2,
          px: 1,
          py: 0.5,
          boxShadow: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <LocalFireDepartment 
            sx={{ 
              fontSize: 16, 
              color: getMatchColor(recommendation.matchScore) === 'success' ? 'success.main' : 'warning.main' 
            }} 
          />
          <Typography variant="caption" fontWeight="bold">
            {recommendation.matchScore}% Match
          </Typography>
        </Box>
      </Box>

      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ mt: 1 }}>
          {recommendation.title}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          {recommendation.reason}
        </Typography>

        {/* Quest Details */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
          <Chip
            size="small"
            label={recommendation.difficulty}
            color={getDifficultyColor(recommendation.difficulty)}
            icon={<Star />}
          />
          <Chip
            size="small"
            label={`${recommendation.estimatedTime} min`}
            icon={<Timer />}
            variant="outlined"
          />
          {recommendation.concepts.slice(0, 2).map((concept, index) => (
            <Chip
              key={index}
              size="small"
              label={concept}
              icon={<School />}
              variant="outlined"
            />
          ))}
          {recommendation.concepts.length > 2 && (
            <Chip
              size="small"
              label={`+${recommendation.concepts.length - 2} more`}
              variant="outlined"
            />
          )}
        </Box>

        {/* Benefits */}
        <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <EmojiEvents fontSize="small" color="primary" />
          What you'll gain:
        </Typography>
        <List dense sx={{ mb: 2 }}>
          {recommendation.benefits.slice(0, 3).map((benefit, index) => (
            <ListItem key={index} disableGutters>
              <ListItemIcon sx={{ minWidth: 28 }}>
                <CheckCircle fontSize="small" color="success" />
              </ListItemIcon>
              <ListItemText 
                primary={benefit}
                primaryTypographyProps={{ variant: 'body2' }}
              />
            </ListItem>
          ))}
        </List>

        {/* Prerequisites */}
        {recommendation.prerequisites && recommendation.prerequisites.length > 0 && (
          <>
            <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Lightbulb fontSize="small" color="warning" />
              Prerequisites:
            </Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 2 }}>
              {recommendation.prerequisites.map((prereq, index) => (
                <Chip
                  key={index}
                  label={prereq}
                  size="small"
                  variant="outlined"
                  color="warning"
                />
              ))}
            </Box>
          </>
        )}

        {/* Match Progress Bar */}
        <Box sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="caption" color="text.secondary">
              AI Confidence
            </Typography>
            <Typography variant="caption" fontWeight="bold">
              {recommendation.matchScore}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={recommendation.matchScore} 
            color={getMatchColor(recommendation.matchScore)}
            sx={{ height: 6, borderRadius: 3 }}
          />
        </Box>
      </CardContent>
      
      <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
        <Button
          size="small"
          startIcon={<TrendingUp />}
        >
          View Details
        </Button>
        <Button
          variant="contained"
          size="small"
          onClick={onSelect}
          endIcon={<NavigateNext />}
        >
          Start Quest
        </Button>
      </CardActions>
    </Card>
  );
};

export default QuestRecommendationCard;