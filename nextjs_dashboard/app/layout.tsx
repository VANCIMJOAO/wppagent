import './globals.css'
import { Inter } from 'next/font/google'
import { AuthProvider } from '@/contexts/auth-context'
import { UniversalErrorBoundary } from '@/components/shared/error-boundary/UniversalErrorBoundary'
import { ConsolidatedErrorProvider } from '@/components/shared/error-boundary/ConsolidatedErrorProvider'
import { ConsolidatedToastProvider } from '@/components/shared/toast/ToastProvider-consolidated'
import { ReactQueryProvider } from '@/components/providers/react-query-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'WhatsApp Agent Dashboard',
  description: 'Dashboard de gestão do WhatsApp Agent'
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
      </head>
      <body className={inter.className}>
        <ConsolidatedErrorProvider>
          <ConsolidatedToastProvider>
            <UniversalErrorBoundary
              level="global"
              name="Root Application"
              showDetails={false}
              maxRetries={3}
            >
              <ReactQueryProvider>
                <AuthProvider>
                  <div className="min-h-screen bg-gray-50">
                    {children}
                  </div>
                </AuthProvider>
              </ReactQueryProvider>
            </UniversalErrorBoundary>
          </ConsolidatedToastProvider>
        </ConsolidatedErrorProvider>
      </body>
    </html>
  )
}
