import { Theme } from '@mui/material/styles';
import { SxProps } from '@mui/system';

// Breakpoint definitions
export const breakpoints = {
  xs: 0,     // Extra small devices (phones, less than 576px)
  sm: 576,   // Small devices (landscape phones, 576px and up)
  md: 768,   // Medium devices (tablets, 768px and up)
  lg: 992,   // Large devices (desktops, 992px and up)
  xl: 1200,  // Extra large devices (large desktops, 1200px and up)
  xxl: 1400  // Extra extra large devices (larger desktops, 1400px and up)
};

// Common responsive values
export const responsiveValues = {
  // Spacing
  spacing: {
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4,
    xl: 5
  },
  
  // Container max widths
  container: {
    xs: '100%',
    sm: '540px',
    md: '720px', 
    lg: '960px',
    xl: '1140px',
    xxl: '1320px'
  },
  
  // Grid columns
  columns: {
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4,
    xl: 6
  },
  
  // Font sizes
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    md: '1rem',
    lg: '1.125rem',
    xl: '1.25rem'
  },
  
  // Card dimensions
  cardHeight: {
    xs: 200,
    sm: 250,
    md: 300,
    lg: 350,
    xl: 400
  },
  
  // Avatar sizes
  avatarSize: {
    xs: 32,
    sm: 40,
    md: 48,
    lg: 56,
    xl: 64
  }
};

// Helper functions for responsive design
export const getResponsiveValue = (
  values: Record<string, any>,
  breakpoint: keyof typeof breakpoints = 'md'
): any => {
  const keys = Object.keys(values);
  const breakpointKeys = Object.keys(breakpoints);
  const currentIndex = breakpointKeys.indexOf(breakpoint);
  
  // Find the appropriate value for the current breakpoint
  for (let i = currentIndex; i >= 0; i--) {
    const key = breakpointKeys[i];
    if (values[key] !== undefined) {
      return values[key];
    }
  }
  
  return values[keys[0]];
};

// Flexbox utilities
export const flexBox = {
  center: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },
  
  spaceBetween: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  
  column: {
    display: 'flex',
    flexDirection: 'column'
  },
  
  columnCenter: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
  },
  
  wrap: {
    display: 'flex',
    flexWrap: 'wrap'
  },
  
  alignCenter: {
    display: 'flex',
    alignItems: 'center'
  },
  
  responsive: {
    xs: { flexDirection: 'column' },
    sm: { flexDirection: 'row' }
  }
} as const;

// Grid utilities
export const gridLayout = {
  // Auto-fit grid with minimum column width
  autoFit: (minWidth: number = 280) => ({
    display: 'grid',
    gridTemplateColumns: `repeat(auto-fit, minmax(${minWidth}px, 1fr))`,
    gap: 2
  }),
  
  // Responsive columns
  responsiveColumns: {
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4,
    xl: 6
  },
  
  // Card grid
  cardGrid: {
    xs: 1,
    sm: 2,
    md: 2,
    lg: 3,
    xl: 4
  },
  
  // List grid
  listGrid: {
    xs: 1,
    sm: 1,
    md: 2,
    lg: 2,
    xl: 3
  }
};

// Container utilities
export const containerStyles = {
  // Responsive padding
  responsivePadding: {
    px: { xs: 2, sm: 3, md: 4 },
    py: { xs: 2, sm: 3, md: 4 }
  },
  
  // Full width with max constraints
  constrainedWidth: {
    width: '100%',
    maxWidth: { xs: '100%', sm: '540px', md: '720px', lg: '960px', xl: '1140px' },
    mx: 'auto'
  },
  
  // Section spacing
  sectionSpacing: {
    mb: { xs: 4, sm: 6, md: 8 }
  }
};

// Typography utilities
export const typographyStyles = {
  // Responsive headings
  heading: {
    fontSize: { xs: '1.5rem', sm: '2rem', md: '2.5rem' },
    fontWeight: 'bold',
    lineHeight: 1.2
  },
  
  subheading: {
    fontSize: { xs: '1.125rem', sm: '1.25rem', md: '1.5rem' },
    fontWeight: 600,
    lineHeight: 1.3
  },
  
  body: {
    fontSize: { xs: '0.875rem', sm: '1rem' },
    lineHeight: 1.6
  },
  
  caption: {
    fontSize: { xs: '0.75rem', sm: '0.875rem' },
    lineHeight: 1.4
  }
};

// Component-specific responsive styles
export const componentStyles = {
  // Card responsive styles
  card: {
    height: { xs: 'auto', md: '100%' },
    minHeight: { xs: 200, sm: 250, md: 300 },
    '& .MuiCardContent-root': {
      padding: { xs: 2, sm: 3 }
    }
  },
  
  // Button responsive styles
  button: {
    fontSize: { xs: '0.875rem', sm: '1rem' },
    padding: { xs: '8px 16px', sm: '10px 20px' },
    minWidth: { xs: 'auto', sm: '64px' }
  },
  
  // Avatar responsive styles
  avatar: {
    width: { xs: 32, sm: 40, md: 48 },
    height: { xs: 32, sm: 40, md: 48 }
  },
  
  // Chip responsive styles
  chip: {
    fontSize: { xs: '0.75rem', sm: '0.875rem' },
    height: { xs: 24, sm: 32 }
  },
  
  // Dialog responsive styles
  dialog: {
    '& .MuiDialog-paper': {
      margin: { xs: 2, sm: 4 },
      width: { xs: 'calc(100% - 32px)', sm: 'auto' },
      maxWidth: { xs: 'none', sm: '600px' }
    }
  },
  
  // Table responsive styles
  table: {
    '& .MuiTableCell-root': {
      padding: { xs: '8px', sm: '16px' },
      fontSize: { xs: '0.875rem', sm: '1rem' }
    }
  }
};

// Media query helpers
export const mediaQueries = {
  up: (breakpoint: keyof typeof breakpoints) => 
    `@media (min-width: ${breakpoints[breakpoint]}px)`,
  
  down: (breakpoint: keyof typeof breakpoints) => 
    `@media (max-width: ${breakpoints[breakpoint] - 1}px)`,
  
  between: (start: keyof typeof breakpoints, end: keyof typeof breakpoints) =>
    `@media (min-width: ${breakpoints[start]}px) and (max-width: ${breakpoints[end] - 1}px)`,
  
  only: (breakpoint: keyof typeof breakpoints) => {
    const keys = Object.keys(breakpoints) as Array<keyof typeof breakpoints>;
    const index = keys.indexOf(breakpoint);
    const nextKey = keys[index + 1];
    
    if (nextKey) {
      return `@media (min-width: ${breakpoints[breakpoint]}px) and (max-width: ${breakpoints[nextKey] - 1}px)`;
    } else {
      return `@media (min-width: ${breakpoints[breakpoint]}px)`;
    }
  }
};

// Touch-friendly styles for mobile
export const touchStyles = {
  // Minimum touch target size (44px)
  touchTarget: {
    minHeight: 44,
    minWidth: 44,
    padding: 1
  },
  
  // Increased spacing for touch
  touchSpacing: {
    margin: 1,
    '& + &': {
      marginLeft: 2
    }
  },
  
  // Touch-friendly list items
  touchListItem: {
    minHeight: 48,
    padding: 2,
    '&:active': {
      backgroundColor: 'action.selected'
    }
  }
};

// Safe area utilities for mobile devices
export const safeAreaStyles = {
  // iOS safe area support
  paddingTop: 'env(safe-area-inset-top)',
  paddingBottom: 'env(safe-area-inset-bottom)',
  paddingLeft: 'env(safe-area-inset-left)',
  paddingRight: 'env(safe-area-inset-right)',
  
  // Combined safe area
  safeArea: {
    paddingTop: 'env(safe-area-inset-top)',
    paddingBottom: 'env(safe-area-inset-bottom)',
    paddingLeft: 'env(safe-area-inset-left)',
    paddingRight: 'env(safe-area-inset-right)'
  }
};

// Responsive hook utility
export const useResponsiveBreakpoint = () => {
  // This would be used with useMediaQuery hook in components
  return {
    isXs: '(max-width: 575px)',
    isSm: '(min-width: 576px) and (max-width: 767px)',
    isMd: '(min-width: 768px) and (max-width: 991px)',
    isLg: '(min-width: 992px) and (max-width: 1199px)',
    isXl: '(min-width: 1200px)',
    isMobile: '(max-width: 767px)',
    isTablet: '(min-width: 768px) and (max-width: 1199px)',
    isDesktop: '(min-width: 1200px)'
  };
};