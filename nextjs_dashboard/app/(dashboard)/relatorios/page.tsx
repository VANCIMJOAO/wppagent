"use client";

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import { 
  Download, 
  Calendar, 
  TrendingUp, 
  TrendingDown, 
  MessageCircle, 
  Users, 
  Clock, 
  Star,
  Filter,
  FileText,
  Mail,
  Phone
} from 'lucide-react';
import { toast } from 'sonner';
import { api } from '@/lib/api-service';

// Mock data
const conversationData = [
  { name: 'Jan', conversas: 400, mensagens: 2400, satisfacao: 4.2 },
  { name: 'Fev', conversas: 300, mensagens: 1398, satisfacao: 4.1 },
  { name: 'Mar', conversas: 200, mensagens: 9800, satisfacao: 4.5 },
  { name: 'Abr', conversas: 278, mensagens: 3908, satisfacao: 4.3 },
  { name: 'Mai', conversas: 189, mensagens: 4800, satisfacao: 4.6 },
  { name: 'Jun', conversas: 239, mensagens: 3800, satisfacao: 4.4 },
];

const responseTimeData = [
  { name: 'Seg', tempo: 2.3 },
  { name: 'Ter', tempo: 1.8 },
  { name: 'Qua', tempo: 2.1 },
  { name: 'Qui', tempo: 1.9 },
  { name: 'Sex', tempo: 2.5 },
  { name: 'Sab', tempo: 3.2 },
  { name: 'Dom', tempo: 3.8 },
];

const channelData = [
  { name: 'WhatsApp', value: 65, color: '#25D366' },
  { name: 'Website', value: 20, color: '#0284C7' },
  { name: 'Facebook', value: 10, color: '#1877F2' },
  { name: 'Instagram', value: 5, color: '#E4405F' },
];

const agentPerformance = [
  { agente: 'João Silva', conversas: 145, tempo_resp: '1.8 min', satisfacao: 4.8, status: 'Excelente' },
  { agente: 'Maria Santos', conversas: 132, tempo_resp: '2.1 min', satisfacao: 4.6, status: 'Muito Bom' },
  { agente: 'Pedro Costa', conversas: 98, tempo_resp: '2.5 min', satisfacao: 4.2, status: 'Bom' },
  { agente: 'Ana Oliveira', conversas: 87, tempo_resp: '3.2 min', satisfacao: 3.9, status: 'Regular' },
];

const tagData = [
  { tag: 'Suporte', count: 45, trend: 'up' },
  { tag: 'Vendas', count: 38, trend: 'up' },
  { tag: 'Reclamação', count: 12, trend: 'down' },
  { tag: 'Dúvidas', count: 28, trend: 'stable' },
  { tag: 'Elogios', count: 15, trend: 'up' },
];

export default function ReportsPage() {
  const [dateRange, setDateRange] = useState('30d');
  const [reportType, setReportType] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [dashboardStats, setDashboardStats] = useState<any>(null);

  // Load report data
  useEffect(() => {
    const loadReportData = async () => {
      try {
        setLoading(true);
        const stats = await api.getDashboardStats();
        setDashboardStats(stats);
      } catch (error) {
        console.error('Erro ao carregar dados do relatório:', error);
        toast.error('Erro ao carregar relatório');
      } finally {
        setLoading(false);
      }
    };

    loadReportData();
  }, [dateRange]);

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-red-500" />;
      default: return <div className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Excelente': return 'bg-green-100 text-green-800';
      case 'Muito Bom': return 'bg-blue-100 text-blue-800';
      case 'Bom': return 'bg-yellow-100 text-yellow-800';
      case 'Regular': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const exportReport = (format: string) => {
    alert(`Exportando relatório em formato ${format.toUpperCase()}`);
  };

  return (
    <div className="p-6 space-y-6 max-w-full">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Relatórios</h1>
          <p className="text-gray-600">Análise detalhada do desempenho e métricas</p>
        </div>
        
        <div className="flex items-center gap-3">
          <Select value={dateRange} onValueChange={setDateRange}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Período" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Últimos 7 dias</SelectItem>
              <SelectItem value="30d">Últimos 30 dias</SelectItem>
              <SelectItem value="90d">Últimos 90 dias</SelectItem>
              <SelectItem value="1y">Último ano</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={() => exportReport('pdf')}>
            <Download className="w-4 h-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {/* KPIs Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Conversas</p>
                <p className="text-2xl font-bold text-gray-900">1,847</p>
                <div className="flex items-center mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">+12.5%</span>
                </div>
              </div>
              <MessageCircle className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Clientes Atendidos</p>
                <p className="text-2xl font-bold text-gray-900">1,234</p>
                <div className="flex items-center mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">+8.3%</span>
                </div>
              </div>
              <Users className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tempo Médio Resposta</p>
                <p className="text-2xl font-bold text-gray-900">2.3 min</p>
                <div className="flex items-center mt-1">
                  <TrendingDown className="w-4 h-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">-15.2%</span>
                </div>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Satisfação Média</p>
                <p className="text-2xl font-bold text-gray-900">4.5</p>
                <div className="flex items-center mt-1">
                  <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  <span className="text-sm text-green-600">+5.1%</span>
                </div>
              </div>
              <Star className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs de Relatórios */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="performance">Desempenho</TabsTrigger>
          <TabsTrigger value="channels">Canais</TabsTrigger>
          <TabsTrigger value="agents">Agentes</TabsTrigger>
        </TabsList>

        {/* Visão Geral */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Conversas e Mensagens</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={conversationData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="conversas" fill="#3B82F6" name="Conversas" />
                    <Bar dataKey="mensagens" fill="#10B981" name="Mensagens" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tempo de Resposta Semanal</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={responseTimeData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="tempo" 
                      stroke="#F59E0B" 
                      strokeWidth={3}
                      name="Tempo (min)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Tags Mais Utilizadas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {tagData.map((tag) => (
                  <div key={tag.tag} className="text-center p-4 border rounded-lg">
                    <div className="flex items-center justify-center mb-2">
                      {getTrendIcon(tag.trend)}
                    </div>
                    <p className="font-semibold text-lg">{tag.count}</p>
                    <p className="text-sm text-gray-600">{tag.tag}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Desempenho */}
        <TabsContent value="performance" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Satisfação do Cliente</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={conversationData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 5]} />
                  <Tooltip />
                  <Area 
                    type="monotone" 
                    dataKey="satisfacao" 
                    stroke="#10B981" 
                    fill="#10B981" 
                    fillOpacity={0.6}
                    name="Satisfação"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Canais */}
        <TabsContent value="channels" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Distribuição por Canal</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={channelData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {channelData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Métricas por Canal</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {channelData.map((channel) => (
                    <div key={channel.name} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div 
                          className="w-4 h-4 rounded-full" 
                          style={{ backgroundColor: channel.color }}
                        />
                        <span className="font-medium">{channel.name}</span>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">{channel.value}%</p>
                        <p className="text-sm text-gray-600">{Math.round(channel.value * 18)} conversas</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Agentes */}
        <TabsContent value="agents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Performance dos Agentes</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Agente</th>
                      <th className="text-left p-2">Conversas</th>
                      <th className="text-left p-2">Tempo Resposta</th>
                      <th className="text-left p-2">Satisfação</th>
                      <th className="text-left p-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agentPerformance.map((agent, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-2 font-medium">{agent.agente}</td>
                        <td className="p-2">{agent.conversas}</td>
                        <td className="p-2">{agent.tempo_resp}</td>
                        <td className="p-2">
                          <div className="flex items-center">
                            <Star className="w-4 h-4 text-yellow-500 mr-1" />
                            {agent.satisfacao}
                          </div>
                        </td>
                        <td className="p-2">
                          <Badge 
                            variant="secondary" 
                            className={getStatusColor(agent.status)}
                          >
                            {agent.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}