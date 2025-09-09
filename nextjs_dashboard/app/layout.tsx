import './globals.css'
import { Inter } from 'next/font/google'
import { AuthProvider } from '@/contexts/auth-context'
import ErrorBoundary from '@/components/error-boundary'
import { PWAWrapper, PWAInstallDetector } from '@/components/pwa/PWAWrapper'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'WhatsApp Agent Dashboard',
  description: 'Dashboard de gestão do WhatsApp Agent - Funciona offline como PWA',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'WA Agent'
  },
  icons: {
    icon: [
      { url: '/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512x512.png', sizes: '512x512', type: 'image/png' }
    ],
    apple: [
      { url: '/icon-192x192.png', sizes: '192x192', type: 'image/png' }
    ]
  }
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: 'cover',
  themeColor: '#366092'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <head>
        {/* PWA Meta Tags */}
        <meta name="theme-color" content="#366092" />
        <meta name="background-color" content="#ffffff" />
        <meta name="display" content="standalone" />
        <meta name="orientation" content="portrait-primary" />
        
        {/* iOS PWA Meta Tags */}
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="WA Agent" />
        
        {/* iOS Icons */}
        <link rel="apple-touch-icon" href="/icon-192x192.png" />
        <link rel="apple-touch-icon" sizes="152x152" href="/icon-152x152.png" />
        <link rel="apple-touch-icon" sizes="192x192" href="/icon-192x192.png" />
        
        {/* Standard Icons */}
        <link rel="icon" type="image/png" sizes="192x192" href="/icon-192x192.png" />
        <link rel="icon" type="image/png" sizes="512x512" href="/icon-512x512.png" />
        
        {/* Manifest */}
        <link rel="manifest" href="/manifest.json" />
        
        {/* Preload Service Worker */}
        <link rel="preload" href="/sw-advanced.js" as="script" />
      </head>
      <body className={inter.className}>
        <ErrorBoundary
        level="global"
        name="RootLayout"
        >
          <PWAWrapper>
            <AuthProvider>
              <div className="min-h-screen bg-gray-50">
                {children}
              </div>
              <PWAInstallDetector />
            </AuthProvider>
          </PWAWrapper>
        </ErrorBoundary>
      </body>
    </html>
  )
}