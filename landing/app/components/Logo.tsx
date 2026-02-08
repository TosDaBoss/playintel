'use client';

interface LogoProps {
  variant?: 'full' | 'icon';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Logo({ variant = 'full', size = 'md', className = '' }: LogoProps) {
  const sizes = {
    sm: { width: variant === 'icon' ? 32 : 140, height: 32 },
    md: { width: variant === 'icon' ? 40 : 160, height: 40 },
    lg: { width: variant === 'icon' ? 48 : 180, height: 48 },
  };

  const { width, height } = sizes[size];

  return (
    <svg
      width={width}
      height={height}
      viewBox={variant === 'icon' ? '0 0 48 48' : '0 0 200 48'}
      fill="none"
      className={className}
    >
      <defs>
        <linearGradient id="logoGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0D9488" />
          <stop offset="100%" stopColor="#14B8A6" />
        </linearGradient>
        <linearGradient id="logoGrad2" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#14B8A6" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#0D9488" stopOpacity="0.9" />
        </linearGradient>
      </defs>

      {variant === 'icon' ? (
        // Icon only - centered in viewBox
        <g transform="translate(4, 4)">
          <rect x="10" y="10" width="28" height="28" rx="7" fill="url(#logoGrad2)" transform="rotate(45 24 24)"/>
          <rect x="6" y="6" width="28" height="28" rx="7" fill="url(#logoGrad1)" transform="rotate(45 20 20)"/>
          <rect x="14" y="14" width="12" height="12" rx="3" fill="white" transform="rotate(45 20 20)"/>
        </g>
      ) : (
        // Full logo with wordmark
        <>
          <g>
            <rect x="8" y="10" width="24" height="24" rx="6" fill="url(#logoGrad2)" transform="rotate(45 20 22)"/>
            <rect x="4" y="8" width="24" height="24" rx="6" fill="url(#logoGrad1)" transform="rotate(45 16 20)"/>
            <rect x="12" y="16" width="8" height="8" rx="2" fill="white" transform="rotate(45 16 20)"/>
          </g>
          <text x="52" y="32" fontFamily="Inter, system-ui, sans-serif" fontSize="22" fontWeight="700" fill="#0F172A">
            Play<tspan fill="#0D9488">Intel</tspan>
          </text>
        </>
      )}
    </svg>
  );
}

// Simple icon version for use in small spaces (navbar, etc.)
export function LogoIcon({ className = '' }: { className?: string }) {
  return (
    <div className={`w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden ${className}`}>
      <svg width="32" height="32" viewBox="0 0 48 48" fill="none">
        <defs>
          <linearGradient id="iconGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0D9488" />
            <stop offset="100%" stopColor="#14B8A6" />
          </linearGradient>
          <linearGradient id="iconGrad2" x1="0%" y1="100%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#14B8A6" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#0D9488" stopOpacity="0.9" />
          </linearGradient>
        </defs>
        <g transform="translate(4, 4)">
          <rect x="10" y="10" width="28" height="28" rx="7" fill="url(#iconGrad2)" transform="rotate(45 24 24)"/>
          <rect x="6" y="6" width="28" height="28" rx="7" fill="url(#iconGrad1)" transform="rotate(45 20 20)"/>
          <rect x="14" y="14" width="12" height="12" rx="3" fill="white" transform="rotate(45 20 20)"/>
        </g>
      </svg>
    </div>
  );
}
