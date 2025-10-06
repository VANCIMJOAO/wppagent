"use client";

import { useState, useEffect } from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Calendar,
  CalendarPlus,
  Search,
  Filter,
  Clock,
  User,
  Phone,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Edit,
  Trash2,
  Loader2,
  Wifi,
  WifiOff
} from 'lucide-react';
import type { Appointment as ApiAppointment, AppointmentStatus } from '@/types/api';
import { toast } from 'sonner';
import { ExportButtons } from '@/components/export-buttons';
import { useWebSocketRobust } from '@/hooks/useWebSocketRobust';
import AppointmentModal from '@/components/appointments/AppointmentModal';
import DeleteConfirmationModal from '@/components/appointments/DeleteConfirmationModal';
import { debugLog } from '@/lib/debug';

interface AppointmentStats {
  total: number;
  confirmed: number;
  pending: number;
  cancelled: number;
  completed: number;
  today: number;
  thisWeek: number;
  thisMonth: number;
}

// Definir tipos específicos para os mapeamentos
const statusColors: Record<string, string> = {
    'confirmado': 'bg-green-100 text-green-800',
    'agendado': 'bg-yellow-100 text-yellow-800',
    'scheduled': 'bg-yellow-100 text-yellow-800', // ✅ Alias para agendado
    'cancelado': 'bg-red-100 text-red-800',
    'cancelled': 'bg-red-100 text-red-800', // ✅ Alias para cancelado
    'realizado': 'bg-blue-100 text-blue-800',
    'completed': 'bg-blue-100 text-blue-800', // ✅ Alias para realizado
    'pendente': 'bg-gray-100 text-gray-800',
    'pending': 'bg-gray-100 text-gray-800', // ✅ Alias para pendente
};

const statusLabels: Record<string, string> = {
  'confirmado': 'Confirmado',
  'agendado': 'Agendado',
  'scheduled': 'Agendado', // ✅ Alias para agendado
  'cancelado': 'Cancelado',
  'cancelled': 'Cancelado', // ✅ Alias para cancelado
  'realizado': 'Realizado',
  'completed': 'Realizado', // ✅ Alias para realizado
  'pendente': 'Pendente',
  'pending': 'Pendente', // ✅ Alias para pendente
};

const statusIcons: Record<string, LucideIcon> = {
  'confirmado': CheckCircle,
  'agendado': AlertCircle,
  'scheduled': AlertCircle, // ✅ Alias para agendado
  'cancelado': XCircle,
  'cancelled': XCircle, // ✅ Alias para cancelado
  'realizado': CheckCircle,
  'completed': CheckCircle, // ✅ Alias para realizado
  'pendente': Clock,
  'pending': Clock, // ✅ Alias para pendente
};

export default function AgendamentosPage() {
  const [appointments, setAppointments] = useState<ApiAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [selectedTab, setSelectedTab] = useState('list');
  const [appointmentStats, setAppointmentStats] = useState<AppointmentStats>({
    total: 0,
    confirmed: 0,
    pending: 0,
    cancelled: 0,
    completed: 0,
    today: 0,
    thisWeek: 0,
    thisMonth: 0
  });

  // Estados para modais
  const [isAppointmentModalOpen, setIsAppointmentModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<ApiAppointment | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  
  // Dados para os modais
  const [clients, setClients] = useState<Array<{ id: number; nome: string; telefone: string }>>([]);
  const [services, setServices] = useState<Array<{ id: number; name: string; duration_minutes: number; price: number }>>([]);

  // WebSocket para atualizações em tempo real
  const { isConnected, error, reconnect } = useWebSocketRobust('ws://localhost:8000/ws');

  // WebSocket irá invalidar o cache automaticamente quando receber eventos

  // Funções para modais
  const handleOpenAppointmentModal = (appointment?: ApiAppointment) => {
    // ✅ Garantir que o modal anterior seja fechado primeiro
    setIsAppointmentModalOpen(false);
    setSelectedAppointment(null);
    
    // ✅ Pequeno delay para garantir re-render
    setTimeout(() => {
      setSelectedAppointment(appointment || null);
      setIsAppointmentModalOpen(true);
    }, 50);
  };

  const handleCloseAppointmentModal = () => {
    setIsAppointmentModalOpen(false);
    setSelectedAppointment(null);
  };

  const handleOpenDeleteModal = (appointment: ApiAppointment) => {
    setSelectedAppointment(appointment);
    setIsDeleteModalOpen(true);
  };

  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setSelectedAppointment(null);
  };

  const handleDeleteAppointment = async () => {
    if (!selectedAppointment) return;

    setIsDeleting(true);
    try {
      const response = await fetch(`/api/appointments/${selectedAppointment.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Erro ao excluir agendamento');
      }

      toast.success('Agendamento excluído com sucesso!');
      await loadData(); // Recarregar dados
      handleCloseDeleteModal();
    } catch (error) {
      debugLog.error('Erro ao excluir agendamento:', error);
      toast.error(
        error instanceof Error 
          ? error.message 
          : 'Erro ao excluir agendamento'
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const handleAppointmentSuccess = async () => {
    await loadData(); // Recarregar dados após criar/editar
  };

  // Load data from API
  async function loadData() {
    try {
      setLoading(true);

      const [appointmentsResponse, dashboardResponse] = await Promise.all([
        fetch('/api/appointments', { credentials: 'include' }).then(r => r.json()),
        fetch('/api/dashboard/stats', { credentials: 'include' }).then(r => r.json())
      ]);

      // Acessa os dados da resposta da API
      const appointmentsData = appointmentsResponse.data || [];
      const dashboardData = dashboardResponse.data || {};

      // Garantir que appointmentsData é um array
      const safeAppointmentsData = Array.isArray(appointmentsData) ? appointmentsData : [];
      setAppointments(safeAppointmentsData);

      // Calculate stats from actual appointments data
      const today = new Date().toDateString();
      const thisWeek = new Date();
      thisWeek.setDate(thisWeek.getDate() - thisWeek.getDay()); // Start of week
      const thisMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1); // Start of month

      const calculatedStats: AppointmentStats = {
        total: safeAppointmentsData.length || 0,
        confirmed: safeAppointmentsData.filter((a: any) => a.status === 'confirmado').length || 0,
        pending: safeAppointmentsData.filter((a: any) => a.status === 'agendado').length || 0,
        cancelled: safeAppointmentsData.filter((a: any) => a.status === 'cancelado').length || 0,
        completed: safeAppointmentsData.filter((a: any) => a.status === 'realizado').length || 0,
        today: safeAppointmentsData.filter((a: any) =>
            new Date(a.data_agendamento).toDateString() === today
          ).length || 0,
          thisWeek: safeAppointmentsData.filter((a: any) =>
            new Date(a.data_agendamento) >= thisWeek
          ).length || 0,
          thisMonth: safeAppointmentsData.filter((a: any) =>
            new Date(a.data_agendamento) >= thisMonth
          ).length || 0
        };

        setAppointmentStats(calculatedStats);

      } catch (error) {
        debugLog.error('Erro ao carregar dados dos agendamentos:', error);
        toast.error('Erro ao carregar dados dos agendamentos');
      } finally {
        setLoading(false);
      }
    }

    // Load data initially
  useEffect(() => {
    loadData();
    loadClientsAndServices();
  }, []);

  // Carregar dados de clientes e serviços para os modais
  const loadClientsAndServices = async () => {
    try {
      debugLog.info('Carregando dados reais de clientes e serviços...');
      
      // Buscar clientes reais do banco
      const clientsResponse = await fetch('/api/clients?limit=100', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!clientsResponse.ok) {
        throw new Error(`Erro ao buscar clientes: ${clientsResponse.status}`);
      }

      const clientsData = await clientsResponse.json();
      debugLog.success(`Clientes carregados: ${clientsData.clients?.length || 0}`);
      
      // Buscar serviços reais do banco
      const servicesResponse = await fetch('/api/services?limit=100', {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!servicesResponse.ok) {
        throw new Error(`Erro ao buscar serviços: ${servicesResponse.status}`);
      }

      const servicesData = await servicesResponse.json();
      debugLog.success(`Serviços carregados: ${servicesData.services?.length || 0}`);

      // Mapear dados para o formato esperado pelo modal
      setClients(
        (clientsData.clients || []).map((client: any) => ({
          id: client.id,
          nome: client.nome,
          telefone: client.telefone,
        }))
      );

      setServices(
        (servicesData.services || []).map((service: any) => ({
          id: service.id,
          name: service.name,
          duration_minutes: service.duration_minutes,
          price: service.price,
        }))
      );

      debugLog.success('Dados reais carregados com sucesso!');
    } catch (error) {
      debugLog.error('Erro ao carregar dados para modais:', error);
      
      // Sem fallback - apenas exibir erro e manter arrays vazios
      toast.error('Erro ao carregar clientes e serviços. Verifique sua conexão.');
      setClients([]);
      setServices([]);
    }
  };

  const filteredAppointments = appointments.filter(appointment => {
    const matchesSearch = appointment.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         appointment.service_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || appointment.status === statusFilter;

    let matchesDate = true;
    if (dateFilter === 'today' && appointment.data_agendamento) {
      const today = new Date().toDateString();
      matchesDate = new Date(appointment.data_agendamento).toDateString() === today;
    } else if (dateFilter === 'tomorrow' && appointment.data_agendamento) {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      matchesDate = new Date(appointment.data_agendamento).toDateString() === tomorrow.toDateString();
    } else if (dateFilter === 'week' && appointment.data_agendamento) {
      const weekFromNow = new Date();
      weekFromNow.setDate(weekFromNow.getDate() + 7);
      matchesDate = new Date(appointment.data_agendamento) <= weekFromNow;
    }

    return matchesSearch && matchesStatus && matchesDate;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('pt-BR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const groupAppointmentsByDate = (appointments: ApiAppointment[]) => {
    const grouped: { [key: string]: ApiAppointment[] } = {};
    appointments.forEach(appointment => {
      if (appointment.data_agendamento) {
        const date = formatDate(appointment.data_agendamento);
        if (!grouped[date]) {
          grouped[date] = [];
        }
        grouped[date].push(appointment);
      }
    });
    return grouped;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6 space-y-6" data-testid="appointments-page">
      {/* Header Moderno */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-md">
            <Calendar className="h-7 w-7 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              Agendamentos
            </h1>
            <p className="text-gray-500 mt-0.5 text-sm">Gerencie sua agenda de forma inteligente</p>
          </div>
          {/* WebSocket Status - Compacto */}
          <Badge
            variant={isConnected ? "default" : "destructive"}
            className={`flex items-center gap-1.5 px-2.5 py-1 ${
              isConnected ? "bg-green-50 text-green-700 border-green-200" : "bg-red-50 text-red-700 border-red-200"
            }`}
          >
            {isConnected ? (
              <Wifi className="w-3.5 h-3.5" />
            ) : (
              <WifiOff className="w-3.5 h-3.5" />
            )}
            <span className="text-xs font-medium">{isConnected ? "Online" : "Offline"}</span>
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          <ExportButtons
            startDate={new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0]}
            endDate={new Date().toISOString().split('T')[0]}
            className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white hover:from-emerald-600 hover:to-teal-700 shadow-md transition-all duration-200"
          />
          <Button 
            onClick={() => handleOpenAppointmentModal()}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-md transition-all duration-200"
          >
            <CalendarPlus className="h-4 w-4 mr-2" />
            Novo Agendamento
          </Button>
        </div>
      </div>

      {/* Stats Cards - Design Moderno */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Total */}
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200 hover:shadow-lg transition-shadow duration-200">
          <CardContent className="p-5">
            <div className="flex flex-col space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Total</p>
                <div className="p-2 bg-blue-500 rounded-lg">
                  <Calendar className="h-4 w-4 text-white" />
                </div>
              </div>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold text-blue-900">{appointmentStats.total}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Hoje */}
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200 hover:shadow-lg transition-shadow duration-200">
          <CardContent className="p-5">
            <div className="flex flex-col space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-orange-700 uppercase tracking-wide">Hoje</p>
                <div className="p-2 bg-orange-500 rounded-lg">
                  <Clock className="h-4 w-4 text-white" />
                </div>
              </div>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold text-orange-900">{appointmentStats.today}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Confirmados */}
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200 hover:shadow-lg transition-shadow duration-200">
          <CardContent className="p-5">
            <div className="flex flex-col space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-green-700 uppercase tracking-wide">Confirmados</p>
                <div className="p-2 bg-green-500 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-white" />
                </div>
              </div>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold text-green-900">{appointmentStats.confirmed}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Pendentes */}
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200 hover:shadow-lg transition-shadow duration-200">
          <CardContent className="p-5">
            <div className="flex flex-col space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-yellow-700 uppercase tracking-wide">Pendentes</p>
                <div className="p-2 bg-yellow-500 rounded-lg">
                  <AlertCircle className="h-4 w-4 text-white" />
                </div>
              </div>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold text-yellow-900">{appointmentStats.pending}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Concluídos */}
        <Card className="bg-gradient-to-br from-indigo-50 to-indigo-100 border-indigo-200 hover:shadow-lg transition-shadow duration-200">
          <CardContent className="p-5">
            <div className="flex flex-col space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wide">Concluídos</p>
                <div className="p-2 bg-indigo-500 rounded-lg">
                  <CheckCircle className="h-4 w-4 text-white" />
                </div>
              </div>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold text-indigo-900">{appointmentStats.completed}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Cancelados */}
        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200 hover:shadow-lg transition-shadow duration-200">
          <CardContent className="p-5">
            <div className="flex flex-col space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold text-red-700 uppercase tracking-wide">Cancelados</p>
                <div className="p-2 bg-red-500 rounded-lg">
                  <XCircle className="h-4 w-4 text-white" />
                </div>
              </div>
              {loading ? (
                <Skeleton className="h-8 w-16" />
              ) : (
                <p className="text-3xl font-bold text-red-900">{appointmentStats.cancelled}</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs - Design Moderno */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
        <TabsList className="bg-white border border-gray-200 p-1.5 shadow-sm rounded-lg">
          <TabsTrigger 
            value="list" 
            className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-500 data-[state=active]:to-indigo-500 data-[state=active]:text-white data-[state=active]:shadow-md rounded-md transition-all duration-200"
          >
            📋 Lista Completa
          </TabsTrigger>
          <TabsTrigger 
            value="calendar" 
            className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-purple-500 data-[state=active]:to-pink-500 data-[state=active]:text-white data-[state=active]:shadow-md rounded-md transition-all duration-200"
          >
            📅 Calendário
          </TabsTrigger>
          <TabsTrigger 
            value="today" 
            className="data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-red-500 data-[state=active]:text-white data-[state=active]:shadow-md rounded-md transition-all duration-200"
          >
            🔥 Hoje
          </TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-6 mt-6">
          {/* Filters - Design Melhorado */}
          <Card className="shadow-md border-gray-200 bg-white">
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="h-5 w-5 absolute left-3 top-2.5 text-blue-400" />
                    <Input
                      placeholder="🔍 Buscar por cliente ou serviço..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-11 border-2 border-gray-200 focus:border-blue-400 focus:ring-2 focus:ring-blue-100 rounded-lg transition-all duration-200"
                    />
                  </div>
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-full sm:w-52 border-2 border-gray-200 focus:border-blue-400 rounded-lg">
                    <SelectValue placeholder="📊 Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os Status</SelectItem>
                    <SelectItem value="confirmado">✅ Confirmado</SelectItem>
                    <SelectItem value="agendado">📅 Agendado</SelectItem>
                    <SelectItem value="realizado">✔️ Realizado</SelectItem>
                    <SelectItem value="cancelado">❌ Cancelado</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={dateFilter} onValueChange={setDateFilter}>
                  <SelectTrigger className="w-full sm:w-52 border-2 border-gray-200 focus:border-blue-400 rounded-lg">
                    <SelectValue placeholder="📆 Período" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as Datas</SelectItem>
                    <SelectItem value="today">🔥 Hoje</SelectItem>
                    <SelectItem value="tomorrow">⏭️ Amanhã</SelectItem>
                    <SelectItem value="week">📅 Esta Semana</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Appointments List - Design Premium */}
          <Card className="shadow-lg border-gray-200 overflow-hidden">
            <CardHeader className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 border-b border-gray-200 py-5">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-3 text-2xl">
                  <div className="p-2 bg-white rounded-lg shadow-sm">
                    <Calendar className="h-6 w-6 text-blue-600" />
                  </div>
                  <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    Agendamentos
                  </span>
                  <Badge variant="secondary" className="text-sm px-3 py-1 bg-blue-100 text-blue-700 font-semibold">
                    {filteredAppointments.length} {filteredAppointments.length === 1 ? 'agendamento' : 'agendamentos'}
                  </Badge>
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-6 bg-gray-50">
              {loading ? (
                <div className="space-y-4">
                  {[1,2,3].map(i => (
                    <Skeleton key={i} className="h-28 w-full rounded-xl" />
                  ))}
                </div>
              ) : filteredAppointments.length === 0 ? (
                <div className="text-center py-16">
                  <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl inline-block mb-4">
                    <Calendar className="h-20 w-20 text-blue-300 mx-auto" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">Nenhum agendamento encontrado</h3>
                  <p className="text-gray-500 text-sm">Ajuste os filtros ou crie um novo agendamento</p>
                  <Button 
                    onClick={() => handleOpenAppointmentModal()}
                    className="mt-6 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600"
                  >
                    <CalendarPlus className="h-4 w-4 mr-2" />
                    Criar Primeiro Agendamento
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredAppointments.map((appointment) => {
                    // ✅ Fallback seguro para status desconhecidos
                    const StatusIcon = statusIcons[appointment.status] || Clock;
                    const isConfirmed = appointment.status === 'confirmado';
                    const isCancelled = appointment.status === 'cancelado' || appointment.status === 'cancelled';
                    const isScheduled = appointment.status === 'agendado' || appointment.status === 'scheduled';
                    
                    return (
                      <div
                        key={appointment.id}
                        className="group flex items-center justify-between p-6 bg-white border-2 border-gray-100 rounded-xl hover:border-blue-300 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1"
                      >
                        <div className="flex items-center space-x-5 flex-1">
                          {/* Icon com gradiente */}
                          <div className={`flex items-center justify-center w-14 h-14 rounded-xl shadow-lg ${
                            isConfirmed ? 'bg-gradient-to-br from-green-400 via-green-500 to-green-600' :
                            isScheduled ? 'bg-gradient-to-br from-yellow-400 via-yellow-500 to-amber-600' :
                            isCancelled ? 'bg-gradient-to-br from-red-400 via-red-500 to-red-600' :
                            'bg-gradient-to-br from-indigo-400 via-indigo-500 to-indigo-600'
                          }`}>
                            <StatusIcon className="h-7 w-7 text-white drop-shadow-md" />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            {/* Nome e Badge */}
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="font-bold text-gray-900 text-lg truncate">{appointment.customer_name}</h3>
                              <Badge className={`${statusColors[appointment.status] || 'bg-gray-100 text-gray-800'} font-semibold text-xs px-3 py-1 shadow-sm`}>
                                {statusLabels[appointment.status] || appointment.status}
                              </Badge>
                            </div>
                            
                            {/* Informações */}
                            <div className="flex flex-wrap items-center gap-4 text-sm">
                              <span className="flex items-center gap-2 text-gray-700 font-medium bg-blue-50 px-3 py-1.5 rounded-lg">
                                <Calendar className="h-4 w-4 text-blue-600" />
                                {appointment.data_agendamento ? formatDate(appointment.data_agendamento) : 'Data não informada'}
                              </span>
                              <span className="flex items-center gap-2 text-gray-700 font-medium bg-indigo-50 px-3 py-1.5 rounded-lg">
                                <Clock className="h-4 w-4 text-indigo-600" />
                                {appointment.hora_agendamento}
                              </span>
                              <span className="flex items-center gap-2 text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg">
                                <User className="h-4 w-4 text-gray-500" />
                                {appointment.service_name}
                              </span>
                            </div>
                            
                            {appointment.observacoes && (
                              <p className="text-xs text-gray-600 mt-3 italic bg-yellow-50 border-l-4 border-yellow-400 px-3 py-2 rounded-r-lg">
                                💬 {appointment.observacoes}
                              </p>
                            )}
                          </div>
                        </div>
                        
                        {/* Actions - aparecem no hover */}
                        <div className="flex items-center gap-2 ml-4 opacity-0 group-hover:opacity-100 transition-all duration-200 transform translate-x-2 group-hover:translate-x-0">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleOpenAppointmentModal(appointment)}
                            className="border-2 border-blue-300 text-blue-700 hover:bg-blue-50 hover:border-blue-500 shadow-sm font-medium"
                          >
                            <Edit className="h-4 w-4 mr-1.5" />
                            Editar
                          </Button>
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => handleOpenDeleteModal(appointment)}
                            className="border-2 border-red-300 text-red-700 hover:bg-red-50 hover:border-red-500 shadow-sm font-medium"
                          >
                            <Trash2 className="h-4 w-4 mr-1.5" />
                            Excluir
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="today" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Agendamentos de Hoje</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {appointments
                  .filter(appointment => {
                    if (!appointment.data_agendamento) return false;
                    const today = new Date().toDateString();
                    return new Date(appointment.data_agendamento).toDateString() === today;
                  })
                  .sort((a, b) => {
                    if (!a.data_agendamento || !b.data_agendamento) return 0;
                    return new Date(a.data_agendamento).getTime() - new Date(b.data_agendamento).getTime();
                  })
                  .map((appointment) => {
                    const StatusIcon = statusIcons[appointment.status];
                    return (
                      <div
                        key={appointment.id}
                        className="flex items-center space-x-4 p-4 border rounded-lg"
                      >
                        <div className="flex items-center justify-center w-12 h-12 rounded-full bg-blue-100">
                          <StatusIcon className={`h-6 w-6 ${
                            appointment.status === 'confirmado' ? 'text-green-600' :
                            appointment.status === 'agendado' ? 'text-yellow-600' :
                            appointment.status === 'cancelado' ? 'text-red-600' :
                            'text-blue-600'
                          }`} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h3 className="font-medium text-gray-900">{appointment.customer_name}</h3>
                            <span className="text-lg font-semibold text-blue-600">
                              {appointment.hora_agendamento}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{appointment.service_name}</p>
                        </div>
                        <Badge className={statusColors[appointment.status] || 'bg-gray-100 text-gray-800'}>
                          {statusLabels[appointment.status] || appointment.status}
                        </Badge>
                      </div>
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="calendar" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Visão do Calendário</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Object.entries(groupAppointmentsByDate(filteredAppointments)).map(([date, dateAppointments]) => (
                  <div key={date}>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">{date}</h3>
                    <div className="space-y-2">
                      {dateAppointments
                        .sort((a, b) => {
                          if (!a.data_agendamento || !b.data_agendamento) return 0;
                          return new Date(a.data_agendamento).getTime() - new Date(b.data_agendamento).getTime();
                        })
                        .map((appointment) => (
                          <div
                            key={appointment.id}
                            className="flex items-center justify-between p-3 border-l-4 border-blue-500 bg-blue-50 rounded-r-lg"
                          >
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="font-medium">{appointment.hora_agendamento}</span>
                                <span>-</span>
                                <span className="font-medium">{appointment.customer_name}</span>
                                <Badge className={statusColors[appointment.status] || 'bg-gray-100 text-gray-800'}>
                                  {statusLabels[appointment.status] || appointment.status}
                                </Badge>
                              </div>
                              <p className="text-sm text-gray-600">{appointment.service_name}</p>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modais - Apenas renderizar quando aberto */}
      {isAppointmentModalOpen && (
        <AppointmentModal
          key={selectedAppointment?.id || 'new-appointment'}
          isOpen={isAppointmentModalOpen}
          onClose={handleCloseAppointmentModal}
          onSuccess={handleAppointmentSuccess}
          appointment={selectedAppointment || undefined}
          clients={clients}
          services={services}
        />
      )}

      {isDeleteModalOpen && (
        <DeleteConfirmationModal
          key={`delete-${selectedAppointment?.id}`}
          isOpen={isDeleteModalOpen}
          onClose={handleCloseDeleteModal}
          onConfirm={handleDeleteAppointment}
          appointment={selectedAppointment || undefined}
          isLoading={isDeleting}
        />
      )}
    </div>
  );
}
