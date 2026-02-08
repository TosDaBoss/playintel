'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { Logo } from '../components/Logo';

// Test accounts for quick access
const TEST_ACCOUNTS = [
  {
    tier: 'free',
    email: 'free@playintel.io',
    password: 'free123',
    label: 'Free',
    queries: '5 queries/month',
  },
  {
    tier: 'indie',
    email: 'indie@playintel.io',
    password: 'indie123',
    label: 'Indie',
    queries: '150 queries/month',
  },
  {
    tier: 'studio',
    email: 'studio@playintel.io',
    password: 'studio123',
    label: 'Studio',
    queries: 'Unlimited',
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
function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPageLoading, setIsPageLoading] = useState(true);
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // Check for plan parameter from pricing page
  useEffect(() => {
    const plan = searchParams.get('plan');
    if (plan) {
      const account = TEST_ACCOUNTS.find(a => a.tier === plan);
      if (account) {
        setEmail(account.email);
        setPassword(account.password);
      }
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    const result = await login(email, password);

    if (result.success) {
      router.push('/app');
    } else {
      setError(result.error || 'Login failed');
      setIsLoading(false);
    }
  };

  const fillCredentials = (account: typeof TEST_ACCOUNTS[0]) => {
    setEmail(account.email);
    setPassword(account.password);
    setError('');
  };

  // Show loading state
  if (isPageLoading) {
    return <LoadingState />;
  }

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
              href="/signup"
              className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
            >
              Don&apos;t have an account? <span className="text-teal-600 font-medium">Sign up</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-col lg:flex-row min-h-[calc(100vh-64px)]">
        {/* Left Side - Form */}
        <div className="flex-1 flex items-center justify-center px-4 py-12">
          <div className="w-full max-w-md">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-slate-900">Welcome back</h1>
              <p className="mt-2 text-slate-600">Sign in to access Steam market intelligence</p>
            </div>

            {/* Login Form */}
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

              {/* Email Field */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  placeholder="you@example.com"
                />
              </div>

              {/* Password Field */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                    Password
                  </label>
                  <a href="#" className="text-sm text-teal-600 hover:text-teal-700">
                    Forgot password?
                  </a>
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                  placeholder="Enter your password"
                />
              </div>

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
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-3 bg-white text-slate-500">Or try a demo account</span>
              </div>
            </div>

            {/* Test Accounts */}
            <div className="space-y-3">
              {TEST_ACCOUNTS.map((account) => (
                <button
                  key={account.tier}
                  type="button"
                  onClick={() => fillCredentials(account)}
                  className={`w-full p-4 rounded-lg border-2 transition-all duration-200 text-left flex items-center justify-between group ${
                    email === account.email
                      ? account.tier === 'indie'
                        ? 'border-teal-500 bg-teal-50'
                        : account.tier === 'studio'
                        ? 'border-purple-500 bg-purple-50'
                        : 'border-slate-400 bg-slate-50'
                      : 'border-slate-200 hover:border-slate-300 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      account.tier === 'indie'
                        ? 'bg-teal-100 text-teal-600'
                        : account.tier === 'studio'
                        ? 'bg-purple-100 text-purple-600'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {account.tier === 'free' && (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      )}
                      {account.tier === 'indie' && (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                      )}
                      {account.tier === 'studio' && (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{account.label} Plan</p>
                      <p className="text-sm text-slate-500">{account.queries}</p>
                    </div>
                  </div>
                  <div className={`text-sm font-medium ${
                    email === account.email ? 'text-teal-600' : 'text-slate-400 group-hover:text-slate-600'
                  }`}>
                    {email === account.email ? 'Selected' : 'Select'}
                  </div>
                </button>
              ))}
            </div>

            {/* Help Text */}
            <p className="mt-6 text-center text-sm text-slate-500">
              Click a plan above to auto-fill demo credentials, then sign in.
            </p>
          </div>
        </div>

        {/* Right Side - Feature Highlight */}
        <div className="hidden lg:flex flex-1 bg-slate-50 items-center justify-center p-12 border-l border-slate-200">
          <div className="max-w-md">
            <div className="w-16 h-16 bg-teal-100 rounded-2xl flex items-center justify-center mb-6">
              <svg className="w-8 h-8 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-4">
              Talk to Steam data like never before
            </h2>
            <p className="text-slate-600 mb-8 leading-relaxed">
              Ask questions in plain English and get data-driven insights from 77,274 games.
              Validate concepts, find pricing sweet spots, and discover market opportunities.
            </p>

            {/* Sample Questions */}
            <div className="space-y-3">
              <p className="text-sm font-medium text-slate-700">Try asking Alex:</p>
              {[
                "What should I price my roguelike at?",
                "How saturated is the horror genre?",
                "Show me successful games under $15"
              ].map((question, i) => (
                <div
                  key={i}
                  className="flex items-center gap-3 text-sm text-slate-600 bg-white rounded-lg p-3 border border-slate-200"
                >
                  <svg className="w-4 h-4 text-teal-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{question}</span>
                </div>
              ))}
            </div>

            {/* Stats */}
            <div className="mt-8 grid grid-cols-3 gap-4">
              {[
                { value: '77,274', label: 'Games' },
                { value: '440', label: 'Tags' },
                { value: '28', label: 'Genres' },
              ].map((stat) => (
                <div key={stat.label} className="text-center">
                  <p className="text-xl font-bold text-slate-900">{stat.value}</p>
                  <p className="text-xs text-slate-500">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// Main export with Suspense boundary
export default function LoginPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <LoginForm />
    </Suspense>
  );
}
