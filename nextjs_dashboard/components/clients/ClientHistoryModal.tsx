"use client";

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  MessageCircle,
  Calendar,
  Clock,
  User,
  Phone,
  Mail,
  TrendingUp,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  History
} from 'lucide-react';
import type { Client } from '@/types/api';
import { toast } from 'sonner';
import { debugLog } from '@/lib/debug';

interface ClientHistory {
  client: Client;
  conversations: Array<{
    id: number;
    status: string;
    created_at: string;
    updated_at: string;
    first_response_at?: string;
    messages_count: number;
    messages: Array<{
      id: number;
      content: string;
      direction: string;
      created_at: string;
    }>;
  }>;
  appointments: Array<{
    id: number;
    service_name: string;
    date_time: string;
    status: string;
    notes?: string;
  }>;
  timeline: Array<{
    event: string;
    description: string;
    timestamp: string;
  }>;
  stats: {
    total_conversations: number;
    total_messages: number;
    total_appointments: number;
    active_conversations_last_7_days: number;
    first_conversation_date?: string;
    last_conversation_date?: string;
  };
}

interface ClientHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  client: Client | null;
}

export default function ClientHistoryModal({ isOpen, onClose, client }: ClientHistoryModalProps) {
  const [history, setHistory] = useState<ClientHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'conversations' | 'appointments' | 'timeline'>('overview');

  useEffect(() => {
    if (isOpen && client) {
      loadClientHistory();
    }
  }, [isOpen, client]);

  const loadClientHistory = async () => {
    if (!client) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/clients/${client.id}/history`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.data) {
        setHistory(data.data);
        debugLog.success(`Histórico carregado para cliente ${client.full_name}`);
      } else {
        throw new Error(data.message || 'Erro ao carregar histórico');
      }
    } catch (error) {
      debugLog.error('Erro ao carregar histórico do cliente:', error);
      toast.error('Erro ao carregar histórico do cliente');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active':
      case 'completed':
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
      case 'scheduled':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
      case 'inactive':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (!client) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <History className="h-6 w-6 text-blue-600" />
            <span>Histórico do Cliente</span>
            <Badge variant="outline" className="ml-auto">
              ID: {client.id}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        {/* Header do Cliente */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xl">
              {client.full_name?.charAt(0)?.toUpperCase() || 'C'}
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900">{client.full_name}</h3>
              <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                <div className="flex items-center gap-1">
                  <Phone className="h-4 w-4" />
                  {client.phone}
                </div>
                {client.email && (
                  <div className="flex items-center gap-1">
                    <Mail className="h-4 w-4" />
                    {client.email}
                  </div>
                )}
              </div>
            </div>
            <Badge className={getStatusColor(client.status || 'active')}>
              {client.status || 'Ativo'}
            </Badge>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b">
          {[
            { id: 'overview', label: 'Visão Geral', icon: TrendingUp },
            { id: 'conversations', label: 'Conversas', icon: MessageCircle },
            { id: 'appointments', label: 'Agendamentos', icon: Calendar },
            { id: 'timeline', label: 'Timeline', icon: Activity }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 ${
                  activeTab === tab.id 
                    ? 'bg-blue-600 text-white' 
                    : 'hover:bg-blue-50'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </Button>
            );
          })}
        </div>

        {/* Conteúdo */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : !history ? (
            <div className="text-center py-8 text-gray-500">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>Não foi possível carregar o histórico</p>
            </div>
          ) : (
            <>
              {/* Visão Geral */}
              {activeTab === 'overview' && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <MessageCircle className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Conversas</p>
                          <p className="text-2xl font-bold">{history.stats.total_conversations}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                          <Activity className="h-5 w-5 text-green-600" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Mensagens</p>
                          <p className="text-2xl font-bold">{history.stats.total_messages}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                          <Calendar className="h-5 w-5 text-purple-600" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Agendamentos</p>
                          <p className="text-2xl font-bold">{history.stats.total_appointments}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                          <TrendingUp className="h-5 w-5 text-orange-600" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Últimos 7 dias</p>
                          <p className="text-2xl font-bold">{history.stats.active_conversations_last_7_days}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Conversas */}
              {activeTab === 'conversations' && (
                <div className="space-y-4">
                  {history.conversations.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                      <p>Nenhuma conversa encontrada</p>
                    </div>
                  ) : (
                    history.conversations.map((conversation) => (
                      <Card key={conversation.id}>
                        <CardHeader className="pb-3">
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-lg">Conversa #{conversation.id}</CardTitle>
                            <Badge className={getStatusColor(conversation.status)}>
                              {conversation.status}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-gray-600">Criada em:</p>
                              <p className="font-medium">{formatDate(conversation.created_at)}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Última atualização:</p>
                              <p className="font-medium">{formatDate(conversation.updated_at)}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Primeira resposta:</p>
                              <p className="font-medium">
                                {conversation.first_response_at 
                                  ? formatDate(conversation.first_response_at)
                                  : 'Não respondida'
                                }
                              </p>
                            </div>
                            <div>
                              <p className="text-gray-600">Total de mensagens:</p>
                              <p className="font-medium">{conversation.messages_count}</p>
                            </div>
                          </div>
                          
                          {conversation.messages.length > 0 && (
                            <div className="mt-4">
                              <h4 className="font-medium mb-2">Últimas mensagens:</h4>
                              <div className="space-y-2 max-h-32 overflow-y-auto">
                                {conversation.messages.slice(-3).map((message) => (
                                  <div 
                                    key={message.id}
                                    className={`p-2 rounded text-sm ${
                                      message.direction === 'in' 
                                        ? 'bg-blue-50 border-l-2 border-blue-200' 
                                        : 'bg-gray-50 border-l-2 border-gray-200'
                                    }`}
                                  >
                                    <div className="flex justify-between items-start">
                                      <p className="flex-1">{message.content}</p>
                                      <span className="text-xs text-gray-500 ml-2">
                                        {formatDate(message.created_at)}
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              )}

              {/* Agendamentos */}
              {activeTab === 'appointments' && (
                <div className="space-y-4">
                  {history.appointments.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                      <p>Nenhum agendamento encontrado</p>
                    </div>
                  ) : (
                    history.appointments.map((appointment) => (
                      <Card key={appointment.id}>
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between mb-3">
                            <h3 className="font-semibold text-lg">{appointment.service_name}</h3>
                            <Badge className={getStatusColor(appointment.status)}>
                              {appointment.status}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4 text-gray-500" />
                              <span>{formatDate(appointment.date_time)}</span>
                            </div>
                            {appointment.notes && (
                              <div>
                                <p className="text-gray-600">Observações:</p>
                                <p className="font-medium">{appointment.notes}</p>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              )}

              {/* Timeline */}
              {activeTab === 'timeline' && (
                <div className="space-y-4">
                  {history.timeline.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Activity className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                      <p>Nenhum evento encontrado</p>
                    </div>
                  ) : (
                    <div className="relative">
                      {/* Linha vertical */}
                      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200"></div>
                      
                      {history.timeline.map((event, index) => (
                        <div key={index} className="relative flex items-start gap-4 pb-6">
                          {/* Ícone do evento */}
                          <div className="relative z-10 w-12 h-12 bg-white border-2 border-blue-200 rounded-full flex items-center justify-center">
                            {event.event.includes('Created') && <User className="h-5 w-5 text-blue-600" />}
                            {event.event.includes('Login') && <CheckCircle className="h-5 w-5 text-green-600" />}
                            {event.event.includes('Conversation') && <MessageCircle className="h-5 w-5 text-purple-600" />}
                            {event.event.includes('Appointment') && <Calendar className="h-5 w-5 text-orange-600" />}
                          </div>
                          
                          {/* Conteúdo do evento */}
                          <div className="flex-1 bg-white p-4 rounded-lg border shadow-sm">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="font-semibold text-gray-900">{event.event}</h3>
                              <span className="text-sm text-gray-500">{formatDate(event.timestamp)}</span>
                            </div>
                            <p className="text-gray-600">{event.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t">
          <Button onClick={onClose} variant="outline">
            Fechar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
