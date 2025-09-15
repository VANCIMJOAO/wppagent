/**
 * Seção de estatísticas do Dashboard com Loading States
 * BUG-006: Implementar Loading States
 */

import { DashboardSkeleton } from '@/components/ui/skeleton'
import { useDashboardStats } from '@/hooks/useDashboardStats'
import { ErrorFallback } from '@/components/ui/error-fallback'
import { StatsCards } from '@/components/dashboard/stats-cards'

export function StatsSection() {
  const { stats, loading, error } = useDashboardStats()

  if (loading) return <DashboardSkeleton />
  if (error) return <ErrorFallback error={error} />

  return <StatsCards stats={stats} />
}

// Seção de estatísticas com período selecionável
interface StatsWithPeriodProps {
  period: 'daily' | 'weekly' | 'monthly' | 'yearly'
  onPeriodChange?: (period: 'daily' | 'weekly' | 'monthly' | 'yearly') => void
}

export function StatsWithPeriod({ period, onPeriodChange }: StatsWithPeriodProps) {
  const { stats, loading, error } = useDashboardStats()

  if (loading) return <DashboardSkeleton />
  if (error) return <ErrorFallback error={error} retry={() => window.location.reload()} />

  return (
    <div className="space-y-4">
      {onPeriodChange && (
        <div className="flex justify-end">
          <select
            value={period}
            onChange={(e) => onPeriodChange(e.target.value as any)}
            className="px-3 py-2 border rounded-md bg-white"
          >
            <option value="daily">Hoje</option>
            <option value="weekly">Esta Semana</option>
            <option value="monthly">Este Mês</option>
            <option value="yearly">Este Ano</option>
          </select>
        </div>
      )}
      <StatsCards stats={stats} period={period} />
    </div>
  )
}
