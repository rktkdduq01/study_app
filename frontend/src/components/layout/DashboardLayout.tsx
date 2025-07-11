import React, { ReactNode } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  AlertTitle,
  Button,
  Skeleton,
} from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface DashboardSection {
  id: string;
  title?: string;
  component: ReactNode;
  gridProps?: {
    xs?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
}

interface DashboardLayoutProps {
  title: string;
  subtitle?: string;
  loading?: boolean;
  error?: Error | null;
  sections: DashboardSection[];
  onRefresh?: () => void;
  headerAction?: ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | false;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  title,
  subtitle,
  loading = false,
  error = null,
  sections,
  onRefresh,
  headerAction,
  maxWidth = 'lg',
}) => {
  if (loading) {
    return (
      <Container maxWidth={maxWidth} sx={{ py: 4 }}>
        <DashboardSkeleton title={title} sectionsCount={sections.length} />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth={maxWidth} sx={{ py: 4 }}>
        <Alert 
          severity="error" 
          action={
            onRefresh && (
              <Button 
                color="inherit" 
                size="small" 
                onClick={onRefresh}
                startIcon={<RefreshIcon />}
              >
                Retry
              </Button>
            )
          }
        >
          <AlertTitle>Error loading dashboard</AlertTitle>
          {error.message || 'An unexpected error occurred'}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth={maxWidth} sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="h4" component="h1">
            {title}
          </Typography>
          {headerAction}
        </Box>
        {subtitle && (
          <Typography variant="body1" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>

      {/* Sections */}
      <Grid container spacing={3}>
        {sections.map((section) => (
          <Grid 
            key={section.id}
            size={{
              xs: section.gridProps?.xs || 12,
              sm: section.gridProps?.sm,
              md: section.gridProps?.md,
              lg: section.gridProps?.lg,
              xl: section.gridProps?.xl,
            }}
          >
            {section.title ? (
              <Paper sx={{ p: 3, height: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  {section.title}
                </Typography>
                {section.component}
              </Paper>
            ) : (
              section.component
            )}
          </Grid>
        ))}
      </Grid>
    </Container>
  );
};

// Loading skeleton component
const DashboardSkeleton: React.FC<{ title: string; sectionsCount: number }> = ({ 
  title, 
  sectionsCount 
}) => (
  <>
    <Box sx={{ mb: 4 }}>
      <Typography variant="h4" component="h1">
        {title}
      </Typography>
      <Skeleton variant="text" width="60%" />
    </Box>
    <Grid container spacing={3}>
      {Array.from({ length: sectionsCount }).map((_, index) => (
        <Grid key={index} size={12}>
          <Paper sx={{ p: 3 }}>
            <Skeleton variant="text" width="30%" height={32} sx={{ mb: 2 }} />
            <Skeleton variant="rectangular" height={200} />
          </Paper>
        </Grid>
      ))}
    </Grid>
  </>
);

// Common dashboard stat card component
interface StatCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  trend?: {
    value: number;
    direction: 'up' | 'down';
  };
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  color = 'primary',
  trend,
}) => (
  <Paper sx={{ p: 3, height: '100%' }}>
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <Box>
        <Typography color="text.secondary" gutterBottom variant="body2">
          {title}
        </Typography>
        <Typography variant="h4" component="div" color={`${color}.main`}>
          {value}
        </Typography>
        {trend && (
          <Typography
            variant="body2"
            sx={{
              color: trend.direction === 'up' ? 'success.main' : 'error.main',
              mt: 1,
            }}
          >
            {trend.direction === 'up' ? '↑' : '↓'} {Math.abs(trend.value)}%
          </Typography>
        )}
      </Box>
      {icon && (
        <Box
          sx={{
            backgroundColor: `${color}.light`,
            borderRadius: '50%',
            p: 1.5,
            color: `${color}.main`,
          }}
        >
          {icon}
        </Box>
      )}
    </Box>
  </Paper>
);