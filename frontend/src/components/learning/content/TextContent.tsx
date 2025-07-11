import React, { useEffect, useRef } from 'react';
import { Box, Typography, Paper } from '@mui/material';

interface TextContentProps {
  text: string;
  onProgressUpdate: (progress: number) => void;
  onComplete: () => void;
}

const TextContent: React.FC<TextContentProps> = ({
  text,
  onProgressUpdate,
  onComplete,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      if (contentRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = contentRef.current;
        const progress = (scrollTop / (scrollHeight - clientHeight)) * 100;
        onProgressUpdate(Math.min(progress, 100));
        
        if (progress >= 90) {
          onComplete();
        }
      }
    };

    const element = contentRef.current;
    element?.addEventListener('scroll', handleScroll);
    return () => element?.removeEventListener('scroll', handleScroll);
  }, [onProgressUpdate, onComplete]);

  return (
    <Paper
      ref={contentRef}
      sx={{
        p: 4,
        maxHeight: '60vh',
        overflow: 'auto',
        '&::-webkit-scrollbar': {
          width: 8,
        },
        '&::-webkit-scrollbar-track': {
          bgcolor: 'grey.200',
        },
        '&::-webkit-scrollbar-thumb': {
          bgcolor: 'primary.main',
          borderRadius: 4,
        },
      }}
    >
      <Typography
        variant="body1"
        sx={{
          fontSize: '1.1rem',
          lineHeight: 1.8,
          whiteSpace: 'pre-wrap',
        }}
      >
        {text}
      </Typography>
    </Paper>
  );
};

export default TextContent;