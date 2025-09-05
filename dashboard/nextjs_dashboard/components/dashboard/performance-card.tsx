'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TrendingUp } from "lucide-react"

export const PerformanceCard = () => {
  const metrics = [
    { label: "Conversas iniciadas", value: "8" },
    { label: "Mensagens enviadas", value: "67" },
    { label: "Taxa de resposta", value: "94%", highlight: true }
  ]

  return (
    <Card className="animate-fadeInUp">
      <CardHeader>
        <CardTitle className="text-lg font-semibold flex items-center">
          <TrendingUp className="h-5 w-5 mr-2 text-blue-600" />
          Performance Hoje
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {metrics.map((metric, index) => (
          <div key={index} className="flex justify-between items-center">
            <span className="text-sm text-gray-600">{metric.label}</span>
            <span className={`font-semibold ${
              metric.highlight ? 'text-green-600' : 'text-gray-900'
            }`}>
              {metric.value}
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}