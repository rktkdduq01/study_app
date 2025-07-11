import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Tooltip,
  Chip,
  Button,
  Dialog,
  DialogContent,
  DialogActions,
  Slider,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Alert,
} from '@mui/material';
import {
  ZoomIn,
  ZoomOut,
  Fullscreen,
  FullscreenExit,
  Info,
  TouchApp,
  Palette,
  Replay,
  Download,
  Share,
  PlayArrow,
  Pause,
  SkipNext,
  SkipPrevious,
} from '@mui/icons-material';
import { VisualAid, InteractionPoint } from '../../types/ai-learning';

interface ConceptVisualizationProps {
  visualAid: VisualAid;
}

const ConceptVisualization: React.FC<ConceptVisualizationProps> = ({ visualAid }) => {
  const [zoom, setZoom] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedPoint, setSelectedPoint] = useState<InteractionPoint | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [showControls, setShowControls] = useState(true);
  const [colorMode, setColorMode] = useState<'normal' | 'contrast' | 'colorblind'>('normal');
  const [annotationsVisible, setAnnotationsVisible] = useState(true);

  const handleZoomIn = () => setZoom(Math.min(zoom * 1.2, 3));
  const handleZoomOut = () => setZoom(Math.max(zoom / 1.2, 0.5));
  const handleResetZoom = () => setZoom(1);

  const handleInteractionPointClick = (point: InteractionPoint) => {
    setSelectedPoint(point);
  };

  const renderDiagram = () => (
    <Box sx={{ position: 'relative', overflow: 'hidden' }}>
      <Box
        sx={{
          transform: `scale(${zoom})`,
          transformOrigin: 'center',
          transition: 'transform 0.3s',
          position: 'relative',
        }}
      >
        <img
          src={visualAid.url}
          alt={visualAid.description}
          style={{
            maxWidth: '100%',
            height: 'auto',
            filter: colorMode === 'contrast' ? 'contrast(1.5)' : 
                   colorMode === 'colorblind' ? 'hue-rotate(90deg)' : 'none',
          }}
        />
        
        {/* Interaction Points */}
        {annotationsVisible && visualAid.interactionPoints?.map((point) => (
          <Tooltip key={point.id} title={point.label} arrow>
            <IconButton
              sx={{
                position: 'absolute',
                left: `${point.coordinates.x}%`,
                top: `${point.coordinates.y}%`,
                transform: 'translate(-50%, -50%)',
                bgcolor: 'primary.main',
                color: 'white',
                width: 32,
                height: 32,
                '&:hover': {
                  bgcolor: 'primary.dark',
                  transform: 'translate(-50%, -50%) scale(1.2)',
                },
              }}
              onClick={() => handleInteractionPointClick(point)}
            >
              <TouchApp fontSize="small" />
            </IconButton>
          </Tooltip>
        ))}
      </Box>
      
      {/* Controls */}
      <Paper
        sx={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          p: 1,
          display: 'flex',
          gap: 1,
          opacity: showControls ? 1 : 0,
          transition: 'opacity 0.3s',
        }}
        onMouseEnter={() => setShowControls(true)}
      >
        <Tooltip title="Zoom In">
          <IconButton size="small" onClick={handleZoomIn}>
            <ZoomIn />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out">
          <IconButton size="small" onClick={handleZoomOut}>
            <ZoomOut />
          </IconButton>
        </Tooltip>
        <Tooltip title="Reset">
          <IconButton size="small" onClick={handleResetZoom}>
            <Replay />
          </IconButton>
        </Tooltip>
        <Tooltip title="Toggle Annotations">
          <IconButton 
            size="small" 
            onClick={() => setAnnotationsVisible(!annotationsVisible)}
            color={annotationsVisible ? 'primary' : 'inherit'}
          >
            <Info />
          </IconButton>
        </Tooltip>
        <Tooltip title="Color Mode">
          <IconButton size="small" onClick={(e) => {/* Open color menu */}}>
            <Palette />
          </IconButton>
        </Tooltip>
        <Tooltip title="Fullscreen">
          <IconButton size="small" onClick={() => setIsFullscreen(true)}>
            <Fullscreen />
          </IconButton>
        </Tooltip>
      </Paper>
    </Box>
  );

  const renderAnimation = () => (
    <Box sx={{ position: 'relative' }}>
      <video
        src={visualAid.url}
        style={{
          width: '100%',
          height: 'auto',
        }}
        controls={false}
      />
      
      {/* Custom Controls */}
      <Paper sx={{ p: 2, mt: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => setIsPlaying(!isPlaying)}>
            {isPlaying ? <Pause /> : <PlayArrow />}
          </IconButton>
          
          <Slider
            value={currentFrame}
            onChange={(_, value) => setCurrentFrame(value as number)}
            max={100}
            sx={{ flex: 1 }}
          />
          
          <Typography variant="body2">
            {Math.floor(currentFrame)}%
          </Typography>
        </Box>
        
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
          {visualAid.description}
        </Typography>
      </Paper>
    </Box>
  );

  const renderInteractive = () => (
    <Box>
      <iframe
        src={visualAid.url}
        style={{
          width: '100%',
          height: '500px',
          border: 'none',
          borderRadius: 8,
        }}
        title={visualAid.description}
      />
      
      <Alert severity="info" sx={{ mt: 2 }}>
        <Typography variant="body2">
          This is an interactive element. Click and drag to explore!
        </Typography>
      </Alert>
      
      {/* Instructions */}
      {visualAid.interactionPoints && visualAid.interactionPoints.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Key Areas to Explore:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {visualAid.interactionPoints.map((point) => (
              <Chip
                key={point.id}
                label={point.label}
                onClick={() => handleInteractionPointClick(point)}
                icon={<TouchApp />}
                size="small"
              />
            ))}
          </Box>
        </Box>
      )}
    </Box>
  );

  const renderContent = () => {
    switch (visualAid.type) {
      case 'diagram':
        return renderDiagram();
      case 'animation':
        return renderAnimation();
      case 'interactive':
        return renderInteractive();
      default:
        return (
          <img
            src={visualAid.url}
            alt={visualAid.description}
            style={{ width: '100%', height: 'auto' }}
          />
        );
    }
  };

  return (
    <>
      <Box
        onMouseEnter={() => setShowControls(true)}
        onMouseLeave={() => setShowControls(false)}
      >
        {renderContent()}
      </Box>

      {/* Interaction Point Dialog */}
      <Dialog
        open={!!selectedPoint}
        onClose={() => setSelectedPoint(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogContent>
          <Typography variant="h6" gutterBottom>
            {selectedPoint?.label}
          </Typography>
          <Typography variant="body1">
            {selectedPoint?.explanation}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedPoint(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Fullscreen Dialog */}
      <Dialog
        open={isFullscreen}
        onClose={() => setIsFullscreen(false)}
        fullScreen
        sx={{ bgcolor: 'black' }}
      >
        <Box sx={{ position: 'relative', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <IconButton
            sx={{ position: 'absolute', top: 16, right: 16, color: 'white' }}
            onClick={() => setIsFullscreen(false)}
          >
            <FullscreenExit />
          </IconButton>
          
          <Box sx={{ maxWidth: '90vw', maxHeight: '90vh' }}>
            {renderContent()}
          </Box>
        </Box>
      </Dialog>
    </>
  );
};

export default ConceptVisualization;