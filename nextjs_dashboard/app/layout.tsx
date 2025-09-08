import './globals.css'
import { Inter } from 'next/font/google'
import { AuthProvider } from '@/contexts/auth-context'
import ErrorBoundary from '@/components/error-boundary'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'WppAgent Dashboard',
  description: 'Dashboard moderno para gestão de atendimentos WhatsApp',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body className={inter.className}>
        <ErrorBoundary
          level="global"
          name="RootLayout"
          onError={(error, errorInfo) => {
            // Log crítico para erros globais
            console.error('🚨 Critical Global Error:', {
              message: error.message,
              stack: error.stack,
              componentStack: errorInfo.componentStack,
              timestamp: new Date().toISOString(),
              url: typeof window !== 'undefined' ? window.location.href : 'SSR'
            });
          }}
        >
          <AuthProvider>
            <div className="min-h-screen bg-gray-50">
              {children}
            </div>
          </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  )
}