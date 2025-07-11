import React from 'react';
import {  Card, CardContent, Skeleton, Box } from '@mui/material';
import { GridContainer } from '../layout';

interface QuestListSkeletonProps {
  count?: number;
}

const QuestListSkeleton: React.FC<QuestListSkeletonProps> = ({ count = 6 }) => {
  return (
    <GridContainer spacing={3}>
      {Array.from({ length: count }).map((_, index) => (
        <Box key={index} sx={{ 
          width: { xs: '100%', sm: '50%', md: '33.333%' },
          px: 1.5,
          pb: 3
        }}>
          <Card>
            <CardContent>
              {/* Title */}
              <Skeleton variant="text" width="80%" height={32} />
              
              {/* Chips */}
              <Box sx={{ display: 'flex', gap: 1, my: 1 }}>
                <Skeleton variant="rounded" width={60} height={24} />
                <Skeleton variant="rounded" width={80} height={24} />
              </Box>
              
              {/* Description */}
              <Skeleton variant="text" width="100%" />
              <Skeleton variant="text" width="90%" />
              
              {/* Info */}
              <Box sx={{ mt: 2 }}>
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="50%" />
                <Skeleton variant="text" width="70%" />
              </Box>
              
              {/* Actions */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Skeleton variant="rounded" width={80} height={32} />
                <Skeleton variant="rounded" width={80} height={32} />
              </Box>
            </CardContent>
          </Card>
        </Box>
      ))}
    </GridContainer>
  );
};

export default QuestListSkeleton;