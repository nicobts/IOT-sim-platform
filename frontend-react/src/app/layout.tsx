import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: {
    default: 'IOT SIM Platform',
    template: '%s | IOT SIM Platform',
  },
  description: 'Manage your IoT SIM cards with 1NCE integration - Next.js 15 & React 19',
  keywords: ['IoT', 'SIM', '1NCE', 'Management', 'Platform'],
  authors: [{ name: 'IOT SIM Platform Team' }],
  creator: 'IOT SIM Platform',
  publisher: 'IOT SIM Platform',
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://iot-sim-platform.com',
    title: 'IOT SIM Platform',
    description: 'Manage your IoT SIM cards with 1NCE integration',
    siteName: 'IOT SIM Platform',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'IOT SIM Platform',
    description: 'Manage your IoT SIM cards with 1NCE integration',
  },
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
}

// Enable Partial Prerendering for this layout
export const experimental_ppr = true

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <head>
        {/* DNS Prefetch for API */}
        <link rel="dns-prefetch" href={process.env.NEXT_PUBLIC_API_URL} />
        {/* Preconnect for faster API calls */}
        <link rel="preconnect" href={process.env.NEXT_PUBLIC_API_URL} />
      </head>
      <body className={`${inter.className} antialiased`}>
        {/* React 19: Children are automatically optimized by the compiler */}
        {children}
      </body>
    </html>
  )
}
