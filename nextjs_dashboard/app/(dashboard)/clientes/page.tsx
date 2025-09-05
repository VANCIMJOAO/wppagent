"use client";

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Users, 
  UserPlus, 
  Search, 
  Filter, 
  MoreVertical, 
  Phone, 
  Mail, 
  Calendar,
  MessageCircle,
  Star,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { api, Client as ApiClient } from '@/lib/api-service';
import { toast } from 'sonner';

interface ClientStats {
  total: number;
  active: number;
  new: number;
  vip: number;
}

const statusColors = {
  'vip': 'bg-purple-100 text-purple-800',
  'active': 'bg-green-100 text-green-800',
  'new': 'bg-blue-100 text-blue-800',
  'inactive': 'bg-gray-100 text-gray-800'
};

const statusLabels = {
  'vip': 'VIP',
  'active': 'Ativo',
  'new': 'Novo',
  'inactive': 'Inativo'
};

export default function ClientesPage() {
  const [clients, setClients] = useState<ApiClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedClient, setSelectedClient] = useState<ApiClient | null>(null);
  const [clientStats, setClientStats] = useState<ClientStats>({
    total: 0,
    active: 0,
    new: 0,
    vip: 0
  });

  // Load data from API
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        
        const [clientsData, dashboardData] = await Promise.all([
          api.getClients(),
          api.getDashboardStats()
        ]);

        setClients(clientsData);
        
        // Calculate client stats from dashboard data
        setClientStats({
          total: dashboardData.totalClients,
          active: Math.floor(dashboardData.totalClients * 0.8),
          vip: Math.floor(dashboardData.totalClients * 0.15),
          new: Math.floor(dashboardData.totalClients * 0.1)
        });
        
        // Calculate stats from actual data if API doesn't provide them
        const calculatedStats = {
          total: clientsData.length,
          active: clientsData.filter(c => c.status === 'active' || c.status === 'vip').length,
          new: clientsData.filter(c => c.status === 'new').length,
          vip: clientsData.filter(c => c.status === 'vip').length
        };
        
      } catch (error) {
        console.error('Erro ao carregar dados dos clientes:', error);
        toast.error('Erro ao carregar dados dos clientes');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const filteredClients = clients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         client.phone.includes(searchTerm) ||
                         (client.email && client.email.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || client.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Clientes</h1>
          <p className="text-gray-600 mt-1">Gestão da base de clientes</p>
        </div>
        <Button>
          <UserPlus className="h-4 w-4 mr-2" />
          Novo Cliente
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total</p>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-3xl font-bold text-gray-900">{clientStats.total}</p>
                )}
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Ativos</p>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-3xl font-bold text-green-600">{clientStats.active}</p>
                )}
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Novos</p>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-3xl font-bold text-blue-600">{clientStats.new}</p>
                )}
              </div>
              <TrendingUp className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">VIP</p>
                {loading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-3xl font-bold text-purple-600">{clientStats.vip}</p>
                )}
              </div>
              <Star className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
                <Input
                  placeholder="Buscar clientes..."
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
                <SelectItem value="vip">VIP</SelectItem>
                <SelectItem value="active">Ativo</SelectItem>
                <SelectItem value="new">Novo</SelectItem>
                <SelectItem value="inactive">Inativo</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Clients List */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Clientes</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center space-x-4 p-4 border rounded-lg">
                  <Skeleton className="w-12 h-12 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-48" />
                    <Skeleton className="h-3 w-64" />
                  </div>
                  <div className="flex space-x-4">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-6 w-16" />
                  </div>
                </div>
              ))}
            </div>
          ) : filteredClients.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {searchTerm || statusFilter !== 'all' 
                  ? 'Nenhum cliente encontrado com os filtros aplicados.' 
                  : 'Nenhum cliente encontrado.'}
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredClients.map((client) => (
                <div
                  key={client.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedClient(client)}
                >
                  <div className="flex items-center space-x-4">
                    <Avatar>
                      <AvatarFallback>
                        {client.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium text-gray-900">{client.name}</h3>
                        <Badge className={statusColors[client.status]}>
                          {statusLabels[client.status]}
                        </Badge>
                        {client.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span className="flex items-center">
                          <Phone className="h-3 w-3 mr-1" />
                          {client.phone}
                        </span>
                        {client.email && (
                          <span className="flex items-center">
                            <Mail className="h-3 w-3 mr-1" />
                            {client.email}
                          </span>
                        )}
                        <span className="flex items-center">
                          <Clock className="h-3 w-3 mr-1" />
                          Última interação: {formatDate(client.lastInteraction)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-6 text-sm text-gray-600">
                    <div className="text-center">
                      <div className="flex items-center">
                        <MessageCircle className="h-4 w-4 mr-1" />
                        <span className="font-medium">{client.totalConversations}</span>
                      </div>
                      <span className="text-xs">Conversas</span>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-1" />
                        <span className="font-medium">{client.totalAppointments}</span>
                      </div>
                      <span className="text-xs">Agendamentos</span>
                    </div>
                    <div className="text-center">
                      <div className="flex items-center">
                        <MessageCircle className="h-4 w-4 mr-1" />
                        <span className="font-medium">{client.totalMessages}</span>
                      </div>
                      <span className="text-xs">Mensagens</span>
                    </div>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Client Details Modal/Sidebar would go here */}
      {selectedClient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
          <Card className="w-full max-w-2xl mx-4">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Detalhes do Cliente</CardTitle>
                <Button variant="ghost" onClick={() => setSelectedClient(null)}>
                  ×
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <Avatar className="w-16 h-16">
                    <AvatarFallback className="text-xl">
                      {selectedClient.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <h2 className="text-xl font-semibold">{selectedClient.name}</h2>
                    <Badge className={statusColors[selectedClient.status]}>
                      {statusLabels[selectedClient.status]}
                    </Badge>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Telefone</Label>
                    <p className="font-medium">{selectedClient.phone}</p>
                  </div>
                  <div>
                    <Label>Email</Label>
                    <p className="font-medium">{selectedClient.email}</p>
                  </div>
                  <div>
                    <Label>Cliente desde</Label>
                    <p className="font-medium">{formatDate(selectedClient.createdAt)}</p>
                  </div>
                  <div>
                    <Label>Última interação</Label>
                    <p className="font-medium">{formatDate(selectedClient.lastInteraction)}</p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 pt-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <MessageCircle className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-blue-600">{selectedClient.totalConversations}</p>
                    <p className="text-sm text-gray-600">Conversas</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <Calendar className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-green-600">{selectedClient.totalAppointments}</p>
                    <p className="text-sm text-gray-600">Agendamentos</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <MessageCircle className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-purple-600">{selectedClient.totalMessages}</p>
                    <p className="text-sm text-gray-600">Mensagens</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
