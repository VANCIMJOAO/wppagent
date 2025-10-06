import ConsolidatedSidebar from '@/components/shared/sidebar/Sidebar-consolidated'
import { UniversalErrorBoundary } from '@/components/shared/error-boundary/UniversalErrorBoundary'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <UniversalErrorBoundary
      level="page"
      name="Dashboard Layout"
      maxRetries={3}
      showDetails={true}
      enableRetry={true}
    >
      <ConsolidatedSidebar>
        {children}
      </ConsolidatedSidebar>
    </UniversalErrorBoundary>
  )
}
