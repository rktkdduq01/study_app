import React from 'react';
import { Box, BoxProps } from '@mui/material';

interface GridItemProps extends BoxProps {
  colSpan?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  } | number;
  rowSpan?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  } | number;
}

/**
 * 커스텀 그리드 아이템 컴포넌트
 * GridContainer 내부에서 사용되며, 필요에 따라 여러 열이나 행을 차지할 수 있습니다.
 */
export const GridItem: React.FC<GridItemProps> = ({
  children,
  colSpan,
  rowSpan,
  sx,
  ...props
}) => {
  const getSpanValue = (span: typeof colSpan, property: 'gridColumn' | 'gridRow') => {
    if (!span) return {};
    
    if (typeof span === 'number') {
      return { [property]: `span ${span}` };
    }

    return {
      [property]: {
        xs: span.xs ? `span ${span.xs}` : undefined,
        sm: span.sm ? `span ${span.sm}` : undefined,
        md: span.md ? `span ${span.md}` : undefined,
        lg: span.lg ? `span ${span.lg}` : undefined,
        xl: span.xl ? `span ${span.xl}` : undefined,
      },
    };
  };

  return (
    <Box
      sx={{
        ...getSpanValue(colSpan, 'gridColumn'),
        ...getSpanValue(rowSpan, 'gridRow'),
        ...sx,
      }}
      {...props}
    >
      {children}
    </Box>
  );
};

// 자주 사용되는 프리셋
export const GridItemFull: React.FC<BoxProps> = ({ sx, ...props }) => (
  <GridItem colSpan={{ xs: 1, sm: 2, md: 3, lg: 4, xl: 4 }} sx={sx} {...props} />
);

export const GridItemHalf: React.FC<BoxProps> = ({ sx, ...props }) => (
  <GridItem colSpan={{ xs: 1, sm: 1, md: 2, lg: 2, xl: 2 }} sx={sx} {...props} />
);