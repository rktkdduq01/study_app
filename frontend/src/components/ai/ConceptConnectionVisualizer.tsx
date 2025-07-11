import React, { useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Tooltip,
  IconButton,
  Card,
  CardContent,
} from '@mui/material';
import {
  Hub,
  ArrowForward,
  Info,
  ZoomIn,
  ZoomOut,
  CenterFocusStrong,
} from '@mui/icons-material';
import { ConceptConnection } from '../../types/ai-learning';

interface ConceptConnectionVisualizerProps {
  connections: ConceptConnection[];
}

const ConceptConnectionVisualizer: React.FC<ConceptConnectionVisualizerProps> = ({
  connections,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = React.useState(1);
  const [selectedConcept, setSelectedConcept] = React.useState<string | null>(null);

  // Group concepts by importance
  const conceptMap = new Map<string, { x: number; y: number; importance: number }>();
  const processedConcepts = new Set<string>();

  connections.forEach(conn => {
    if (!processedConcepts.has(conn.fromConcept)) {
      processedConcepts.add(conn.fromConcept);
    }
    if (!processedConcepts.has(conn.toConcept)) {
      processedConcepts.add(conn.toConcept);
    }
  });

  // Simple layout algorithm
  const concepts = Array.from(processedConcepts);
  const centerX = 300;
  const centerY = 200;
  const radius = 150;

  concepts.forEach((concept, index) => {
    const angle = (2 * Math.PI * index) / concepts.length;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);
    
    // Calculate importance based on connections
    const importance = connections.filter(
      conn => conn.fromConcept === concept || conn.toConcept === concept
    ).length;
    
    conceptMap.set(concept, { x, y, importance });
  });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Apply zoom
    ctx.save();
    ctx.scale(zoom, zoom);

    // Draw connections
    connections.forEach(conn => {
      const from = conceptMap.get(conn.fromConcept);
      const to = conceptMap.get(conn.toConcept);
      
      if (from && to) {
        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        
        // Draw curved line
        const midX = (from.x + to.x) / 2;
        const midY = (from.y + to.y) / 2;
        const curve = 20;
        
        ctx.quadraticCurveTo(
          midX + curve,
          midY - curve,
          to.x,
          to.y
        );
        
        // Style based on importance
        ctx.strokeStyle = 
          conn.importance === 'essential' ? '#1976d2' :
          conn.importance === 'helpful' ? '#4caf50' :
          '#9e9e9e';
        ctx.lineWidth = 
          conn.importance === 'essential' ? 3 :
          conn.importance === 'helpful' ? 2 :
          1;
        
        if (selectedConcept === conn.fromConcept || selectedConcept === conn.toConcept) {
          ctx.lineWidth += 2;
        }
        
        ctx.stroke();
        
        // Draw arrow
        const angle = Math.atan2(to.y - from.y, to.x - from.x);
        const arrowLength = 10;
        
        ctx.beginPath();
        ctx.moveTo(to.x, to.y);
        ctx.lineTo(
          to.x - arrowLength * Math.cos(angle - Math.PI / 6),
          to.y - arrowLength * Math.sin(angle - Math.PI / 6)
        );
        ctx.moveTo(to.x, to.y);
        ctx.lineTo(
          to.x - arrowLength * Math.cos(angle + Math.PI / 6),
          to.y - arrowLength * Math.sin(angle + Math.PI / 6)
        );
        ctx.stroke();
      }
    });

    // Draw concept nodes
    conceptMap.forEach((pos, concept) => {
      const isSelected = selectedConcept === concept;
      const radius = 30 + pos.importance * 5;
      
      // Draw circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = isSelected ? '#e3f2fd' : '#ffffff';
      ctx.fill();
      ctx.strokeStyle = isSelected ? '#1976d2' : '#757575';
      ctx.lineWidth = isSelected ? 3 : 1;
      ctx.stroke();
      
      // Draw text
      ctx.fillStyle = '#212121';
      ctx.font = `${12 + pos.importance}px Arial`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      // Word wrap for long concepts
      const words = concept.split(' ');
      const lineHeight = 14;
      let line = '';
      let y = pos.y - (words.length - 1) * lineHeight / 2;
      
      words.forEach((word, index) => {
        const testLine = line + word + ' ';
        const metrics = ctx.measureText(testLine);
        const testWidth = metrics.width;
        
        if (testWidth > radius * 1.5 && index > 0) {
          ctx.fillText(line, pos.x, y);
          line = word + ' ';
          y += lineHeight;
        } else {
          line = testLine;
        }
      });
      ctx.fillText(line, pos.x, y);
    });

    ctx.restore();
  }, [connections, zoom, selectedConcept]);

  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) / zoom;
    const y = (event.clientY - rect.top) / zoom;

    // Check if click is on a concept
    let clickedConcept: string | null = null;
    conceptMap.forEach((pos, concept) => {
      const radius = 30 + pos.importance * 5;
      const distance = Math.sqrt(Math.pow(x - pos.x, 2) + Math.pow(y - pos.y, 2));
      
      if (distance <= radius) {
        clickedConcept = concept;
      }
    });

    setSelectedConcept(clickedConcept);
  };

  const getConnectionsForConcept = (concept: string) => {
    return connections.filter(
      conn => conn.fromConcept === concept || conn.toConcept === concept
    );
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Hub />
            Concept Map
          </Typography>
          
          <Box>
            <IconButton onClick={() => setZoom(zoom * 1.2)} size="small">
              <ZoomIn />
            </IconButton>
            <IconButton onClick={() => setZoom(zoom / 1.2)} size="small">
              <ZoomOut />
            </IconButton>
            <IconButton onClick={() => setZoom(1)} size="small">
              <CenterFocusStrong />
            </IconButton>
          </Box>
        </Box>

        <Box sx={{ position: 'relative' }}>
          <canvas
            ref={canvasRef}
            width={600}
            height={400}
            style={{
              border: '1px solid #e0e0e0',
              borderRadius: 8,
              cursor: 'pointer',
              width: '100%',
              maxWidth: 600,
            }}
            onClick={handleCanvasClick}
          />
          
          {/* Legend */}
          <Box sx={{ position: 'absolute', bottom: 8, left: 8, bgcolor: 'rgba(255,255,255,0.9)', p: 1, borderRadius: 1 }}>
            <Typography variant="caption" display="block">
              Connection Importance:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Chip
                label="Essential"
                size="small"
                sx={{ bgcolor: '#1976d2', color: 'white' }}
              />
              <Chip
                label="Helpful"
                size="small"
                sx={{ bgcolor: '#4caf50', color: 'white' }}
              />
              <Chip
                label="Extension"
                size="small"
                sx={{ bgcolor: '#9e9e9e', color: 'white' }}
              />
            </Box>
          </Box>
        </Box>

        {/* Selected Concept Details */}
        {selectedConcept && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="subtitle2" gutterBottom>
              {selectedConcept}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Connections:
            </Typography>
            {getConnectionsForConcept(selectedConcept).map((conn, index) => (
              <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                {conn.fromConcept === selectedConcept ? (
                  <>
                    <Typography variant="caption">{conn.fromConcept}</Typography>
                    <ArrowForward fontSize="small" />
                    <Typography variant="caption">{conn.toConcept}</Typography>
                  </>
                ) : (
                  <>
                    <Typography variant="caption">{conn.fromConcept}</Typography>
                    <ArrowForward fontSize="small" />
                    <Typography variant="caption">{conn.toConcept}</Typography>
                  </>
                )}
                <Typography variant="caption" color="text.secondary">
                  ({conn.relationship})
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Click on concepts to see their connections
        </Typography>
      </CardContent>
    </Card>
  );
};

export default ConceptConnectionVisualizer;