import Sidebar from '@/components/layout/sidebar'
import { AdvancedErrorBoundary } from '@/components/error-boundaries/AdvancedErrorBoundary'
import { ApiErrorBoundary } from '@/components/error-boundaries/ApiErrorBoundary'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AdvancedErrorBoundary
      level="page"
      context="Dashboard Layout"
      retryAttempts={3}
      showErrorDetails={true}
    >
      <ApiErrorBoundary
        level="important"
        enableRetry={true}
        maxRetries={5}
        showToast={true}
      >
        <Sidebar>
          {children}
        </Sidebar>
      </ApiErrorBoundary>
    </AdvancedErrorBoundary>
  )
}
