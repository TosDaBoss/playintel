'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

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

function SuccessContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [countdown, setCountdown] = useState(5);
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    // Countdown timer
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          router.push('/app');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [router]);

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Success Icon */}
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <h1 className="text-3xl font-bold text-slate-900 mb-4">
          Payment Successful!
        </h1>

        <p className="text-slate-600 mb-8">
          Welcome to PlayIntel! Your subscription is now active.
          You can start using all the features of your plan immediately.
        </p>

        {/* Confirmation Box */}
        <div className="bg-slate-50 rounded-lg p-4 mb-8 border border-slate-200">
          <p className="text-sm text-slate-500 mb-1">Confirmation</p>
          <p className="text-sm font-mono text-slate-700 truncate">
            {sessionId ? `Session: ${sessionId.slice(0, 20)}...` : 'Processing...'}
          </p>
        </div>

        {/* Redirect Notice */}
        <p className="text-sm text-slate-500 mb-6">
          Redirecting to your dashboard in {countdown} seconds...
        </p>

        {/* Manual Navigation */}
        <div className="space-y-3">
          <a
            href="/app"
            className="block w-full py-3 px-4 bg-teal-600 text-white font-medium rounded-lg hover:bg-teal-700 transition-colors"
          >
            Go to Dashboard Now
          </a>
          <a
            href="/"
            className="block w-full py-3 px-4 bg-white text-slate-600 font-medium rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            Return to Homepage
          </a>
        </div>

        {/* Help Text */}
        <p className="mt-8 text-xs text-slate-400">
          A confirmation email has been sent to your inbox.
          <br />
          Questions? Contact support@playintel.io
        </p>
      </div>
    </div>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <SuccessContent />
    </Suspense>
  );
}
