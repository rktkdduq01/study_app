import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ToggleButton,
  ToggleButtonGroup,
  Badge
} from '@mui/material';
import {
  Check as CheckIcon,
  Close as CloseIcon,
  Star as StarIcon,
  TrendingUp as TrendingIcon,
  School as SchoolIcon,
  Group as GroupIcon,
  Bolt as BoltIcon,
  Support as SupportIcon,
  Analytics as AnalyticsIcon,
  Storage as StorageIcon
} from '@mui/icons-material';
import { paymentService, PlanDetails, SubscriptionPlan } from '../../services/payment';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import PaymentForm from './PaymentForm';

export const SubscriptionPlans: React.FC = () => {
  const [plans, setPlans] = useState<PlanDetails[]>([]);
  const [currentPlan, setCurrentPlan] = useState<SubscriptionPlan>('free');
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [upgrading, setUpgrading] = useState(false);
  
  const user = useSelector((state: RootState) => state.auth.user);

  useEffect(() => {
    loadPlansAndSubscription();
  }, []);

  const loadPlansAndSubscription = async () => {
    try {
      setLoading(true);
      const [plansData, subscriptionData] = await Promise.all([
        paymentService.getPlans(),
        paymentService.getCurrentSubscription()
      ]);
      
      setPlans(plansData);
      setCurrentPlan(subscriptionData.plan);
    } catch (err) {
      setError('Failed to load subscription plans');
      console.error('Error loading plans:', err);
    } finally {
      setLoading(false);
    }
  };

  const getFeatureIcon = (feature: string) => {
    switch (feature) {
      case 'ai_requests': return <BoltIcon />;
      case 'practice_questions': return <SchoolIcon />;
      case 'learning_paths': return <TrendingIcon />;
      case 'storage': return <StorageIcon />;
      case 'multiplayer': return <GroupIcon />;
      case 'priority_support': return <SupportIcon />;
      case 'advanced_analytics': return <AnalyticsIcon />;
      default: return <CheckIcon />;
    }
  };

  const formatFeatureValue = (value: number | boolean, featureName: string) => {
    if (typeof value === 'boolean') {
      return value ? <CheckIcon color="success" /> : <CloseIcon color="disabled" />;
    }
    if (value === -1) {
      return 'Unlimited';
    }
    if (featureName.includes('gb')) {
      return `${value} GB`;
    }
    if (featureName.includes('per_month')) {
      return `${value}/month`;
    }
    if (featureName.includes('per_day')) {
      return `${value}/day`;
    }
    return value;
  };

  const getYearlyPrice = (monthlyPrice: number) => {
    // 20% discount for yearly billing
    return Math.floor(monthlyPrice * 12 * 0.8);
  };

  const handleSelectPlan = (plan: SubscriptionPlan) => {
    if (plan === currentPlan) return;
    
    setSelectedPlan(plan);
    if (plan === 'free') {
      // Downgrading to free
      handleDowngrade();
    } else {
      setShowPaymentDialog(true);
    }
  };

  const handleDowngrade = async () => {
    if (!window.confirm('Are you sure you want to downgrade to the free plan? You will lose access to premium features.')) {
      return;
    }

    try {
      setUpgrading(true);
      await paymentService.cancelSubscription(false);
      await loadPlansAndSubscription();
      setError(null);
    } catch (err) {
      setError('Failed to downgrade subscription');
    } finally {
      setUpgrading(false);
    }
  };

  const handlePaymentSuccess = async () => {
    setShowPaymentDialog(false);
    await loadPlansAndSubscription();
    setSelectedPlan(null);
  };

  const getPlanColor = (plan: SubscriptionPlan) => {
    switch (plan) {
      case 'basic': return 'primary';
      case 'premium': return 'secondary';
      case 'family': return 'success';
      default: return 'inherit';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom align="center">
        Choose Your Plan
      </Typography>
      
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
        <ToggleButtonGroup
          value={billingCycle}
          exclusive
          onChange={(_, value) => value && setBillingCycle(value)}
          aria-label="billing cycle"
        >
          <ToggleButton value="monthly">Monthly</ToggleButton>
          <ToggleButton value="yearly">
            Yearly
            <Chip label="Save 20%" size="small" color="success" sx={{ ml: 1 }} />
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {plans.map((plan) => {
          const isCurrentPlan = plan.id === currentPlan;
          const displayPrice = billingCycle === 'yearly' 
            ? getYearlyPrice(plan.price) 
            : plan.price;
          const priceText = plan.price === 0 
            ? 'Free' 
            : billingCycle === 'yearly'
            ? `$${(displayPrice / 100 / 12).toFixed(2)}/mo`
            : `$${(displayPrice / 100).toFixed(2)}/mo`;

          return (
            <Grid size={{ xs: 12, md: 6, lg: 3 }} key={plan.id}>
              <Card 
                elevation={plan.recommended ? 8 : 2}
                sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column',
                  position: 'relative',
                  border: isCurrentPlan ? 2 : 0,
                  borderColor: 'primary.main'
                }}
              >
                {plan.recommended && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: -12,
                      right: 20,
                      bgcolor: 'secondary.main',
                      color: 'white',
                      px: 2,
                      py: 0.5,
                      borderRadius: 1,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5
                    }}
                  >
                    <StarIcon fontSize="small" />
                    <Typography variant="caption" fontWeight="bold">
                      RECOMMENDED
                    </Typography>
                  </Box>
                )}

                {isCurrentPlan && (
                  <Chip
                    label="Current Plan"
                    color="primary"
                    size="small"
                    sx={{ position: 'absolute', top: 10, left: 10 }}
                  />
                )}

                <CardContent sx={{ flexGrow: 1, pt: isCurrentPlan ? 5 : 3 }}>
                  <Typography variant="h5" gutterBottom align="center">
                    {plan.name}
                  </Typography>
                  
                  <Box sx={{ textAlign: 'center', mb: 3 }}>
                    <Typography variant="h3" component="span">
                      {priceText.split('/')[0]}
                    </Typography>
                    {plan.price > 0 && (
                      <Typography variant="body1" component="span" color="text.secondary">
                        /{priceText.split('/')[1]}
                      </Typography>
                    )}
                    {billingCycle === 'yearly' && plan.price > 0 && (
                      <Typography variant="body2" color="text.secondary">
                        Billed ${(displayPrice / 100).toFixed(2)} yearly
                      </Typography>
                    )}
                  </Box>

                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        {getFeatureIcon('ai_requests')}
                      </ListItemIcon>
                      <ListItemText 
                        primary={`AI Tutor Requests`}
                        secondary={formatFeatureValue(plan.features.ai_requests_per_month, 'per_month')}
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        {getFeatureIcon('practice_questions')}
                      </ListItemIcon>
                      <ListItemText 
                        primary={`Practice Questions`}
                        secondary={formatFeatureValue(plan.features.practice_questions_per_day, 'per_day')}
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        {getFeatureIcon('learning_paths')}
                      </ListItemIcon>
                      <ListItemText 
                        primary={`Learning Paths`}
                        secondary={formatFeatureValue(plan.features.learning_paths, '')}
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        {getFeatureIcon('storage')}
                      </ListItemIcon>
                      <ListItemText 
                        primary={`Storage`}
                        secondary={formatFeatureValue(plan.features.storage_gb, 'gb')}
                      />
                    </ListItem>
                    
                    <ListItem>
                      <ListItemIcon>
                        {getFeatureIcon('multiplayer')}
                      </ListItemIcon>
                      <ListItemText 
                        primary={`Multiplayer`}
                        secondary={formatFeatureValue(plan.features.multiplayer, '')}
                      />
                    </ListItem>
                    
                    {plan.features.priority_support && (
                      <ListItem>
                        <ListItemIcon>
                          {getFeatureIcon('priority_support')}
                        </ListItemIcon>
                        <ListItemText primary={`Priority Support`} />
                      </ListItem>
                    )}
                    
                    {plan.features.advanced_analytics && (
                      <ListItem>
                        <ListItemIcon>
                          {getFeatureIcon('advanced_analytics')}
                        </ListItemIcon>
                        <ListItemText primary={`Advanced Analytics`} />
                      </ListItem>
                    )}
                    
                    {plan.features.family_accounts && (
                      <ListItem>
                        <ListItemIcon>
                          <Badge badgeContent={plan.features.family_accounts} color="primary">
                            <GroupIcon />
                          </Badge>
                        </ListItemIcon>
                        <ListItemText primary={`Family Accounts`} />
                      </ListItem>
                    )}
                  </List>
                </CardContent>

                <CardActions sx={{ p: 2 }}>
                  <Button
                    fullWidth
                    variant={isCurrentPlan ? "outlined" : "contained"}
                    color={getPlanColor(plan.id)}
                    disabled={isCurrentPlan || upgrading}
                    onClick={() => handleSelectPlan(plan.id)}
                  >
                    {isCurrentPlan ? 'Current Plan' : plan.id === 'free' ? 'Downgrade' : 'Upgrade'}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Payment Dialog */}
      <Dialog 
        open={showPaymentDialog} 
        onClose={() => setShowPaymentDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Upgrade to {selectedPlan && plans.find(p => p.id === selectedPlan)?.name}
        </DialogTitle>
        <DialogContent>
          {selectedPlan && (
            <PaymentForm
              plan={selectedPlan}
              amount={billingCycle === 'yearly' 
                ? getYearlyPrice(plans.find(p => p.id === selectedPlan)?.price || 0)
                : plans.find(p => p.id === selectedPlan)?.price || 0
              }
              onSuccess={handlePaymentSuccess}
              onCancel={() => setShowPaymentDialog(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};