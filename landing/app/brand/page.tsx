'use client';

import { useState } from 'react';

// Concept 1: The Aperture - Sophisticated, layered, premium (Teal color scheme)
function LogoConcept1({ variant = 'full' }: { variant?: 'full' | 'icon' }) {
  return (
    <svg width={variant === 'icon' ? '48' : '180'} height="48" viewBox={variant === 'icon' ? '0 0 48 48' : '0 0 200 48'} fill="none">
      <defs>
        <linearGradient id="c1grad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0D9488" />
          <stop offset="100%" stopColor="#14B8A6" />
        </linearGradient>
        <linearGradient id="c1grad2" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#14B8A6" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#0D9488" stopOpacity="0.9" />
        </linearGradient>
      </defs>
      <g transform={variant === 'icon' ? 'translate(8, 4)' : ''}>
        <rect x="8" y="10" width="24" height="24" rx="6" fill="url(#c1grad2)" transform="rotate(45 20 22)"/>
        <rect x="4" y="8" width="24" height="24" rx="6" fill="url(#c1grad1)" transform="rotate(45 16 20)"/>
        <rect x="12" y="16" width="8" height="8" rx="2" fill="white" transform="rotate(45 16 20)"/>
      </g>
      {variant === 'full' && (
        <text x="52" y="32" fontFamily="Inter, system-ui, sans-serif" fontSize="22" fontWeight="700" fill="#0F172A">
          Play<tspan fill="#0D9488">Intel</tspan>
        </text>
      )}
    </svg>
  );
}

// Concept 2: The Spark - Bold, energetic, gaming-forward
function LogoConcept2({ variant = 'full' }: { variant?: 'full' | 'icon' }) {
  return (
    <svg width={variant === 'icon' ? '48' : '180'} height="48" viewBox={variant === 'icon' ? '0 0 48 48' : '0 0 200 48'} fill="none">
      <defs>
        <linearGradient id="c2sparkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#F59E0B" />
          <stop offset="50%" stopColor="#EF4444" />
          <stop offset="100%" stopColor="#EC4899" />
        </linearGradient>
      </defs>
      <g transform={variant === 'icon' ? 'translate(8, 4)' : ''}>
        <rect x="4" y="8" width="32" height="32" rx="8" fill="#0F172A"/>
        <path d="M22 14L14 26H19L17 34L26 22H21L22 14Z" fill="url(#c2sparkGrad)"/>
        <circle cx="12" cy="16" r="2" fill="#F59E0B" opacity="0.6"/>
        <circle cx="28" cy="32" r="1.5" fill="#EC4899" opacity="0.6"/>
      </g>
      {variant === 'full' && (
        <text x="48" y="32" fontFamily="Inter, system-ui, sans-serif" fontSize="22" fontWeight="800" letterSpacing="-0.5" fill="#0F172A">
          play<tspan fontWeight="400">intel</tspan>
        </text>
      )}
    </svg>
  );
}

// Concept 3: The Wave - Friendly, data-driven, approachable
function LogoConcept3({ variant = 'full' }: { variant?: 'full' | 'icon' }) {
  return (
    <svg width={variant === 'icon' ? '48' : '180'} height="48" viewBox={variant === 'icon' ? '0 0 48 48' : '0 0 200 48'} fill="none">
      <defs>
        <linearGradient id="c3waveGrad1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#06B6D4" />
          <stop offset="100%" stopColor="#0EA5E9" />
        </linearGradient>
        <linearGradient id="c3waveGrad2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#0EA5E9" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#6366F1" stopOpacity="0.8" />
        </linearGradient>
      </defs>
      <g transform={variant === 'icon' ? 'translate(8, 4)' : ''}>
        <path d="M4 30C4 30 10 26 16 26C22 26 26 30 32 30C32 30 32 34 32 36C32 38 30 40 28 40H8C6 40 4 38 4 36V30Z" fill="url(#c3waveGrad2)"/>
        <path d="M4 22C4 22 10 18 18 18C26 18 32 22 32 22V28C32 28 26 24 18 24C10 24 4 28 4 28V22Z" fill="url(#c3waveGrad1)" opacity="0.7"/>
        <path d="M4 14C4 12 6 10 8 10H28C30 10 32 12 32 14V18C32 18 26 14 18 14C10 14 4 18 4 18V14Z" fill="url(#c3waveGrad1)"/>
        <path d="M15 20L23 24L15 28V20Z" fill="white" opacity="0.9"/>
      </g>
      {variant === 'full' && (
        <text x="46" y="32" fontFamily="Inter, system-ui, sans-serif" fontSize="21" fontWeight="600" fill="#0F172A">
          Play<tspan fill="#0EA5E9" fontWeight="700">Intel</tspan>
        </text>
      )}
    </svg>
  );
}

const concepts = [
  {
    id: 1,
    name: 'The Aperture',
    tagline: 'Sophisticated & Trustworthy',
    description: 'Inspired by Synthesia\'s layered aperture concept. The overlapping diamond shapes suggest depth, data layers, and discovery. The center window represents the insight you gain. Teal gradient conveys trust, intelligence, and approachability.',
    colors: ['#0D9488', '#14B8A6', '#5EEAD4'],
    personality: ['Trustworthy', 'Professional', 'Intelligent', 'Approachable'],
    bestFor: 'Indie developers, game studios, data-driven decisions',
    Logo: LogoConcept1,
  },
  {
    id: 2,
    name: 'The Spark',
    tagline: 'Bold & Energetic',
    description: 'A lightning bolt within a dark container represents the spark of insight and AI intelligence. Warm gradient (amber to pink) creates energy and excitement. The gaming-forward aesthetic appeals to indie developers.',
    colors: ['#F59E0B', '#EF4444', '#EC4899', '#0F172A'],
    personality: ['Bold', 'Energetic', 'Gaming', 'Fun'],
    bestFor: 'Indie developers, gaming community, social media',
    Logo: LogoConcept2,
  },
  {
    id: 3,
    name: 'The Wave',
    tagline: 'Friendly & Data-Driven',
    description: 'Flowing waves represent data streams and market trends. The embedded play button connects to gaming. Cyan/sky blue is approachable yet professional. Layers suggest the depth of data analysis.',
    colors: ['#06B6D4', '#0EA5E9', '#6366F1'],
    personality: ['Friendly', 'Approachable', 'Community', 'Data'],
    bestFor: 'Community building, content marketing, broad appeal',
    Logo: LogoConcept3,
  },
];

export default function BrandPage() {
  const [selectedConcept, setSelectedConcept] = useState(1);
  const [darkMode, setDarkMode] = useState(false);

  return (
    <div className={`min-h-screen ${darkMode ? 'bg-slate-900' : 'bg-white'}`}>
      {/* Header */}
      <header className={`border-b ${darkMode ? 'border-slate-700' : 'border-slate-200'}`}>
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">PI</span>
            </div>
            <span className={`font-semibold ${darkMode ? 'text-white' : 'text-slate-900'}`}>Brand Concepts</span>
          </a>
          <button
            onClick={() => setDarkMode(!darkMode)}
            className={`px-3 py-1.5 rounded-lg text-sm ${darkMode ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-700'}`}
          >
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-12">
        {/* Title */}
        <div className="text-center mb-12">
          <h1 className={`text-4xl font-bold mb-4 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
            PlayIntel Logo Concepts
          </h1>
          <p className={`text-lg max-w-2xl mx-auto ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>
            Three distinct directions for a trustworthy, fun brand that builds community.
            Inspired by top-tier companies like Synthesia, Notion, and Linear.
          </p>
        </div>

        {/* Logo Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {concepts.map((concept) => (
            <button
              key={concept.id}
              onClick={() => setSelectedConcept(concept.id)}
              className={`p-6 rounded-2xl text-left transition-all ${
                selectedConcept === concept.id
                  ? darkMode
                    ? 'bg-slate-800 ring-2 ring-teal-500'
                    : 'bg-slate-50 ring-2 ring-teal-500'
                  : darkMode
                  ? 'bg-slate-800/50 hover:bg-slate-800'
                  : 'bg-white border border-slate-200 hover:border-slate-300'
              }`}
            >
              {/* Logo Preview */}
              <div className={`h-20 flex items-center justify-center rounded-lg mb-4 ${darkMode ? 'bg-slate-700' : 'bg-slate-100'}`}>
                <concept.Logo variant="full" />
              </div>

              <h3 className={`text-lg font-semibold mb-1 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                {concept.name}
              </h3>
              <p className={`text-sm mb-3 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
                {concept.tagline}
              </p>

              {/* Color Swatches */}
              <div className="flex gap-2">
                {concept.colors.map((color, i) => (
                  <div
                    key={i}
                    className="w-6 h-6 rounded-full border-2 border-white shadow-sm"
                    style={{ backgroundColor: color }}
                  />
                ))}
              </div>
            </button>
          ))}
        </div>

        {/* Selected Concept Detail */}
        {concepts.map((concept) => (
          concept.id === selectedConcept && (
            <div key={concept.id} className={`rounded-2xl p-8 ${darkMode ? 'bg-slate-800' : 'bg-slate-50'}`}>
              <div className="grid md:grid-cols-2 gap-8">
                {/* Left: Visual */}
                <div>
                  <h2 className={`text-2xl font-bold mb-6 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                    {concept.name}
                  </h2>

                  {/* Logo Variants */}
                  <div className="space-y-6">
                    {/* Full Logo on Light */}
                    <div>
                      <p className={`text-xs uppercase tracking-wide mb-2 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                        Full Logo (Light BG)
                      </p>
                      <div className="bg-white rounded-lg p-6 flex items-center justify-center">
                        <concept.Logo variant="full" />
                      </div>
                    </div>

                    {/* Full Logo on Dark */}
                    <div>
                      <p className={`text-xs uppercase tracking-wide mb-2 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                        Full Logo (Dark BG)
                      </p>
                      <div className="bg-slate-900 rounded-lg p-6 flex items-center justify-center">
                        <concept.Logo variant="full" />
                      </div>
                    </div>

                    {/* Icon Only */}
                    <div>
                      <p className={`text-xs uppercase tracking-wide mb-2 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                        Icon Only (Favicon, App Icon)
                      </p>
                      <div className="flex gap-4">
                        <div className="bg-white rounded-lg p-4">
                          <concept.Logo variant="icon" />
                        </div>
                        <div className="bg-slate-900 rounded-lg p-4">
                          <concept.Logo variant="icon" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Details */}
                <div>
                  <div className="mb-6">
                    <h3 className={`font-semibold mb-2 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                      Design Rationale
                    </h3>
                    <p className={`text-sm leading-relaxed ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                      {concept.description}
                    </p>
                  </div>

                  <div className="mb-6">
                    <h3 className={`font-semibold mb-2 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                      Brand Personality
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {concept.personality.map((trait) => (
                        <span
                          key={trait}
                          className={`px-3 py-1 rounded-full text-sm ${
                            darkMode ? 'bg-slate-700 text-slate-300' : 'bg-white text-slate-700 border border-slate-200'
                          }`}
                        >
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className={`font-semibold mb-2 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                      Color Palette
                    </h3>
                    <div className="flex gap-3">
                      {concept.colors.map((color, i) => (
                        <div key={i} className="text-center">
                          <div
                            className="w-12 h-12 rounded-lg shadow-sm mb-1"
                            style={{ backgroundColor: color }}
                          />
                          <span className={`text-xs font-mono ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
                            {color}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className={`font-semibold mb-2 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
                      Best For
                    </h3>
                    <p className={`text-sm ${darkMode ? 'text-slate-300' : 'text-slate-600'}`}>
                      {concept.bestFor}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )
        ))}

        {/* Comparison Table */}
        <div className="mt-16">
          <h2 className={`text-2xl font-bold mb-6 text-center ${darkMode ? 'text-white' : 'text-slate-900'}`}>
            Quick Comparison
          </h2>
          <div className={`rounded-xl overflow-hidden ${darkMode ? 'bg-slate-800' : 'bg-white border border-slate-200'}`}>
            <table className="w-full">
              <thead>
                <tr className={darkMode ? 'bg-slate-700' : 'bg-slate-50'}>
                  <th className={`px-6 py-4 text-left text-sm font-semibold ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>Aspect</th>
                  <th className={`px-6 py-4 text-center text-sm font-semibold ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>Aperture</th>
                  <th className={`px-6 py-4 text-center text-sm font-semibold ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>Spark</th>
                  <th className={`px-6 py-4 text-center text-sm font-semibold ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>Wave</th>
                </tr>
              </thead>
              <tbody className={`divide-y ${darkMode ? 'divide-slate-700' : 'divide-slate-100'}`}>
                {[
                  ['Vibe', 'Premium/Tech', 'Bold/Gaming', 'Friendly/Data'],
                  ['Primary Color', 'Purple/Indigo', 'Orange/Pink', 'Cyan/Blue'],
                  ['Target Audience', 'Enterprise', 'Indie Devs', 'Everyone'],
                  ['Trustworthy', '5/5', '3/5', '4/5'],
                  ['Fun', '3/5', '5/5', '4/5'],
                  ['Community Feel', '3/5', '4/5', '5/5'],
                  ['Similar To', 'Linear, Figma', 'Discord, Epic', 'Notion, Loom'],
                ].map(([aspect, ...values]) => (
                  <tr key={aspect}>
                    <td className={`px-6 py-3 text-sm font-medium ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>{aspect}</td>
                    {values.map((val, i) => (
                      <td key={i} className={`px-6 py-3 text-sm text-center ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>{val}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recommendation */}
        <div className={`mt-12 p-6 rounded-xl ${darkMode ? 'bg-teal-900/30 border border-teal-700' : 'bg-teal-50 border border-teal-200'}`}>
          <h3 className={`font-semibold mb-2 ${darkMode ? 'text-teal-300' : 'text-teal-800'}`}>
            Recommendation
          </h3>
          <p className={`text-sm ${darkMode ? 'text-teal-200' : 'text-teal-700'}`}>
            For a "strong, trustworthy but fun brand with community focus," I recommend <strong>Concept 3: The Wave</strong> or a hybrid approach combining the sophistication of Concept 1 with the friendly colors of Concept 3. The cyan/blue palette is approachable, the data visualization elements build trust, and the play button creates gaming connection without being too niche.
          </p>
        </div>
      </main>
    </div>
  );
}
