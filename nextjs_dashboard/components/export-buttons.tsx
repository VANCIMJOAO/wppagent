"use client"

import { Button } from '@/components/ui/button'
import { Download, FileText, FileSpreadsheet, Database, Loader2 } from 'lucide-react'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '@/components/ui/dropdown-menu'
import { useState } from 'react'
import { debugLog } from '@/lib/debug';

interface ExportButtonsProps {
  periodDays?: number
  startDate?: string
  endDate?: string
  className?: string
}

export function ExportButtons({
  periodDays = 30,
  startDate,
  endDate,
  className = ""
}: ExportButtonsProps) {
  const [loading, setLoading] = useState<string | null>(null)

  const showNotification = (title: string, message: string, type: 'success' | 'error' = 'success') => {
    // Usar alert temporariamente até implementar toast
    if (type === 'error') {
      alert(`❌ ${title}: ${message}`)
    } else {
      alert(`✅ ${title}: ${message}`)
    }
  }

  const downloadFile = async (url: string, filename: string, exportType: string) => {
    try {
      setLoading(exportType)

      // 🔒 SECURITY: Usando cookies HttpOnly seguros via credentials: 'include'
      const response = await fetch(url, {
        credentials: 'include', // Inclui cookies HttpOnly automaticamente
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        if (response.status === 401) {
          showNotification(
            "Erro de Autenticação",
            "Acesso negado. Verifique suas credenciais.",
            'error'
          )
          return
        }

        const error = await response.text()
        throw new Error(`HTTP ${response.status}: ${error}`)
      }

      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(downloadUrl)

      showNotification(
        "Download Concluído",
        `Arquivo ${filename} baixado com sucesso!`
      )

    } catch (error: any) {
      debugLog.error('Erro no download:', error)
      showNotification(
        "Erro no Download",
        error.message || "Falha ao baixar arquivo. Tente novamente.",
        'error'
      )
    } finally {
      setLoading(null)
    }
  }

  const exportAppointmentsCSV = () => {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)

    const url = `/api/export/appointments/csv?${params}`
    const filename = `agendamentos_${new Date().toISOString().split('T')[0]}.csv`
    downloadFile(url, filename, 'csv')
  }

  const exportAnalyticsExcel = () => {
    const url = `/api/export/analytics/excel?period_days=${periodDays}`
    const filename = `analytics_${periodDays}dias_${new Date().toISOString().split('T')[0]}.xlsx`
    downloadFile(url, filename, 'excel')
  }

  const exportExecutivePDF = () => {
    const url = `/api/export/executive/pdf?period_days=${periodDays}`
    const filename = `relatorio_executivo_${periodDays}dias_${new Date().toISOString().split('T')[0]}.pdf`
    downloadFile(url, filename, 'pdf')
  }

  const isLoading = loading !== null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className={`relative ${className}`}
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
          ) : (
            <Download className="w-4 h-4 mr-2" />
          )}
          {isLoading ? 'Gerando...' : 'Exportar'}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-56">
        <div className="px-2 py-1.5">
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Relatórios Disponíveis
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Exportar dados para análise
          </p>
        </div>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          onClick={exportAppointmentsCSV}
          disabled={loading === 'csv'}
          className="cursor-pointer"
        >
          <div className="flex items-center w-full">
            {loading === 'csv' ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Database className="w-4 h-4 mr-2" />
            )}
            <div className="flex-1">
              <div className="font-medium">Agendamentos (CSV)</div>
              <div className="text-xs text-gray-500">
                Dados detalhados para Excel
              </div>
            </div>
          </div>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={exportAnalyticsExcel}
          disabled={loading === 'excel'}
          className="cursor-pointer"
        >
          <div className="flex items-center w-full">
            {loading === 'excel' ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <FileSpreadsheet className="w-4 h-4 mr-2" />
            )}
            <div className="flex-1">
              <div className="font-medium">Analytics Completas (Excel)</div>
              <div className="text-xs text-gray-500">
                Múltiplas abas com gráficos
              </div>
            </div>
          </div>
        </DropdownMenuItem>

        <DropdownMenuItem
          onClick={exportExecutivePDF}
          disabled={loading === 'pdf'}
          className="cursor-pointer"
        >
          <div className="flex items-center w-full">
            {loading === 'pdf' ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <FileText className="w-4 h-4 mr-2" />
            )}
            <div className="flex-1">
              <div className="font-medium">Relatório Executivo (PDF)</div>
              <div className="text-xs text-gray-500">
                Formatado para apresentação
              </div>
            </div>
          </div>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <div className="px-2 py-1.5">
          <p className="text-xs text-gray-400">
            {periodDays ? `Período: ${periodDays} dias` : 'Período personalizado'}
          </p>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
