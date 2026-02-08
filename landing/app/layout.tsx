import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'PlayIntel — AI-Powered Steam Market Intelligence',
  description: 'Talk to Steam data and get decision-grade answers in seconds. Validate game concepts, set competitive prices, and find underserved niches.',
  keywords: ['steam', 'indie games', 'game development', 'market research', 'pricing', 'analytics'],
  authors: [{ name: 'PlayIntel' }],
  openGraph: {
    title: 'PlayIntel — AI-Powered Steam Market Intelligence',
    description: 'Talk to Steam data and get decision-grade answers in seconds.',
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
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
