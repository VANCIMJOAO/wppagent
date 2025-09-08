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
        <AuthProvider>
          <ErrorBoundary>
            <div className="min-h-screen bg-gray-50">
              {children}
            </div>
          </ErrorBoundary>
        </AuthProvider>
      </body>
    </html>
  )
}