import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  IconButton,
  Paper,
  Slider,
  Stack,
  Tooltip,
  Fab,
  Zoom,
  Card,
  CardContent,
  Divider,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  VolumeUp,
  VolumeOff,
  Replay10,
  Forward10,
  Fullscreen,
  Speed,
  Subtitles,
  NavigateNext,
  NavigateBefore,
  CheckCircle,
} from '@mui/icons-material';
import { ContentType, LearningContent } from '../../types/learning';
import VideoPlayer from './content/VideoPlayer';
import TextContent from './content/TextContent';
import InteractiveContent from './content/InteractiveContent';
import DiagramViewer from './content/DiagramViewer';
import SimulationPlayer from './content/SimulationPlayer';

interface LearningContentViewerProps {
  content: LearningContent;
  onComplete: () => void;
  onBookmark?: (timestamp: number) => void;
}

const LearningContentViewer: React.FC<LearningContentViewerProps> = ({
  content,
  onComplete,
  onBookmark,
}) => {
  const [completed, setCompleted] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [readingProgress, setReadingProgress] = useState(0);

  // Handle different content types
  const renderContent = () => {
    switch (content.type) {
      case ContentType.VIDEO:
        return (
          <VideoPlayer
            videoUrl={content.content.videoUrl!}
            subtitles={content.content.subtitles}
            onComplete={handleContentComplete}
          />
        );
      
      case ContentType.TEXT:
        return (
          <TextContent
            text={content.content.text || content.content.richText}
            onProgressUpdate={setReadingProgress}
            onComplete={handleContentComplete}
          />
        );
      
      case ContentType.INTERACTIVE:
        return (
          <InteractiveContent
            url={content.content.interactiveUrl}
            data={content.content.interactiveData}
            onComplete={handleContentComplete}
          />
        );
      
      case ContentType.DIAGRAM:
        return (
          <DiagramViewer
            data={content.content.diagramData}
            onComplete={handleContentComplete}
          />
        );
      
      case ContentType.SIMULATION:
        return (
          <SimulationPlayer
            config={content.content.simulationConfig}
            onComplete={handleContentComplete}
          />
        );
      
      default:
        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" color="text.secondary">
              Content type not supported yet
            </Typography>
          </Box>
        );
    }
  };

  const handleContentComplete = () => {
    setCompleted(true);
    // Show completion animation
    setTimeout(() => {
      onComplete();
    }, 1500);
  };

  // Completion animation
  if (completed) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '400px',
          position: 'relative',
        }}
      >
        <Zoom in={completed}>
          <Box sx={{ textAlign: 'center' }}>
            <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Great Job! 🎉
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              You've completed the learning content!
            </Typography>
            <Typography variant="h6" color="primary">
              +25 XP Earned!
            </Typography>
          </Box>
        </Zoom>
      </Box>
    );
  }

  return (
    <Box sx={{ position: 'relative', height: '100%' }}>
      {/* Content Area */}
      <Box sx={{ mb: 3 }}>
        {renderContent()}
      </Box>

      {/* Content Navigation (for multi-page content) */}
      {content.content.text && content.content.text.length > 1000 && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
          <IconButton
            disabled={currentPage === 0}
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            <NavigateBefore />
          </IconButton>
          
          <Typography variant="body2" color="text.secondary">
            Page {currentPage + 1}
          </Typography>
          
          <IconButton
            disabled={readingProgress >= 100}
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            <NavigateNext />
          </IconButton>
        </Box>
      )}

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 4 }}>
        <Button
          variant="contained"
          size="large"
          onClick={handleContentComplete}
          startIcon={<CheckCircle />}
          disabled={content.type === ContentType.TEXT && readingProgress < 90}
        >
          Mark as Complete
        </Button>
        
        {onBookmark && (
          <Button
            variant="outlined"
            onClick={() => onBookmark(Date.now())}
          >
            Add Bookmark
          </Button>
        )}
      </Box>

      {/* Progress indicator for text content */}
      {content.type === ContentType.TEXT && (
        <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0 }}>
          <LinearProgress
            variant="determinate"
            value={readingProgress}
            sx={{ height: 4 }}
          />
        </Box>
      )}
    </Box>
  );
};

// Placeholder components - these would be fully implemented
const LinearProgress = ({ variant, value, sx }: any) => (
  <Box sx={{ width: '100%', bgcolor: 'grey.300', ...sx }}>
    <Box sx={{ width: `${value}%`, bgcolor: 'primary.main', height: '100%' }} />
  </Box>
);

export default LearningContentViewer;