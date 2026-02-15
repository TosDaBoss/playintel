'use client';

import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Logo } from '../components/Logo';

const Icons = {
  Check: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
};

const PLANS = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Get started with PlayIntel - no credit card required',
    queries: '30 queries/month',
    features: [
      '30 queries per month',
      'Access to all 77,274 games',
      'Full market insights',
      'CSV export',
    ],
    cta: 'Create Free Account',
    highlighted: true,
    stripePlan: false,
  },
];

export default function PricingPage() {
  const { user, isAuthenticated } = useAuth();
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async (planId: string) => {
    if (!isAuthenticated) {
      // Redirect to signup with plan
      window.location.href = `/signup?plan=${planId}`;
      return;
    }

    const plan = PLANS.find(p => p.id === planId);
    if (!plan?.stripePlan) {
      // Free plan - just redirect to app
      window.location.href = '/app';
      return;
    }

    setLoadingPlan(planId);
    setError(null);

    try {
      const response = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          planType: planId,
          userId: user?.id,
          userEmail: user?.email,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to create checkout session');
      }

      // Redirect to Stripe Checkout using the URL from the session
      if (data.url) {
        window.location.href = data.url;
      } else {
        throw new Error('No checkout URL received');
      }
    } catch (err) {
      console.error('Checkout error:', err);
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoadingPlan(null);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <a href="/" className="flex items-center">
              <Logo variant="full" size="sm" />
            </a>
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-slate-600">
                    {user?.name}
                  </span>
                  <a
                    href="/app"
                    className="text-sm text-teal-600 font-medium hover:text-teal-700"
                  >
                    Go to App
                  </a>
                </>
              ) : (
                <>
                  <a
                    href="/login"
                    className="text-sm text-slate-600 hover:text-slate-900"
                  >
                    Sign in
                  </a>
                  <a
                    href="/signup"
                    className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700"
                  >
                    Get Started
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="py-16 lg:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-slate-900">
              Get Started
            </h1>
            <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
              Create your free account and start exploring game market data. No credit card required.
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="max-w-md mx-auto mb-8 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-center">
              {error}
            </div>
          )}

          {/* Pricing Cards */}
          <div className="flex justify-center max-w-md mx-auto">
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                className={`relative rounded-2xl p-8 ${
                  plan.highlighted
                    ? 'bg-teal-600 text-white shadow-xl scale-105'
                    : 'bg-white text-slate-900 border border-slate-200 shadow-sm'
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-teal-500 text-white text-xs font-semibold rounded-full">
                    Most Popular
                  </div>
                )}

                <div className="text-center mb-6">
                  <h3 className={`text-xl font-bold ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>
                    {plan.name}
                  </h3>
                  <div className="mt-4 flex items-baseline justify-center gap-1">
                    <span className={`text-4xl font-bold ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>
                      {plan.price}
                    </span>
                    <span className={`text-sm ${plan.highlighted ? 'text-teal-100' : 'text-slate-500'}`}>
                      {plan.period}
                    </span>
                  </div>
                  <p className={`mt-2 text-sm ${plan.highlighted ? 'text-teal-100' : 'text-slate-500'}`}>
                    {plan.description}
                  </p>
                </div>

                <div className={`mb-6 py-3 px-4 rounded-lg text-center ${
                  plan.highlighted ? 'bg-teal-500' : 'bg-slate-50'
                }`}>
                  <span className={`font-semibold ${plan.highlighted ? 'text-white' : 'text-teal-600'}`}>
                    {plan.queries}
                  </span>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className={plan.highlighted ? 'text-teal-200' : 'text-teal-600'}>
                        <Icons.Check />
                      </span>
                      <span className={`text-sm ${plan.highlighted ? 'text-teal-50' : 'text-slate-600'}`}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={loadingPlan === plan.id}
                  className={`block w-full py-3 px-4 rounded-lg font-medium text-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                    plan.highlighted
                      ? 'bg-white text-teal-600 hover:bg-teal-50'
                      : 'bg-teal-600 text-white hover:bg-teal-700'
                  }`}
                >
                  {loadingPlan === plan.id ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Processing...
                    </span>
                  ) : (
                    plan.cta
                  )}
                </button>

                {/* Current Plan Indicator */}
                {isAuthenticated && user?.plan === plan.id && (
                  <p className={`mt-3 text-center text-sm ${plan.highlighted ? 'text-teal-100' : 'text-slate-500'}`}>
                    Your current plan
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* Additional Info */}
          <div className="mt-16 max-w-3xl mx-auto">
            <div className="bg-slate-50 rounded-xl p-8 border border-slate-200">
              <h3 className="text-lg font-semibold text-slate-900 mb-4 text-center">
                Frequently Asked Questions
              </h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-slate-900">Can I cancel anytime?</h4>
                  <p className="text-sm text-slate-600 mt-1">
                    Yes! You can cancel your subscription at any time. You'll keep access until the end of your billing period.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-slate-900">What happens when I run out of queries?</h4>
                  <p className="text-sm text-slate-600 mt-1">
                    Queries reset on the 1st of each month. If you need more, you can upgrade your plan at any time.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium text-slate-900">Do you offer refunds?</h4>
                  <p className="text-sm text-slate-600 mt-1">
                    We offer a 14-day money-back guarantee. If you're not satisfied, contact us for a full refund.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <p className="mt-12 text-center text-sm text-slate-500">
            All plans include access to our full database of 77,274 games.
            <br />
            Questions? Contact us at support@playintel.io
          </p>
        </div>
      </main>
    </div>
  );
}
