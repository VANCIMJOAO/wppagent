'use client'

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

const data = [
  { name: 'Seg', conversas: 12 },
  { name: 'Ter', conversas: 19 },
  { name: 'Qua', conversas: 13 },
  { name: 'Qui', conversas: 25 },
  { name: 'Sex', conversas: 18 },
  { name: 'Sáb', conversas: 22 },
  { name: 'Dom', conversas: 16 },
]

export const ConversationsChart = () => {
  return (
    <Card className="animate-fadeInUp">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg font-semibold">Conversas - 7 dias</CardTitle>
        <Button variant="ghost" size="sm">
          <RefreshCw className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="conversas" fill="#667eea" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
