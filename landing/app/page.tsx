'use client';

import { useState } from 'react';
import { useAuth } from './context/AuthContext';
import { Logo, LogoIcon } from './components/Logo';

// ============================================================================
// PLAYINTEL LANDING PAGE
// A conversion-focused landing page for indie game developers
// ============================================================================

// --- Icon Components (Simple SVGs) ---
const Icons = {
  Chat: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  ),
  PriceTag: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
    </svg>
  ),
  Grid: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  Target: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  ),
  Users: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  ),
  TrendingUp: () => (
    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  ),
  Check: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  ArrowRight: () => (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  ),
  Database: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
    </svg>
  ),
  Zap: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  Eye: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ),
  Compass: () => (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
    </svg>
  ),
};

// --- Navigation ---
function Navigation() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  const navLinks = [
    { href: '#features', label: 'Features' },
    { href: '#plans', label: 'Pricing' },
    { href: '#why', label: 'Why PlayIntel' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <a href="#" className="flex items-center">
            <Logo variant="full" size="sm" />
          </a>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
              >
                {link.label}
              </a>
            ))}
            {!isLoading && isAuthenticated && (
              <a
                href="/app"
                className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
              >
                Dashboard
              </a>
            )}
          </div>

          {/* CTA / Auth */}
          <div className="hidden md:flex items-center gap-4">
            {isLoading ? (
              // Show placeholder while checking auth to prevent hydration mismatch
              <div className="h-9 w-32 bg-slate-100 rounded-lg animate-pulse" />
            ) : isAuthenticated ? (
              <>
                <span className="text-sm text-slate-600">
                  Hi, {user?.name.split(' ')[0]}
                </span>
                <a
                  href="/app"
                  className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 transition-colors"
                >
                  Open App
                </a>
                <button
                  onClick={logout}
                  className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <a
                  href="/login"
                  className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
                >
                  Sign in
                </a>
                <a
                  href="#access"
                  className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
                >
                  Request early access
                </a>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 text-slate-600"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-slate-200">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="block py-2 text-slate-600 hover:text-slate-900"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </a>
            ))}
            {!isLoading && isAuthenticated ? (
              <>
                <a
                  href="/app"
                  className="block py-2 text-slate-600 hover:text-slate-900"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Dashboard
                </a>
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="block py-2 text-slate-500 hover:text-slate-700"
                >
                  Sign out
                </button>
              </>
            ) : !isLoading ? (
              <>
                <a
                  href="/login"
                  className="block py-2 text-slate-600 hover:text-slate-900"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Sign in
                </a>
                <a
                  href="#access"
                  className="mt-4 block w-full text-center px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Request early access
                </a>
              </>
            ) : null}
          </div>
        )}
      </div>
    </nav>
  );
}

// --- Hero Section ---
function Hero() {
  const sampleQuestions = [
    "What should I price my roguelike at?",
    "How saturated is the horror genre?",
    "Compare indie vs AAA success rates",
    "Show me top-rated games under $15",
    "What tags have the highest success rate?",
    "Find developers similar to my profile",
  ];

  const [activeQuestion, setActiveQuestion] = useState(sampleQuestions[0]);

  return (
    <section className="pt-24 pb-16 lg:pt-32 lg:pb-24 bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Left: Copy */}
          <div>
            <h1 className="text-4xl sm:text-5xl lg:text-5xl font-bold text-slate-900 leading-tight">
              Imagine if you could talk to Steam data and get data-driven insights.{' '}
              <span className="text-teal-600">Now you can.</span>
            </h1>
            <p className="mt-6 text-lg text-slate-600 leading-relaxed">
              PlayIntel helps indie developers validate game concepts, set competitive prices, and find underserved niches — all through natural conversation with 77,000+ games of market data.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-4">
              <a
                href="#access"
                className="inline-flex items-center justify-center px-6 py-3 bg-teal-600 text-white font-medium rounded-lg hover:bg-teal-700 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
              >
                Request early access
              </a>
              <a
                href="#features"
                className="inline-flex items-center justify-center px-6 py-3 bg-white text-slate-700 font-medium rounded-lg border border-slate-300 hover:border-slate-400 hover:bg-slate-50 transition-colors"
              >
                See sample insights
              </a>
            </div>
          </div>

          {/* Right: Faux Product Screenshot */}
          <div className="relative">
            <div className="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
              {/* Chat Header */}
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center gap-3">
                <div className="w-8 h-8 bg-teal-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">A</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">Alex</p>
                  <p className="text-xs text-slate-500">Steam Market Analyst</p>
                </div>
              </div>

              {/* Chat Content */}
              <div className="p-4 space-y-4 min-h-[280px]">
                {/* User Message */}
                <div className="flex justify-end">
                  <div className="bg-teal-600 text-white px-4 py-2 rounded-2xl rounded-br-md max-w-[80%]">
                    <p className="text-sm">{activeQuestion}</p>
                  </div>
                </div>

                {/* AI Response */}
                <div className="flex justify-start">
                  <div className="bg-slate-100 text-slate-800 px-4 py-3 rounded-2xl rounded-bl-md max-w-[90%]">
                    <p className="text-sm leading-relaxed">
                      Rogue-like games perform best in the <strong>$10-20 tier</strong> with an 18.3% rate reaching 100K+ estimated owners. There are currently 1,847 rogue-like games on Steam with a 73% average rating.
                    </p>
                    {/* Mini Chart Placeholder */}
                    <div className="mt-3 bg-white rounded-lg p-3 border border-slate-200">
                      <p className="text-xs text-slate-500 mb-2">Success rate by price tier</p>
                      <div className="flex items-end gap-1 h-12">
                        <div className="flex-1 bg-slate-200 rounded-t" style={{ height: '40%' }}>
                          <div className="text-[10px] text-center text-slate-500 mt-1">Free</div>
                        </div>
                        <div className="flex-1 bg-slate-200 rounded-t" style={{ height: '50%' }}>
                          <div className="text-[10px] text-center text-slate-500 mt-1">$5</div>
                        </div>
                        <div className="flex-1 bg-teal-500 rounded-t" style={{ height: '85%' }}>
                          <div className="text-[10px] text-center text-white mt-1">$15</div>
                        </div>
                        <div className="flex-1 bg-slate-200 rounded-t" style={{ height: '65%' }}>
                          <div className="text-[10px] text-center text-slate-500 mt-1">$25</div>
                        </div>
                        <div className="flex-1 bg-slate-200 rounded-t" style={{ height: '55%' }}>
                          <div className="text-[10px] text-center text-slate-500 mt-1">$40</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Sample Questions */}
              <div className="px-4 pb-4">
                <p className="text-xs text-slate-500 mb-2">Try asking:</p>
                <div className="flex flex-wrap gap-2">
                  {sampleQuestions.slice(0, 3).map((q) => (
                    <button
                      key={q}
                      onClick={() => setActiveQuestion(q)}
                      className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                        activeQuestion === q
                          ? 'bg-teal-50 border-teal-300 text-teal-700'
                          : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300'
                      }`}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// --- Trust Strip ---
function TrustStrip() {
  const stats = [
    { value: '77,274', label: 'games indexed' },
    { value: '440', label: 'tags analysed' },
    { value: '28', label: 'genres tracked' },
    { value: '4,457', label: 'multi-game developers' },
  ];

  return (
    <section className="py-12 bg-white border-y border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm text-slate-500 mb-8">
          Built for indie teams making their next big decision
        </p>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-2xl sm:text-3xl font-bold text-slate-900">{stat.value}</p>
              <p className="text-sm text-slate-500">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Data Source Note */}
        <p className="mt-8 text-center text-xs text-slate-400">
          Ownership estimates via <a href="https://steamspy.com" target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-300">SteamSpy</a> + metadata from Steam API.
          Ownership figures are estimates based on public data.
        </p>
      </div>
    </section>
  );
}


// --- Feature Block Component ---
interface FeatureBlockProps {
  title: string;
  copy: string;
  bullets: string[];
  cta: string;
  ctaHref: string;
  reversed?: boolean;
  visual: React.ReactNode;
}

function FeatureBlock({ title, copy, bullets, cta, ctaHref, reversed, visual }: FeatureBlockProps) {
  return (
    <div className={`grid lg:grid-cols-2 gap-12 items-center ${reversed ? 'lg:flex-row-reverse' : ''}`}>
      <div className={reversed ? 'lg:order-2' : ''}>
        <h3 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-4">{title}</h3>
        <p className="text-slate-600 leading-relaxed mb-6">{copy}</p>
        <ul className="space-y-3 mb-6">
          {bullets.map((bullet, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="mt-1 text-teal-600"><Icons.Check /></span>
              <span className="text-slate-600 text-sm">{bullet}</span>
            </li>
          ))}
        </ul>
        <a
          href={ctaHref}
          className="inline-flex items-center gap-2 text-teal-600 font-medium hover:text-teal-700 transition-colors"
        >
          {cta}
          <Icons.ArrowRight />
        </a>
      </div>
      <div className={reversed ? 'lg:order-1' : ''}>
        {visual}
      </div>
    </div>
  );
}

// --- Feature Sections ---
function FeatureSections() {
  return (
    <section id="pricing" className="py-16 lg:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-24">
        {/* Block 1: Conversational Analysis */}
        <FeatureBlock
          title="Skip the spreadsheets. Just ask."
          copy="PlayIntel's AI analyst (we call them Alex) understands indie dev questions and pulls from pre-computed aggregate tables for instant answers. No SQL. No pivot tables. Just answers."
          bullets={[
            '"How saturated is the roguelike market?" → 1,847 games, 73% avg rating, 8.2% reach 100K+ estimated owners',
            '"What\'s the best price for a horror game?" → Data across 7 price tiers with estimated performance',
            '"Show me developers similar to my profile" → Filtered by game count, genre, and estimated performance',
          ]}
          cta="See example conversations"
          ctaHref="#access"
          visual={
            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-slate-200 rounded-full flex-shrink-0"></div>
                  <div className="bg-white rounded-lg p-3 border border-slate-200 flex-1">
                    <p className="text-sm text-slate-600">How saturated is the roguelike market?</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <div className="w-8 h-8 bg-teal-600 rounded-full flex-shrink-0 flex items-center justify-center">
                    <span className="text-white text-xs font-bold">A</span>
                  </div>
                  <div className="bg-teal-50 rounded-lg p-3 border border-teal-100 flex-1">
                    <p className="text-sm text-slate-700">
                      <strong>1,847 rogue-like games</strong> on Steam with a <strong>73% average rating</strong>.
                      About <strong>8.2% reach 100K+ estimated owners</strong> — that's competitive but not oversaturated.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          }
        />


        {/* Block 3: Realistic Expectations */}
        <FeatureBlock
          title="Know what success actually looks like."
          copy="Based on estimated ownership data, ~88% of Steam games have fewer than 100K estimated owners. PlayIntel shows you the distribution to help you set realistic expectations for your situation."
          bullets={[
            'Mega (10M+): ~97 games (0.13% of market)',
            'Hit (1M-10M): ~1,353 games (1.75% of market)',
            'Success (100K-1M): ~7,515 games (9.73% of market)',
            'Moderate (10K-100K): ~68,309 games (88.4% of market)',
          ]}
          cta="See estimated ownership tiers"
          ctaHref="#access"
          reversed
          visual={
            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
              <p className="text-xs text-slate-500 mb-4">Estimated ownership distribution</p>
              <div className="space-y-3">
                {[
                  { tier: 'Mega (10M+)', pct: 0.13, count: '97', color: 'bg-purple-500' },
                  { tier: 'Hit (1M-10M)', pct: 1.75, count: '1,353', color: 'bg-teal-500' },
                  { tier: 'Success (100K-1M)', pct: 9.73, count: '7,515', color: 'bg-blue-500' },
                  { tier: 'Moderate (10K-100K)', pct: 88.4, count: '68,309', color: 'bg-slate-300' },
                ].map((item) => (
                  <div key={item.tier}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-600">{item.tier}</span>
                      <span className="text-slate-500">{item.count} games ({item.pct}%)</span>
                    </div>
                    <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${item.color} rounded-full`}
                        style={{ width: `${Math.max(item.pct, 2)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          }
        />


        {/* Block 5: Price Confidence */}
        <FeatureBlock
          title="Stop guessing your price point."
          copy="See how each price tier performs based on estimated ownership data: average estimated owners, ratings, and relative success rates. Use this to inform your pricing decisions."
          bullets={[
            'Free games: ~294K avg estimated owners, 72% rating',
            'Medium ($10-20): ~182K avg estimated owners, 77% rating',
            'Premium ($30-50): ~795K avg estimated owners, 76% rating',
          ]}
          cta="Compare price tiers"
          ctaHref="#access"
          visual={
            <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
              <p className="text-xs text-slate-500 mb-4">Price tier performance (estimated)</p>
              <div className="space-y-3">
                {[
                  { tier: 'Free', owners: '294K', rating: '72%', success: '19%' },
                  { tier: 'Budget ($0-5)', owners: '43K', rating: '75%', success: '6%' },
                  { tier: 'Low ($5-10)', owners: '79K', rating: '77%', success: '10%' },
                  { tier: 'Medium ($10-20)', owners: '182K', rating: '77%', success: '18%' },
                  { tier: 'Standard ($20-30)', owners: '430K', rating: '76%', success: '35%' },
                  { tier: 'Premium ($30-50)', owners: '795K', rating: '76%', success: '41%' },
                  { tier: 'AAA ($50+)', owners: '1.1M', rating: '63%', success: '30%' },
                ].map((item) => (
                  <div key={item.tier} className="flex items-center gap-4 text-xs">
                    <span className="w-28 text-slate-600">{item.tier}</span>
                    <span className="w-16 text-right text-slate-700 font-medium">{item.owners}</span>
                    <span className="w-12 text-right text-slate-500">{item.rating}</span>
                    <div className="flex-1">
                      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-teal-500 rounded-full"
                          style={{ width: item.success }}
                        ></div>
                      </div>
                    </div>
                    <span className="w-10 text-right text-teal-600 font-medium">{item.success}</span>
                  </div>
                ))}
              </div>
            </div>
          }
        />
      </div>
    </section>
  );
}

// --- Integrations Strip ---
function IntegrationsStrip() {
  const integrations = [
    {
      name: 'CSV Export',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      description: 'Export any data table to Excel-compatible CSV files',
    },
    {
      name: 'Shareable Summaries',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
        </svg>
      ),
      description: 'Generate and share market research summaries with your team',
    },
  ];

  return (
    <section className="py-16 lg:py-24 bg-slate-50 border-y border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-center text-3xl sm:text-4xl font-bold text-slate-900 mb-12">
          Built for your workflow
        </h2>
        <div className="flex flex-wrap justify-center gap-8">
          {integrations.map((int) => (
            <div
              key={int.name}
              className="flex flex-col items-center text-center max-w-[200px]"
            >
              <div className="w-16 h-16 bg-white rounded-xl border border-slate-200 flex items-center justify-center text-teal-600 mb-4 shadow-sm">
                {int.icon}
              </div>
              <p className="font-semibold text-slate-900 mb-1">{int.name}</p>
              <p className="text-sm text-slate-500">{int.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// --- Pricing Section ---
function PricingSection() {
  const tiers = [
    {
      name: 'Free',
      price: '$0',
      period: 'forever',
      description: 'Try PlayIntel with limited queries',
      queries: '5 queries/month',
      features: [
        '5 queries per month',
        'Access to all 77,274 games',
        'Basic market insights',
        'CSV export (limited)',
      ],
      cta: 'Get Started',
      ctaHref: '/signup?plan=free',
      highlighted: false,
    },
    {
      name: 'Indie',
      price: '$29',
      period: '/month',
      description: 'Perfect for solo developers and small teams',
      queries: '150 queries/month',
      features: [
        '150 queries per month',
        'Full market intelligence',
        'Unlimited CSV exports',
        'Chat history & saved insights',
        'Priority response times',
      ],
      cta: 'Start Indie Plan',
      ctaHref: '/signup?plan=indie',
      highlighted: true,
    },
    {
      name: 'Studio',
      price: '$69',
      period: '/user/month',
      description: 'For studios that need unlimited insights',
      queries: 'Unlimited queries',
      features: [
        'Unlimited queries',
        'Everything in Indie',
        'Team collaboration',
        'API access (coming soon)',
        'Dedicated support',
      ],
      cta: 'Start Studio Plan',
      ctaHref: '/signup?plan=studio',
      highlighted: false,
    },
  ];

  return (
    <section id="plans" className="py-16 lg:py-24 bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900">
            Simple, transparent pricing
          </h2>
          <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
            Start free, upgrade when you need more. No hidden fees.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={`relative rounded-2xl p-8 ${
                tier.highlighted
                  ? 'bg-teal-600 text-white shadow-xl scale-105'
                  : 'bg-white text-slate-900 border border-slate-200 shadow-sm'
              }`}
            >
              {tier.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-teal-500 text-white text-xs font-semibold rounded-full">
                  Most Popular
                </div>
              )}
              <div className="text-center mb-6">
                <h3 className={`text-xl font-bold ${tier.highlighted ? 'text-white' : 'text-slate-900'}`}>
                  {tier.name}
                </h3>
                <div className="mt-4 flex items-baseline justify-center gap-1">
                  <span className={`text-4xl font-bold ${tier.highlighted ? 'text-white' : 'text-slate-900'}`}>
                    {tier.price}
                  </span>
                  <span className={`text-sm ${tier.highlighted ? 'text-teal-100' : 'text-slate-500'}`}>
                    {tier.period}
                  </span>
                </div>
                <p className={`mt-2 text-sm ${tier.highlighted ? 'text-teal-100' : 'text-slate-500'}`}>
                  {tier.description}
                </p>
              </div>

              <div className={`mb-6 py-3 px-4 rounded-lg text-center ${
                tier.highlighted ? 'bg-teal-500' : 'bg-slate-50'
              }`}>
                <span className={`font-semibold ${tier.highlighted ? 'text-white' : 'text-teal-600'}`}>
                  {tier.queries}
                </span>
              </div>

              <ul className="space-y-3 mb-8">
                {tier.features.map((feature, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className={tier.highlighted ? 'text-teal-200' : 'text-teal-600'}>
                      <Icons.Check />
                    </span>
                    <span className={`text-sm ${tier.highlighted ? 'text-teal-50' : 'text-slate-600'}`}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              <a
                href={tier.ctaHref}
                className={`block w-full py-3 px-4 rounded-lg font-medium text-center transition-colors ${
                  tier.highlighted
                    ? 'bg-white text-teal-600 hover:bg-teal-50'
                    : 'bg-teal-600 text-white hover:bg-teal-700'
                }`}
              >
                {tier.cta}
              </a>
            </div>
          ))}
        </div>

        <p className="mt-12 text-center text-sm text-slate-500">
          All plans include access to our full database of 77,274 Steam games.
          <br />
          Questions reset on the 1st of each month.
        </p>
      </div>
    </section>
  );
}

// --- Why Choose Section ---
function WhyChoose() {
  const reasons = [
    {
      icon: <Icons.Eye />,
      title: 'Transparent methodology',
      description: 'We clearly show our sources (SteamSpy estimates + Steam API metadata), data limitations, and refresh dates. Ownership data is estimated, not actual sales.',
    },
    {
      icon: <Icons.Compass />,
      title: 'Guided questions',
      description: 'Not sure what to ask? Start with templates like "Validate my concept" or "Find my price point."',
    },
    {
      icon: <Icons.Zap />,
      title: 'Instant answers',
      description: 'Pre-computed aggregate tables mean answers in seconds, not minutes of query time.',
    },
    {
      icon: <Icons.Target />,
      title: 'Built for pre-launch',
      description: 'Designed for the decisions you make before you build — not post-launch analytics.',
    },
  ];

  return (
    <section id="why" className="py-16 lg:py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900">
            Why choose PlayIntel?
          </h2>
          <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
            Built specifically for indie developers making pre-launch decisions.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {reasons.map((reason) => (
            <div
              key={reason.title}
              className="text-center p-6"
            >
              <div className="w-12 h-12 bg-teal-50 rounded-full flex items-center justify-center text-teal-600 mx-auto mb-4">
                {reason.icon}
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">{reason.title}</h3>
              <p className="text-slate-600 text-sm leading-relaxed">{reason.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}


// --- Access Form ---
function AccessForm() {
  const [formState, setFormState] = useState({
    name: '',
    email: '',
    role: '',
    project: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/waitlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formState),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to join waitlist');
      }

      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="access" className="py-16 lg:py-24 bg-slate-900">
      <div className="max-w-xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-8">
          <h2 className="text-3xl sm:text-4xl font-bold text-white">
            Get early access to PlayIntel
          </h2>
          <p className="mt-4 text-lg text-slate-400">
            We're onboarding indie teams in batches. Join the waitlist.
          </p>
        </div>

        {submitted ? (
          <div className="bg-teal-900/50 border border-teal-700 rounded-xl p-8 text-center">
            <div className="w-12 h-12 bg-teal-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Icons.Check />
            </div>
            <p className="text-lg font-medium text-white">You're on the list!</p>
            <p className="mt-2 text-slate-400">We'll be in touch when your spot opens up.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-slate-300 mb-1">
                Name
              </label>
              <input
                type="text"
                id="name"
                required
                value={formState.name}
                onChange={(e) => setFormState({ ...formState, name: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                placeholder="Your name"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-300 mb-1">
                Email
              </label>
              <input
                type="email"
                id="email"
                required
                value={formState.email}
                onChange={(e) => setFormState({ ...formState, email: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="role" className="block text-sm font-medium text-slate-300 mb-1">
                Role
              </label>
              <select
                id="role"
                required
                value={formState.role}
                onChange={(e) => setFormState({ ...formState, role: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              >
                <option value="">Select your role</option>
                <option value="indie">Indie Developer</option>
                <option value="studio">Small Studio</option>
                <option value="publisher">Publisher</option>
                <option value="analyst">Analyst</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label htmlFor="project" className="block text-sm font-medium text-slate-300 mb-1">
                What are you building? <span className="text-slate-500">(optional)</span>
              </label>
              <input
                type="text"
                id="project"
                value={formState.project}
                onChange={(e) => setFormState({ ...formState, project: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                placeholder="e.g., Roguelike deckbuilder, early prototype"
              />
            </div>

            {error && (
              <div className="bg-red-900/50 border border-red-700 rounded-lg p-3 text-red-300 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full px-6 py-3 bg-teal-600 text-white font-medium rounded-lg hover:bg-teal-500 transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Joining...' : 'Join the waitlist'}
            </button>

            <p className="text-xs text-slate-500 text-center">
              We'll only email you about access and major updates. No spam.
            </p>
          </form>
        )}
      </div>
    </section>
  );
}

// --- Footer ---
function Footer() {
  const links = {
    product: [
      { label: 'Features', href: '#features' },
      { label: 'Pricing', href: '#', note: 'Coming soon' },
      { label: 'Changelog', href: '#' },
    ],
    resources: [
      { label: 'Sample Questions', href: '#' },
      { label: 'Data Coverage', href: '#' },
      { label: 'API Docs', href: '#', note: 'Coming soon' },
    ],
    company: [
      { label: 'About', href: '#' },
      { label: 'Contact', href: '#' },
      { label: 'Privacy', href: '#' },
    ],
  };

  return (
    <footer className="bg-slate-900 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="lg:col-span-2">
            <div className="flex items-center mb-4">
              <Logo variant="full" size="sm" />
            </div>
            <p className="text-sm text-slate-400 max-w-xs">
              AI-powered Steam market intelligence for indie game developers.
            </p>
            <div className="flex gap-4 mt-4">
              {/* Social Placeholders */}
              {['Twitter', 'Discord', 'IndieDB'].map((social) => (
                <a
                  key={social}
                  href="#"
                  className="text-slate-500 hover:text-slate-400 text-sm transition-colors"
                  aria-label={social}
                >
                  {social}
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          <div>
            <p className="font-medium text-white mb-4">Product</p>
            <ul className="space-y-2">
              {links.product.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-slate-400 hover:text-white transition-colors">
                    {link.label}
                    {link.note && <span className="text-slate-600 ml-1">({link.note})</span>}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="font-medium text-white mb-4">Resources</p>
            <ul className="space-y-2">
              {links.resources.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-slate-400 hover:text-white transition-colors">
                    {link.label}
                    {link.note && <span className="text-slate-600 ml-1">({link.note})</span>}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="font-medium text-white mb-4">Company</p>
            <ul className="space-y-2">
              {links.company.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-slate-400 hover:text-white transition-colors">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-slate-800">
          <p className="text-xs text-slate-600 text-center max-w-3xl mx-auto mb-4">
            <strong>Data disclaimer:</strong> Ownership figures shown are estimates derived from{' '}
            <a href="https://steamspy.com" target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-400">SteamSpy</a>{' '}
            and do not represent actual sales data. These estimates are based on publicly available information and statistical methods.
            PlayIntel is designed to help inform decisions, not to provide definitive sales figures.
          </p>
          <p className="text-sm text-slate-500 text-center">
            © {new Date().getFullYear()} PlayIntel. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

// ============================================================================
// MAIN PAGE COMPONENT
// ============================================================================

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-white">
      <Navigation />
      <Hero />
      <TrustStrip />
      <FeatureSections />
      <IntegrationsStrip />
      <PricingSection />
      <WhyChoose />
      <AccessForm />
      <Footer />
    </main>
  );
}
