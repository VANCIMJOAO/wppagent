import './globals.css'
import { Inter } from 'next/font/google'
import { AuthProvider } from '@/contexts/auth-context'
import { AdvancedErrorBoundary } from '@/components/error-boundaries/AdvancedErrorBoundary'
import { ErrorProvider } from '@/components/error-boundaries/ErrorProvider'
import { ToastProvider } from '@/components/error-boundaries/ToastProvider'
import { ReactQueryProvider } from '@/components/providers/react-query-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'WhatsApp Agent Dashboard',
  description: 'Dashboard de gestão do WhatsApp Agent',
  icons: {
    icon: [
      { url: '/icon-96x96.png', sizes: '96x96', type: 'image/png' },
      { url: '/icon-128x128.png', sizes: '128x128', type: 'image/png' }
    ]
  }
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <head>
        {/* Standard Icons */}
        <link rel="icon" type="image/png" sizes="96x96" href="/icon-96x96.png" />
        <link rel="icon" type="image/png" sizes="128x128" href="/icon-128x128.png" />
      </head>
      <body className={inter.className}>
        <ErrorProvider>
          <ToastProvider>
            <AdvancedErrorBoundary
              level="page"
              context="Root Application"
              showErrorDetails={false}
            >
              <ReactQueryProvider>
                <AuthProvider>
                  <div className="min-h-screen bg-gray-50">
                    {children}
                  </div>
                </AuthProvider>
              </ReactQueryProvider>
            </AdvancedErrorBoundary>
          </ToastProvider>
        </ErrorProvider>
      </body>
    </html>
  )
}
