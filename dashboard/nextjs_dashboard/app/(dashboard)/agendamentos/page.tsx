"use client";

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
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
  Loader2
} from 'lucide-react';
import { api, Appointment as ApiAppointment } from '@/lib/api-service';
import { toast } from 'sonner';

interface AppointmentStats {
  total: number;
  confirmed: number;
  pending: number;
  cancelled: number;
  completed: number;
  today: number;
}

const statusColors = {
  'confirmed': 'bg-green-100 text-green-800',
  'pending': 'bg-yellow-100 text-yellow-800',
  'cancelled': 'bg-red-100 text-red-800',
  'completed': 'bg-blue-100 text-blue-800'
};

const statusLabels = {
  'confirmed': 'Confirmado',
  'pending': 'Pendente',
  'cancelled': 'Cancelado',
  'completed': 'Concluído'
};

const statusIcons = {
  'confirmed': CheckCircle,
  'pending': AlertCircle,
  'cancelled': XCircle,
  'completed': CheckCircle
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
    today: 0
  });

  // Load data from API
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        
        const [appointmentsData, dashboardData] = await Promise.all([
          api.getAppointments(),
          api.getDashboardStats()
        ]);

        setAppointments(appointmentsData);
        
        // Convert dashboard stats to appointment stats
        setAppointmentStats({
          total: dashboardData.totalAppointments,
          today: Math.floor(dashboardData.totalAppointments * 0.1),
          confirmed: dashboardData.confirmedAppointments,
          pending: dashboardData.pendingAppointments,
          completed: Math.floor(dashboardData.totalAppointments * 0.6),
          cancelled: dashboardData.cancelledAppointments
        });
        const today = new Date().toDateString();
        const calculatedStats = {
          total: appointmentsData.length,
          confirmed: appointmentsData.filter(a => a.status === 'confirmed').length,
          pending: appointmentsData.filter(a => a.status === 'pending').length,
          cancelled: appointmentsData.filter(a => a.status === 'cancelled').length,
          completed: appointmentsData.filter(a => a.status === 'completed').length,
          today: appointmentsData.filter(a => 
            new Date(a.dateTime).toDateString() === today
          ).length
        };
        
      } catch (error) {
        console.error('Erro ao carregar dados dos agendamentos:', error);
        toast.error('Erro ao carregar dados dos agendamentos');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const filteredAppointments = appointments.filter(appointment => {
    const matchesSearch = appointment.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         appointment.phone.includes(searchTerm) ||
                         appointment.serviceType.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || appointment.status === statusFilter;
    
    let matchesDate = true;
    if (dateFilter === 'today') {
      const today = new Date().toDateString();
      matchesDate = new Date(appointment.dateTime).toDateString() === today;
    } else if (dateFilter === 'tomorrow') {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      matchesDate = new Date(appointment.dateTime).toDateString() === tomorrow.toDateString();
    } else if (dateFilter === 'week') {
      const weekFromNow = new Date();
      weekFromNow.setDate(weekFromNow.getDate() + 7);
      matchesDate = new Date(appointment.dateTime) <= weekFromNow;
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
      const date = formatDate(appointment.dateTime);
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(appointment);
    });
    return grouped;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agendamentos</h1>
          <p className="text-gray-600 mt-1">Gestão de agenda e compromissos</p>
        </div>
        <Button>
          <CalendarPlus className="h-4 w-4 mr-2" />
          Novo Agendamento
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-gray-900">{appointmentStats.total}</p>
                )}
              </div>
              <Calendar className="h-6 w-6 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Hoje</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-orange-600">{appointmentStats.today}</p>
                )}
              </div>
              <Clock className="h-6 w-6 text-orange-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Confirmados</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-green-600">{appointmentStats.confirmed}</p>
                )}
              </div>
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pendentes</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-yellow-600">{appointmentStats.pending}</p>
                )}
              </div>
              <AlertCircle className="h-6 w-6 text-yellow-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Concluídos</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-blue-600">{appointmentStats.completed}</p>
                )}
              </div>
              <CheckCircle className="h-6 w-6 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Cancelados</p>
                {loading ? (
                  <Skeleton className="h-6 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-red-600">{appointmentStats.cancelled}</p>
                )}
              </div>
              <XCircle className="h-6 w-6 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="list">Lista</TabsTrigger>
          <TabsTrigger value="calendar">Calendário</TabsTrigger>
          <TabsTrigger value="today">Hoje</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-6">
          {/* Filters */}
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                    <Input
                      placeholder="Buscar agendamentos..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos os Status</SelectItem>
                    <SelectItem value="confirmed">Confirmado</SelectItem>
                    <SelectItem value="pending">Pendente</SelectItem>
                    <SelectItem value="completed">Concluído</SelectItem>
                    <SelectItem value="cancelled">Cancelado</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={dateFilter} onValueChange={setDateFilter}>
                  <SelectTrigger className="w-48">
                    <SelectValue placeholder="Data" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas as Datas</SelectItem>
                    <SelectItem value="today">Hoje</SelectItem>
                    <SelectItem value="tomorrow">Amanhã</SelectItem>
                    <SelectItem value="week">Esta Semana</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Appointments List */}
          <Card>
            <CardHeader>
              <CardTitle>Agendamentos</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredAppointments.map((appointment) => {
                  const StatusIcon = statusIcons[appointment.status];
                  return (
                    <div
                      key={appointment.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-blue-100">
                          <StatusIcon className={`h-5 w-5 ${
                            appointment.status === 'confirmed' ? 'text-green-600' :
                            appointment.status === 'pending' ? 'text-yellow-600' :
                            appointment.status === 'cancelled' ? 'text-red-600' :
                            'text-blue-600'
                          }`} />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="font-medium text-gray-900">{appointment.customerName}</h3>
                            <Badge className={statusColors[appointment.status]}>
                              {statusLabels[appointment.status]}
                            </Badge>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                            <span className="flex items-center">
                              <Calendar className="h-3 w-3 mr-1" />
                              {formatDate(appointment.dateTime)} às {formatTime(appointment.dateTime)}
                            </span>
                            <span className="flex items-center">
                              <Phone className="h-3 w-3 mr-1" />
                              {appointment.phone}
                            </span>
                            <span className="flex items-center">
                              <Clock className="h-3 w-3 mr-1" />
                              {appointment.duration}min
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">{appointment.serviceType}</p>
                          {appointment.notes && (
                            <p className="text-xs text-gray-500 mt-1">{appointment.notes}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {appointment.price && (
                          <span className="text-lg font-semibold text-green-600">
                            R$ {appointment.price.toFixed(2)}
                          </span>
                        )}
                        <div className="flex space-x-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
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
                    const today = new Date().toDateString();
                    return new Date(appointment.dateTime).toDateString() === today;
                  })
                  .sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
                  .map((appointment) => {
                    const StatusIcon = statusIcons[appointment.status];
                    return (
                      <div
                        key={appointment.id}
                        className="flex items-center space-x-4 p-4 border rounded-lg"
                      >
                        <div className="flex items-center justify-center w-12 h-12 rounded-full bg-blue-100">
                          <StatusIcon className={`h-6 w-6 ${
                            appointment.status === 'confirmed' ? 'text-green-600' :
                            appointment.status === 'pending' ? 'text-yellow-600' :
                            appointment.status === 'cancelled' ? 'text-red-600' :
                            'text-blue-600'
                          }`} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h3 className="font-medium text-gray-900">{appointment.customerName}</h3>
                            <span className="text-lg font-semibold text-blue-600">
                              {formatTime(appointment.dateTime)}
                            </span>
                          </div>
                          <p className="text-sm text-gray-600">{appointment.serviceType}</p>
                          <p className="text-xs text-gray-500">{appointment.phone}</p>
                        </div>
                        <Badge className={statusColors[appointment.status]}>
                          {statusLabels[appointment.status]}
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
                        .sort((a, b) => new Date(a.dateTime).getTime() - new Date(b.dateTime).getTime())
                        .map((appointment) => (
                          <div
                            key={appointment.id}
                            className="flex items-center justify-between p-3 border-l-4 border-blue-500 bg-blue-50 rounded-r-lg"
                          >
                            <div>
                              <div className="flex items-center space-x-2">
                                <span className="font-medium">{formatTime(appointment.dateTime)}</span>
                                <span>-</span>
                                <span className="font-medium">{appointment.customerName}</span>
                                <Badge className={statusColors[appointment.status]}>
                                  {statusLabels[appointment.status]}
                                </Badge>
                              </div>
                              <p className="text-sm text-gray-600">{appointment.serviceType}</p>
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
    </div>
  );
}
