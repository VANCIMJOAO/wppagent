'use client';

import { useState, useEffect } from 'react';
import { useConversationEndpoints } from '@/lib/use-conversation-endpoints';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MessageSquare, Phone, Clock, Users, BarChart3, Zap } from 'lucide-react';

interface Conversation {
  id: number | string;
  user_id?: number;
  user_name?: string;
  phone_number?: string;
  user_phone?: string;
  status?: string;
  last_message_at?: string;
  created_at?: string;
  message_count?: number;
  total_messages?: number;
  type?: string;
  // Campos de estatísticas
  total_conversations?: number;
  active_conversations?: number;
  generated_at?: string;
}

export default function ConversasPage() {
  const { fetchConversations, loading, error, hasWorkingEndpoint, reconnect } = useConversationEndpoints();
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const loadConversations = async () => {
    try {
      console.log('🔍 Carregando conversas...');
      const data = await fetchConversations();
      
      if (data && Array.isArray(data)) {
        console.log(`✅ Conversas carregadas: ${data.length}`);
        setConversations(data);
        
        // Log para debug
        if (data.length > 0) {
          console.log('📊 Primeira conversa:', data[0]);
          if (data[0].type === 'statistics') {
            console.log('ℹ️ Dados estatísticos recebidos ao invés de conversas individuais');
          } else {
            console.log('✅ Conversas individuais recebidas');
          }
        }
      } else {
        console.log('⚠️ Nenhum dado de conversa recebido');
        setConversations([]);
      }
    } catch (err) {
      console.error('❌ Erro ao carregar conversas:', err);
      setConversations([]);
    }
  };

  useEffect(() => {
    if (hasWorkingEndpoint) {
      loadConversations();
    }
  }, [hasWorkingEndpoint]);

  const formatTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString('pt-BR');
    } catch {
      return 'Data inválida';
    }
  };

  const getStatusBadge = (status?: string) => {
    const statusColors: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      closed: 'bg-gray-100 text-gray-800',
    };
    
    return (
      <Badge className={statusColors[status || 'closed'] || statusColors.closed}>
        {status || 'unknown'}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando conversas...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <MessageSquare className="h-12 w-12 mx-auto mb-2" />
            <p className="font-semibold">Erro ao carregar conversas</p>
            <p className="text-sm text-gray-600 mt-1">{error}</p>
          </div>
          <Button onClick={reconnect} variant="outline">
            <Zap className="h-4 w-4 mr-2" />
            Tentar novamente
          </Button>
        </div>
      </div>
    );
  }

  if (!hasWorkingEndpoint) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-orange-500 mb-4">
            <MessageSquare className="h-12 w-12 mx-auto mb-2" />
            <p className="font-semibold">Nenhum endpoint disponível</p>
            <p className="text-sm text-gray-600 mt-1">Verifique a conexão com o backend</p>
          </div>
          <Button onClick={reconnect} variant="outline">
            <Zap className="h-4 w-4 mr-2" />
            Reconectar
          </Button>
        </div>
      </div>
    );
  }

  // Se temos apenas dados estatísticos, mostrar um painel informativo
  if (conversations.length === 1 && conversations[0].type === 'statistics') {
    const stats = conversations[0];
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Conversas</h1>
            <p className="text-gray-600">Estatísticas do sistema</p>
          </div>
          <Button onClick={loadConversations} variant="outline">
            <Zap className="h-4 w-4 mr-2" />
            Atualizar
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total de Conversas</CardTitle>
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_conversations}</div>
              <p className="text-xs text-muted-foreground">Conversas no sistema</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Conversas Ativas</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_conversations}</div>
              <p className="text-xs text-muted-foreference">Ativas no momento</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total de Mensagens</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_messages}</div>
              <p className="text-xs text-muted-foreground">Mensagens enviadas</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>⚠️ Lista de Conversas Indisponível</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-600 mb-4">
              Não foi possível carregar a lista individual de conversas. 
              Dados estatísticos do banco PostgreSQL foram carregados com sucesso.
            </p>
            <p className="text-sm text-gray-500">
              Última atualização: {formatTime(stats.generated_at)}
            </p>
            <div className="mt-4">
              <Button onClick={() => window.location.reload()} variant="outline">
                <Zap className="h-4 w-4 mr-2" />
                Recarregar página
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Mostrar lista de conversas individuais (formato WhatsApp)
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Conversas</h1>
          <p className="text-gray-600">{conversations.length} conversas encontradas</p>
        </div>
        <Button onClick={loadConversations} variant="outline">
          <Zap className="h-4 w-4 mr-2" />
          Atualizar
        </Button>
      </div>

      <div className="space-y-4">
        {conversations.map((conversation) => (
          <Card key={conversation.id} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center space-x-4">
                {/* Avatar/Icone */}
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <Phone className="h-6 w-6 text-blue-600" />
                  </div>
                </div>

                {/* Informações principais */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-medium text-gray-900 truncate">
                      {conversation.user_name || `Usuário ${conversation.user_id}` || 'Usuário Desconhecido'}
                    </h3>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(conversation.status)}
                      <span className="text-xs text-gray-500">
                        {formatTime(conversation.last_message_at)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center mt-1">
                    <Phone className="h-3 w-3 text-gray-400 mr-1" />
                    <span className="text-sm text-gray-500">
                      {conversation.phone_number || conversation.user_phone || 'Telefone não disponível'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center">
                      <MessageSquare className="h-3 w-3 text-gray-400 mr-1" />
                      <span className="text-xs text-gray-500">
                        {conversation.message_count || conversation.total_messages || 0} mensagens
                      </span>
                    </div>
                    <div className="flex items-center">
                      <Clock className="h-3 w-3 text-gray-400 mr-1" />
                      <span className="text-xs text-gray-500">
                        Criada em {formatTime(conversation.created_at)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {conversations.length === 0 && (
        <div className="text-center py-12">
          <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhuma conversa encontrada</h3>
          <p className="text-gray-600 mb-4">Não há conversas disponíveis no momento.</p>
          <Button onClick={loadConversations} variant="outline">
            <Zap className="h-4 w-4 mr-2" />
            Carregar conversas
          </Button>
        </div>
      )}
    </div>
  );
}
