import Stripe from 'stripe';

// Lazy-loaded Stripe instance to avoid build-time errors
let stripeInstance: Stripe | null = null;

export function getStripeServer(): Stripe {
  if (!stripeInstance) {
    if (!process.env.STRIPE_SECRET_KEY) {
      throw new Error('STRIPE_SECRET_KEY is not set');
    }
    stripeInstance = new Stripe(process.env.STRIPE_SECRET_KEY, {
      apiVersion: '2026-01-28.clover',
    });
  }
  return stripeInstance;
}

// For backwards compatibility - throws if called during build
export const stripe = {
  get checkout() { return getStripeServer().checkout; },
  get customers() { return getStripeServer().customers; },
  get subscriptions() { return getStripeServer().subscriptions; },
  get billingPortal() { return getStripeServer().billingPortal; },
  get webhooks() { return getStripeServer().webhooks; },
};

// Price IDs for each plan - you'll get these from Stripe Dashboard
// For now, these are placeholders that you'll replace with real IDs
export const STRIPE_PLANS = {
  indie: {
    priceId: process.env.STRIPE_INDIE_PRICE_ID || 'price_indie_placeholder',
    name: 'Indie',
    price: 25,
    queries: 150,
  },
  studio: {
    priceId: process.env.STRIPE_STUDIO_PRICE_ID || 'price_studio_placeholder',
    name: 'Studio',
    price: 59,
    queries: -1, // unlimited
  },
} as const;

export type PlanType = keyof typeof STRIPE_PLANS;
