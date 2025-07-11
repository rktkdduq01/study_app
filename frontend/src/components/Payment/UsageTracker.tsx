import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Button,
  Tooltip,
  Alert,
  Skeleton,
  IconButton,
  Collapse
} from '@mui/material';
import {
  TrendingUp as TrendingIcon,
  School as SchoolIcon,
  Bolt as BoltIcon,
  Storage as StorageIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon
} from '@mui/icons-material';
import { paymentService, UsageData, Subscription } from '../../services/payment';
import { useNavigate } from 'react-router-dom';

export const UsageTracker: React.FC = () => {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedMetrics, setExpandedMetrics] = useState<Set<string>>(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    loadUsageData();
  }, []);

  const loadUsageData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [usageData, subscriptionData] = await Promise.all([
        paymentService.getUsageSummary(),
        paymentService.getCurrentSubscription()
      ]);
      
      setUsage(usageData);
      setSubscription(subscriptionData);
    } catch (err) {
      setError('Failed to load usage data');
      console.error('Error loading usage:', err);
    } finally {
      setLoading(false);
    }
  };

  const getMetricIcon = (metric: string) => {
    if (metric.includes('ai_requests')) return <BoltIcon />;
    if (metric.includes('practice_questions')) return <SchoolIcon />;
    if (metric.includes('learning_paths')) return <TrendingIcon />;
    if (metric.includes('storage')) return <StorageIcon />;
    return <InfoIcon />;
  };

  const formatMetricName = (metric: string) => {
    return metric
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
      .replace('Ai ', 'AI ')
      .replace('Gb', 'GB');
  };

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'error';
    if (percentage >= 75) return 'warning';
    return 'primary';
  };

  const toggleMetricExpand = (metric: string) => {
    setExpandedMetrics(prev => {
      const newSet = new Set(prev);
      if (newSet.has(metric)) {
        newSet.delete(metric);
      } else {
        newSet.add(metric);
      }
      return newSet;
    });
  };

  const getUsageRecommendation = (metric: string, percentage: number) => {
    if (percentage >= 90) {
      return {
        severity: 'error' as const,
        message: 'You\'re approaching your limit. Consider upgrading your plan.',
        action: 'Upgrade Now'
      };
    }
    if (percentage >= 75) {
      return {
        severity: 'warning' as const,
        message: 'You\'ve used most of your allowance for this period.',
        action: 'View Plans'
      };
    }
    return null;
  };

  if (loading) {
    return (
      <Box>
        {[1, 2, 3].map((i) => (
          <Card key={i} sx={{ mb: 2 }}>
            <CardContent>
              <Skeleton variant="text" width="40%" height={32} />
              <Skeleton variant="rectangular" height={20} sx={{ mt: 2 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                <Skeleton variant="text" width="20%" />
                <Skeleton variant="text" width="20%" />
              </Box>
            </CardContent>
          </Card>
        ))}
      </Box>
    );
  }

  if (error || !usage || !subscription) {
    return (
      <Alert 
        severity="error" 
        action={
          <Button color="inherit" size="small" onClick={loadUsageData}>
            Retry
          </Button>
        }
      >
        {error || 'Unable to load usage data'}
      </Alert>
    );
  }

  const periodStart = new Date(usage.periodStart);
  const periodEnd = new Date(usage.periodEnd);
  const daysRemaining = Math.ceil((periodEnd.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24));

  return (
    <Box>
      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h5">Usage Summary</Typography>
              <Typography variant="body2" color="text.secondary">
                Current Period: {periodStart.toLocaleDateString()} - {periodEnd.toLocaleDateString()}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Chip 
                label={`${subscription.plan.toUpperCase()} Plan`} 
                color="primary" 
                variant="outlined"
              />
              <Tooltip title="Refresh usage data">
                <IconButton onClick={loadUsageData} size="small">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
          
          <Alert severity="info" variant="outlined" icon={<InfoIcon />}>
            <Typography variant="body2">
              {daysRemaining} days remaining in current billing period
            </Typography>
          </Alert>
        </CardContent>
      </Card>

      {/* Usage Metrics */}
      <Grid container spacing={2}>
        {Object.entries(usage.usage).map(([metric, data]) => {
          const recommendation = getUsageRecommendation(metric, data.percentage);
          const isExpanded = expandedMetrics.has(metric);
          
          return (
            <Grid size={12} key={metric}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getMetricIcon(metric)}
                      <Typography variant="h6">
                        {formatMetricName(metric)}
                      </Typography>
                    </Box>
                    <IconButton 
                      size="small" 
                      onClick={() => toggleMetricExpand(metric)}
                    >
                      {isExpanded ? <CollapseIcon /> : <ExpandIcon />}
                    </IconButton>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        {data.used} / {data.limit === null ? 'Unlimited' : data.limit} used
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {data.limit === null ? '∞' : `${Math.round(data.percentage)}%`}
                      </Typography>
                    </Box>
                    
                    {data.limit !== null && (
                      <LinearProgress 
                        variant="determinate" 
                        value={Math.min(data.percentage, 100)}
                        color={getProgressColor(data.percentage)}
                        sx={{ height: 8, borderRadius: 1 }}
                      />
                    )}
                  </Box>

                  {recommendation && (
                    <Alert 
                      severity={recommendation.severity} 
                      action={
                        <Button 
                          color="inherit" 
                          size="small"
                          onClick={() => navigate('/subscription')}
                        >
                          {recommendation.action}
                        </Button>
                      }
                      sx={{ mb: 2 }}
                    >
                      {recommendation.message}
                    </Alert>
                  )}

                  <Collapse in={isExpanded}>
                    <List dense>
                      <ListItem>
                        <ListItemText 
                          primary="Daily Average"
                          secondary={`${Math.round(data.used / Math.max(1, 30 - daysRemaining))} per day`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText 
                          primary="Projected Usage"
                          secondary={
                            data.limit === null 
                              ? 'Unlimited' 
                              : `${Math.round((data.used / Math.max(1, 30 - daysRemaining)) * 30)} by period end`
                          }
                        />
                      </ListItem>
                      {data.limit !== null && (
                        <ListItem>
                          <ListItemText 
                            primary="Remaining"
                            secondary={`${Math.max(0, data.limit - data.used)} ${metric.includes('storage') ? 'GB' : 'units'}`}
                          />
                        </ListItem>
                      )}
                    </List>
                  </Collapse>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Upgrade Prompt */}
      {subscription.plan === 'free' && (
        <Card sx={{ mt: 3, bgcolor: 'primary.main', color: 'white' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Unlock More with Premium
            </Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              Get unlimited AI requests, advanced analytics, and priority support.
            </Typography>
            <Button 
              variant="contained" 
              color="secondary"
              onClick={() => navigate('/subscription')}
            >
              View Plans
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};