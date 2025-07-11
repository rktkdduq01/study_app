import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  CircularProgress,
  Alert,
  TextField,
  FormControlLabel,
  Checkbox,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Radio,
  RadioGroup,
  Divider
} from '@mui/material';
import {
  CreditCard as CardIcon,
  Delete as DeleteIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { 
  CardElement,
  Elements,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';
import { paymentService, SubscriptionPlan, PaymentMethod } from '../../services/payment';

interface PaymentFormProps {
  plan: SubscriptionPlan;
  amount: number;
  onSuccess: () => void;
  onCancel: () => void;
}

const PaymentFormContent: React.FC<PaymentFormProps> = ({
  plan,
  amount,
  onSuccess,
  onCancel
}) => {
  const stripe = useStripe();
  const elements = useElements();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMethods, setSavedMethods] = useState<PaymentMethod[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<string>('new');
  const [saveCard, setSaveCard] = useState(true);
  const [billingDetails, setBillingDetails] = useState({
    name: '',
    email: ''
  });

  useEffect(() => {
    loadPaymentMethods();
  }, []);

  const loadPaymentMethods = async () => {
    try {
      const methods = await paymentService.getPaymentMethods();
      setSavedMethods(methods);
      if (methods.length > 0) {
        setSelectedMethod(methods[0].id);
      }
    } catch (err) {
      console.error('Error loading payment methods:', err);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!stripe) return;

    setLoading(true);
    setError(null);

    try {
      let paymentMethodId: string;

      if (selectedMethod === 'new') {
        // Create new payment method
        if (!elements) return;
        
        const cardElement = elements.getElement(CardElement);
        if (!cardElement) return;

        const { error: methodError, paymentMethod } = await stripe.createPaymentMethod({
          type: 'card',
          card: cardElement,
          billing_details: billingDetails
        });

        if (methodError) {
          throw new Error(methodError.message);
        }

        paymentMethodId = paymentMethod!.id;

        // Save card if requested
        if (saveCard) {
          await paymentService.addPaymentMethod(paymentMethodId, true);
        }
      } else {
        // Use existing payment method
        paymentMethodId = selectedMethod;
      }

      // Create subscription
      const result = await paymentService.createSubscription(plan, paymentMethodId);

      // Confirm payment if needed
      if (result.clientSecret) {
        const { error: confirmError } = await stripe.confirmCardPayment(result.clientSecret);
        
        if (confirmError) {
          throw new Error(confirmError.message);
        }
      }

      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Payment failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePaymentMethod = async (methodId: string) => {
    if (!window.confirm('Are you sure you want to remove this payment method?')) {
      return;
    }

    try {
      await paymentService.removePaymentMethod(methodId);
      await loadPaymentMethods();
      if (selectedMethod === methodId) {
        setSelectedMethod('new');
      }
    } catch (err) {
      setError('Failed to remove payment method');
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#424770',
        '::placeholder': {
          color: '#aab7c4',
        },
        fontFamily: '"Roboto", sans-serif',
      },
      invalid: {
        color: '#9e2146',
      },
    },
  };

  return (
    <form onSubmit={handleSubmit}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Order Summary
        </Typography>
        <Card variant="outlined">
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography>Plan</Typography>
              <Typography fontWeight="bold">{plan.charAt(0).toUpperCase() + plan.slice(1)}</Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography>Amount</Typography>
              <Typography fontWeight="bold">${(amount / 100).toFixed(2)}</Typography>
            </Box>
          </CardContent>
        </Card>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Typography variant="h6" gutterBottom>
        Payment Method
      </Typography>

      {savedMethods.length > 0 && (
        <RadioGroup
          value={selectedMethod}
          onChange={(e) => setSelectedMethod(e.target.value)}
          sx={{ mb: 2 }}
        >
          {savedMethods.map((method) => (
            <Card key={method.id} variant="outlined" sx={{ mb: 1 }}>
              <ListItem>
                <Radio value={method.id} />
                <CardIcon sx={{ mx: 2 }} />
                <ListItemText
                  primary={`${method.brand.toUpperCase()} •••• ${method.last4}`}
                  secondary={`Expires ${method.expMonth}/${method.expYear}`}
                />
                <ListItemSecondaryAction>
                  <IconButton
                    edge="end"
                    aria-label="delete"
                    onClick={() => handleDeletePaymentMethod(method.id)}
                    disabled={loading}
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            </Card>
          ))}
          
          <Card variant="outlined">
            <ListItem>
              <Radio value="new" />
              <AddIcon sx={{ mx: 2 }} />
              <ListItemText primary="Add new card" />
            </ListItem>
          </Card>
        </RadioGroup>
      )}

      {selectedMethod === 'new' && (
        <Box>
          <TextField
            fullWidth
            label="Cardholder Name"
            value={billingDetails.name}
            onChange={(e) => setBillingDetails({ ...billingDetails, name: e.target.value })}
            sx={{ mb: 2 }}
            required
          />
          
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={billingDetails.email}
            onChange={(e) => setBillingDetails({ ...billingDetails, email: e.target.value })}
            sx={{ mb: 2 }}
            required
          />

          <Box sx={{ p: 2, border: 1, borderColor: 'divider', borderRadius: 1, mb: 2 }}>
            <CardElement options={cardElementOptions} />
          </Box>

          <FormControlLabel
            control={
              <Checkbox
                checked={saveCard}
                onChange={(e) => setSaveCard(e.target.checked)}
              />
            }
            label="Save card for future payments"
            sx={{ mb: 2 }}
          />
        </Box>
      )}

      <Box sx={{ display: 'flex', gap: 2, mt: 3 }}>
        <Button
          variant="outlined"
          onClick={onCancel}
          disabled={loading}
          fullWidth
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="contained"
          disabled={!stripe || loading}
          fullWidth
        >
          {loading ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            `Subscribe - $${(amount / 100).toFixed(2)}`
          )}
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
        Your subscription will renew automatically. You can cancel anytime.
      </Typography>
    </form>
  );
};

const PaymentForm: React.FC<PaymentFormProps> = (props) => {
  const [stripe, setStripe] = useState<any>(null);

  useEffect(() => {
    const loadStripe = async () => {
      const stripeInstance = await paymentService.getStripe();
      setStripe(stripeInstance);
    };
    loadStripe();
  }, []);

  if (!stripe) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Elements stripe={stripe}>
      <PaymentFormContent {...props} />
    </Elements>
  );
};

export default PaymentForm;