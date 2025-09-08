import Sidebar from '@/components/layout/sidebar'
import { DashboardErrorBoundary } from '@/components/error-boundaries'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <DashboardErrorBoundary>
      <Sidebar>
        {children}
      </Sidebar>
    </DashboardErrorBoundary>
  )
}
