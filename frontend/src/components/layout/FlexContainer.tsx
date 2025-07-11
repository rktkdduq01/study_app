import React from 'react';
import { Box, BoxProps } from '@mui/material';

interface FlexContainerProps extends BoxProps {
  direction?: 'row' | 'column';
  wrap?: boolean;
  spacing?: number;
  alignItems?: 'flex-start' | 'center' | 'flex-end' | 'stretch' | 'baseline';
  justifyContent?: 'flex-start' | 'center' | 'flex-end' | 'space-between' | 'space-around' | 'space-evenly';
}

/**
 * Flexbox 기반 레이아웃 컨테이너
 * 간단한 행/열 레이아웃에 사용됩니다.
 */
export const FlexContainer: React.FC<FlexContainerProps> = ({
  children,
  direction = 'row',
  wrap = false,
  spacing = 2,
  alignItems = 'stretch',
  justifyContent = 'flex-start',
  sx,
  ...props
}) => {
  const gap = spacing * 8; // MUI spacing을 픽셀로 변환

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: direction,
        flexWrap: wrap ? 'wrap' : 'nowrap',
        gap: `${gap}px`,
        alignItems,
        justifyContent,
        ...sx,
      }}
      {...props}
    >
      {children}
    </Box>
  );
};

// 자주 사용되는 프리셋
export const FlexRow: React.FC<FlexContainerProps> = (props) => (
  <FlexContainer direction="row" {...props} />
);

export const FlexColumn: React.FC<FlexContainerProps> = (props) => (
  <FlexContainer direction="column" {...props} />
);

export const FlexCenter: React.FC<FlexContainerProps> = (props) => (
  <FlexContainer alignItems="center" justifyContent="center" {...props} />
);