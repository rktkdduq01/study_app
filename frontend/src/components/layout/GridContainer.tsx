import React from 'react';
import { Box, BoxProps } from '@mui/material';

interface GridContainerProps extends BoxProps {
  spacing?: number;
  columns?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

/**
 * 커스텀 그리드 컨테이너 컴포넌트
 * CSS Grid를 사용하여 반응형 레이아웃을 구현합니다.
 */
export const GridContainer: React.FC<GridContainerProps> = ({
  children,
  spacing = 2,
  columns = { xs: 1, sm: 2, md: 3, lg: 4, xl: 4 },
  sx,
  ...props
}) => {
  const gap = spacing * 8; // MUI spacing을 픽셀로 변환

  return (
    <Box
      sx={{
        display: 'grid',
        gap: `${gap}px`,
        gridTemplateColumns: {
          xs: `repeat(${columns.xs || 1}, 1fr)`,
          sm: `repeat(${columns.sm || 2}, 1fr)`,
          md: `repeat(${columns.md || 3}, 1fr)`,
          lg: `repeat(${columns.lg || 4}, 1fr)`,
          xl: `repeat(${columns.xl || 4}, 1fr)`,
        },
        width: '100%',
        ...sx,
      }}
      {...props}
    >
      {children}
    </Box>
  );
};

// 자주 사용되는 프리셋
export const GridContainer2Cols: React.FC<GridContainerProps> = (props) => (
  <GridContainer columns={{ xs: 1, sm: 2, md: 2, lg: 2, xl: 2 }} {...props} />
);

export const GridContainer3Cols: React.FC<GridContainerProps> = (props) => (
  <GridContainer columns={{ xs: 1, sm: 2, md: 3, lg: 3, xl: 3 }} {...props} />
);

export const GridContainer4Cols: React.FC<GridContainerProps> = (props) => (
  <GridContainer columns={{ xs: 1, sm: 2, md: 3, lg: 4, xl: 4 }} {...props} />
);