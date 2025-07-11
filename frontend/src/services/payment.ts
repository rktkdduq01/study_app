import { api } from './api';
import { loadStripe, Stripe, StripeElements } from '@stripe/stripe-js';

// Initialize Stripe
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY || '');

export type SubscriptionPlan = 'free' | 'basic' | 'premium' | 'family';

export interface PlanDetails {
  id: SubscriptionPlan;
  name: string;
  price: number;
  priceDisplay: string;
  features: {
    ai_requests_per_month: number;
    practice_questions_per_day: number;
    learning_paths: number;
    storage_gb: number;
    multiplayer: boolean;
    priority_support: boolean;
    advanced_analytics?: boolean;
    custom_content?: boolean;
    family_accounts?: number;
    parental_controls?: boolean;
  };
  recommended?: boolean;
}

export interface Subscription {
  plan: SubscriptionPlan;
  status: string;
  features: Record<string, any>;
  currentPeriodStart?: string;
  currentPeriodEnd?: string;
  cancelAtPeriodEnd: boolean;
  trialEnd?: string;
}

export interface PaymentMethod {
  id: string;
  brand: string;
  last4: string;
  expMonth: number;
  expYear: number;
  isDefault: boolean;
}

export interface Payment {
  id: number;
  amount: number;
  currency: string;
  description: string;
  status: string;
  createdAt: string;
  completedAt?: string;
}

export interface UsageData {
  periodStart: string;
  periodEnd: string;
  usage: Record<string, {
    used: number;
    limit: number | null;
    percentage: number;
  }>;
}

class PaymentService {
  async getStripe(): Promise<Stripe | null> {
    return stripePromise;
  }

  async getPlans(): Promise<PlanDetails[]> {
    const response = await api.get('/payments/plans');
    return response.data.plans;
  }

  async getCurrentSubscription(): Promise<Subscription> {
    const response = await api.get('/payments/subscription');
    return response.data;
  }

  async createSubscription(plan: SubscriptionPlan, paymentMethodId: string): Promise<{
    subscriptionId: string;
    status: string;
    clientSecret?: string;
  }> {
    const response = await api.post('/payments/subscription', {
      plan,
      payment_method_id: paymentMethodId
    });
    return response.data;
  }

  async updateSubscription(plan: SubscriptionPlan): Promise<{
    subscriptionId: string;
    plan: string;
    status: string;
  }> {
    const response = await api.put('/payments/subscription', { plan });
    return response.data;
  }

  async cancelSubscription(immediate: boolean = false): Promise<{
    status: string;
    cancelAt?: string;
  }> {
    const response = await api.delete('/payments/subscription', {
      params: { immediate }
    });
    return response.data;
  }

  async createPaymentIntent(amount: number, description?: string): Promise<{
    paymentIntentId: string;
    clientSecret: string;
    amount: number;
    currency: string;
  }> {
    const response = await api.post('/payments/payment-intent', {
      amount,
      currency: 'usd',
      description
    });
    return response.data;
  }

  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await api.get('/payments/payment-methods');
    return response.data.payment_methods;
  }

  async addPaymentMethod(paymentMethodId: string, setAsDefault: boolean = true): Promise<{
    paymentMethod: PaymentMethod;
  }> {
    const response = await api.post('/payments/payment-methods', {
      payment_method_id: paymentMethodId,
      set_as_default: setAsDefault
    });
    return response.data;
  }

  async removePaymentMethod(paymentMethodId: string): Promise<void> {
    await api.delete(`/payments/payment-methods/${paymentMethodId}`);
  }

  async getPaymentHistory(limit: number = 10, offset: number = 0): Promise<{
    payments: Payment[];
    total: number;
  }> {
    const response = await api.get('/payments/payment-history', {
      params: { limit, offset }
    });
    return response.data;
  }

  async getUsageSummary(): Promise<UsageData> {
    const response = await api.get('/payments/usage');
    return response.data;
  }

  async checkFeatureAccess(featureKey: string): Promise<{
    hasAccess: boolean;
    limit: number | null;
    isUnlimited: boolean;
  }> {
    const response = await api.get(`/payments/feature-access/${featureKey}`);
    return response.data;
  }

  async createCustomerPortalSession(): Promise<{ url: string }> {
    const response = await api.post('/payments/create-portal-session');
    return response.data;
  }

  // Helper method to confirm payment
  async confirmPayment(
    stripe: Stripe,
    clientSecret: string,
    paymentMethodId?: string
  ): Promise<any> {
    if (paymentMethodId) {
      return stripe.confirmCardPayment(clientSecret, {
        payment_method: paymentMethodId
      });
    } else {
      // Will use the default payment method
      return stripe.confirmCardPayment(clientSecret);
    }
  }

  // Helper method to create payment method
  async createPaymentMethod(
    stripe: Stripe,
    elements: StripeElements,
    billingDetails?: {
      name?: string;
      email?: string;
      phone?: string;
      address?: any;
    }
  ): Promise<any> {
    const cardElement = elements.getElement('card');
    if (!cardElement) {
      throw new Error('Card element not found');
    }

    return stripe.createPaymentMethod({
      type: 'card',
      card: cardElement,
      billing_details: billingDetails
    });
  }
}

export const paymentService = new PaymentService();