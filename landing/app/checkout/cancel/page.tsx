'use client';

export default function CheckoutCancelPage() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        {/* Cancel Icon */}
        <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <svg className="w-10 h-10 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <h1 className="text-3xl font-bold text-slate-900 mb-4">
          Checkout Cancelled
        </h1>

        <p className="text-slate-600 mb-8">
          No worries! Your payment was not processed.
          If you have any questions about our plans, feel free to reach out.
        </p>

        {/* Reassurance Box */}
        <div className="bg-slate-50 rounded-lg p-4 mb-8 border border-slate-200">
          <div className="flex items-center justify-center gap-2 text-sm text-slate-600">
            <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <span>No charges were made to your account</span>
          </div>
        </div>

        {/* Navigation Options */}
        <div className="space-y-3">
          <a
            href="/#plans"
            className="block w-full py-3 px-4 bg-teal-600 text-white font-medium rounded-lg hover:bg-teal-700 transition-colors"
          >
            View Plans Again
          </a>
          <a
            href="/login"
            className="block w-full py-3 px-4 bg-white text-slate-600 font-medium rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors"
          >
            Sign In with Free Account
          </a>
          <a
            href="/"
            className="block w-full py-3 px-4 text-slate-500 font-medium hover:text-slate-700 transition-colors"
          >
            Return to Homepage
          </a>
        </div>

        {/* Help Text */}
        <p className="mt-8 text-xs text-slate-400">
          Have questions? Contact us at support@playintel.io
        </p>
      </div>
    </div>
  );
}
