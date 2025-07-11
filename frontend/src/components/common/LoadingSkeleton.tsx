import React, { memo } from 'react';
import { Box, Card, CardContent, Skeleton } from '@mui/material';
import { GridContainer } from '../layout';
import { flexBox } from '../../utils/responsive';

interface LoadingSkeletonProps {
  type?: 'card' | 'list' | 'table' | 'custom';
  count?: number;
  columns?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
  };
  customContent?: React.ReactNode;
}

const LoadingSkeleton: React.FC<LoadingSkeletonProps> = memo(({ 
  type = 'card', 
  count = 6,
  columns = { xs: 1, sm: 2, md: 3, lg: 4 },
  customContent
}) => {
  if (customContent) {
    return <>{customContent}</>;
  }

  const renderCardSkeleton = () => (
    <Card>
      <CardContent>
        <Box sx={{ ...flexBox.alignCenter, gap: 2, mb: 2 }}>
          <Skeleton variant="circular" width={56} height={56} />
          <Box>
            <Skeleton variant="text" width={120} />
            <Skeleton variant="text" width={80} />
          </Box>
        </Box>
        <Skeleton variant="text" width="100%" />
        <Skeleton variant="text" width="60%" />
      </CardContent>
    </Card>
  );

  const renderListSkeleton = () => (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ ...flexBox.alignCenter, gap: 2 }}>
        <Skeleton variant="circular" width={48} height={48} />
        <Box sx={{ flex: 1 }}>
          <Skeleton variant="text" width="30%" />
          <Skeleton variant="text" width="50%" />
        </Box>
        <Skeleton variant="rectangular" width={80} height={32} />
      </Box>
    </Box>
  );

  const renderTableSkeleton = () => (
    <Box>
      <Skeleton variant="rectangular" width="100%" height={40} sx={{ mb: 2 }} />
      {Array.from({ length: count }).map((_, index) => (
        <Box key={index} sx={{ ...flexBox.alignCenter, gap: 2, mb: 1 }}>
          <Skeleton variant="text" width="20%" />
          <Skeleton variant="text" width="30%" />
          <Skeleton variant="text" width="25%" />
          <Skeleton variant="text" width="15%" />
          <Skeleton variant="text" width="10%" />
        </Box>
      ))}
    </Box>
  );

  if (type === 'list') {
    return (
      <Box>
        {Array.from({ length: count }).map((_, index) => (
          <React.Fragment key={index}>
            {renderListSkeleton()}
          </React.Fragment>
        ))}
      </Box>
    );
  }

  if (type === 'table') {
    return renderTableSkeleton();
  }

  // Card type (default)
  return (
    <GridContainer columns={columns} spacing={3}>
      {Array.from({ length: count }).map((_, index) => (
        <Box key={index}>
          {renderCardSkeleton()}
        </Box>
      ))}
    </GridContainer>
  );
});

LoadingSkeleton.displayName = 'LoadingSkeleton';

export default LoadingSkeleton;