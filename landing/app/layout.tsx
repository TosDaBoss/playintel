import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Analytics } from '@vercel/analytics/react';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'PlayIntel — AI-Powered Game Market Intelligence',
  description: 'Talk to game market data and get decision-grade answers in seconds. Validate game concepts, set competitive prices, and find underserved niches.',
  keywords: ['indie games', 'game development', 'market research', 'pricing', 'analytics', 'game market'],
  authors: [{ name: 'PlayIntel' }],
  openGraph: {
    title: 'PlayIntel — AI-Powered Game Market Intelligence',
    description: 'Talk to game market data and get decision-grade answers in seconds.',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        {/* Google tag (gtag.js) */}
        <script async src="https://www.googletagmanager.com/gtag/js?id=AW-17948130851"></script>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', 'AW-17948130851');
            `,
          }}
        />
      </head>
      <body className={inter.className}>
        <Providers>{children}</Providers>
        <Analytics />
      </body>
    </html>
  );
}
