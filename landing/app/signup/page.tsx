'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { Logo } from '../components/Logo';

// Plan details for display
const PLANS = [
  {
    tier: 'free',
    name: 'Free',
    price: '$0',
    period: 'forever',
    queries: '5 queries/month',
    features: ['5 queries per month', 'Access to all 77,274 games', 'Basic market insights'],
  },
  {
    tier: 'indie',
    name: 'Indie',
    price: '$29',
    period: '/month',
    queries: '150 queries/month',
    features: ['150 queries per month', 'Full market intelligence', 'Unlimited CSV exports', 'Chat history'],
    popular: true,
  },
  {
    tier: 'studio',
    name: 'Studio',
    price: '$69',
    period: '/user/month',
    queries: 'Unlimited',
    features: ['Unlimited queries', 'Everything in Indie', 'Team collaboration', 'API access (coming soon)'],
  },
];

// Loading component
function LoadingState() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <svg className="animate-spin w-8 h-8 text-teal-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="text-slate-500">Loading...</span>
      </div>
    </div>
  );
}

// Inner component that uses searchParams
function SignupForm() {
  const [selectedPlan, setSelectedPlan] = useState('indie');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPageLoading, setIsPageLoading] = useState(true);
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Check for plan parameter from pricing page
  useEffect(() => {
    const plan = searchParams.get('plan');
    if (plan && PLANS.some(p => p.tier === plan)) {
      setSelectedPlan(plan);
    }
  }, [searchParams]);

  // Handle auth loading and redirect
  useEffect(() => {
    if (!authLoading) {
      if (isAuthenticated) {
        router.push('/app');
      } else {
        setIsPageLoading(false);
      }
    }
  }, [authLoading, isAuthenticated, router]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    try {
      // Store signup data in Supabase
      const signupResponse = await fetch('/api/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: formData.name,
          email: formData.email,
          password: formData.password,
          plan: selectedPlan,
        }),
      });

      const signupData = await signupResponse.json();

      if (!signupResponse.ok) {
        throw new Error(signupData.error || 'Failed to create account');
      }

      // For paid plans, redirect to Stripe checkout
      if (selectedPlan !== 'free') {
        const checkoutResponse = await fetch('/api/stripe/checkout', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            planType: selectedPlan,
            userId: signupData.userId,
            userEmail: formData.email,
          }),
        });

        const checkoutData = await checkoutResponse.json();

        if (!checkoutResponse.ok) {
          throw new Error(checkoutData.error || 'Failed to create checkout session');
        }

        // Redirect to Stripe Checkout
        if (checkoutData.url) {
          window.location.href = checkoutData.url;
          return;
        } else {
          throw new Error('No checkout URL received');
        }
      }

      // For free plan, redirect to login with success message
      router.push('/login?signup=success&plan=' + selectedPlan);
    } catch (err) {
      console.error('Signup error:', err);
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
      setIsLoading(false);
    }
  };

  // Show loading state
  if (isPageLoading) {
    return <LoadingState />;
  }

  const selectedPlanDetails = PLANS.find(p => p.tier === selectedPlan);

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <a href="/" className="flex items-center">
              <Logo variant="full" size="sm" />
            </a>
            <a
              href="/login"
              className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
            >
              Already have an account? <span className="text-teal-600 font-medium">Sign in</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-12">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-slate-900">Create your account</h1>
          <p className="mt-2 text-slate-600">Start making data-driven decisions for your game</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Left Side - Plan Selection */}
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Choose your plan</h2>
            <div className="space-y-3">
              {PLANS.map((plan) => (
                <button
                  key={plan.tier}
                  type="button"
                  onClick={() => setSelectedPlan(plan.tier)}
                  className={`w-full p-4 rounded-xl border-2 transition-all duration-200 text-left relative ${
                    selectedPlan === plan.tier
                      ? plan.tier === 'indie'
                        ? 'border-teal-500 bg-teal-50'
                        : plan.tier === 'studio'
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-slate-400 bg-slate-50'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  {plan.popular && (
                    <span className="absolute -top-2.5 left-4 px-2 py-0.5 bg-teal-600 text-white text-xs font-medium rounded-full">
                      Most Popular
                    </span>
                  )}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        selectedPlan === plan.tier
                          ? plan.tier === 'indie'
                            ? 'border-teal-500 bg-teal-500'
                            : plan.tier === 'studio'
                            ? 'border-purple-500 bg-purple-500'
                            : 'border-slate-500 bg-slate-500'
                          : 'border-slate-300'
                      }`}>
                        {selectedPlan === plan.tier && (
                          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">{plan.name}</p>
                        <p className="text-sm text-slate-500">{plan.queries}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-bold text-slate-900">{plan.price}</span>
                      <span className="text-sm text-slate-500">{plan.period}</span>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t border-slate-100">
                    <ul className="space-y-1">
                      {plan.features.map((feature, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm text-slate-600">
                          <svg className={`w-4 h-4 flex-shrink-0 ${
                            plan.tier === 'indie' ? 'text-teal-500' :
                            plan.tier === 'studio' ? 'text-purple-500' : 'text-slate-400'
                          }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </div>
                </button>
              ))}
            </div>

            {/* Selected Plan Summary */}
            {selectedPlanDetails && selectedPlan !== 'free' && (
              <div className="mt-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Due today</span>
                  <span className="text-lg font-bold text-slate-900">
                    {selectedPlanDetails.price}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Cancel anytime. Billed monthly.
                </p>
              </div>
            )}
          </div>

          {/* Right Side - Signup Form */}
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Your details</h2>
            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700 text-sm flex items-center gap-2">
                  <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {error}
                </div>
              )}

              {/* Name Field */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1.5">
                  Full name
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  placeholder="John Doe"
                />
              </div>

              {/* Email Field */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">
                  Email address
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  placeholder="you@example.com"
                />
              </div>

              {/* Password Field */}
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1.5">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  placeholder="Create a password (min. 6 characters)"
                />
              </div>

              {/* Confirm Password Field */}
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700 mb-1.5">
                  Confirm password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  placeholder="Confirm your password"
                />
              </div>

              {/* Terms */}
              <p className="text-xs text-slate-500">
                By creating an account, you agree to our{' '}
                <a href="#" className="text-teal-600 hover:underline">Terms of Service</a>
                {' '}and{' '}
                <a href="#" className="text-teal-600 hover:underline">Privacy Policy</a>.
              </p>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    {selectedPlan !== 'free' ? 'Proceeding to checkout...' : 'Creating account...'}
                  </>
                ) : (
                  <>
                    {selectedPlan !== 'free'
                      ? `Continue to Payment — ${selectedPlanDetails?.price}${selectedPlanDetails?.period}`
                      : 'Create Free Account'
                    }
                  </>
                )}
              </button>
            </form>

            {/* Demo Notice */}
            <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex gap-3">
                <svg className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-amber-800">Demo Mode</p>
                  <p className="text-sm text-amber-700 mt-1">
                    This is a demo. For testing, use the{' '}
                    <a href="/login" className="underline font-medium">login page</a>
                    {' '}with pre-configured test accounts.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// Main export with Suspense boundary
export default function SignupPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <SignupForm />
    </Suspense>
  );
}
