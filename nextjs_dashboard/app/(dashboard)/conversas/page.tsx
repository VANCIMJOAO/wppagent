"use client";

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { debugLog } from '@/lib/debug';
import {
  MessageCircle,
  Search,
  Phone,
  Clock,
  CheckCircle,
  AlertCircle,
  MoreVertical,
  Send,
  Paperclip,
  Smile,
  RefreshCw,
  Loader2
} from 'lucide-react';
import { useConversations, useMessages, useSendMessage } from '@/hooks/useConversations';
import type { Conversation, Message } from '@/types/api';

export default function ConversasPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [newMessage, setNewMessage] = useState('');

  // ✅ Hook para buscar conversas reais com React Query
  const {
    data: conversationsData,
    isLoading: conversationsLoading,
    error: conversationsError,
    refetch: refreshConversations,
  } = useConversations();

  // Extrair dados do React Query
  const conversations = conversationsData?.conversations || [];
  const total = conversationsData?.total || 0;

  // Verificar se é erro de autenticação
  const isAuthError = conversationsError?.message?.includes('Sessão expirada') || 
                     conversationsError?.message?.includes('Token de autenticação');

  // ✅ Hook para buscar mensagens reais com React Query
  const {
    data: messagesData,
    isLoading: messagesLoading,
    error: messagesError,
  } = useMessages(
    selectedConversationId || 0, 
    {}, 
    !!selectedConversationId
  );

  const messages = messagesData?.messages || [];

  // ✅ Hook para enviar mensagem com React Query
  const sendMessageMutation = useSendMessage();

  // Ref para scroll automático
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll quando mensagens mudarem
  useEffect(() => {
    if (messages.length > 0 && !messagesLoading) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [messages, messagesLoading]);

  // Filtrar conversas por termo de busca
  const filteredConversations = conversations.filter(conv => {
    const nome = conv.user_name || '';
    const phone = conv.user_phone || '';
    
    return nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
           phone.includes(searchTerm);
  });

  const selectedConversation = conversations.find(
    conv => conv.id === selectedConversationId
  );

  const handleSelectConversation = (conversation: Conversation) => {
    setSelectedConversationId(conversation.id);
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedConversationId) return;

    try {
      await sendMessageMutation.mutateAsync({
        conversationId: selectedConversationId,
        data: { content: newMessage }
      });
      setNewMessage('');
    } catch (error) {
      debugLog.error('Erro ao enviar mensagem:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <div className="w-2 h-2 bg-green-500 rounded-full" />;
      case 'human':
        return <div className="w-2 h-2 bg-blue-500 rounded-full" />;
      case 'closed':
        return <div className="w-2 h-2 bg-gray-400 rounded-full" />;
      default:
        return <div className="w-2 h-2 bg-gray-400 rounded-full" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Ativa';
      case 'human':
        return 'Atendimento Humano';
      case 'closed':
        return 'Fechada';
      default:
        return 'Desconhecido';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('pt-BR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatFullDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar com lista de conversas */}
      <div className="w-1/3 border-r bg-white flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Conversas</h1>
              <p className="text-gray-600 mt-1">
                {total > 0 ? `${total} conversas encontradas` : 'Gerencie suas conversas do WhatsApp'}
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => refreshConversations()}
              disabled={conversationsLoading}
            >
              {conversationsLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Barra de pesquisa */}
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-3 text-gray-400" />
            <Input
              placeholder="Buscar conversas..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Lista de conversas */}
        <div className="flex-1 overflow-y-auto">
          {conversationsError && (
            <div className="p-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  {isAuthError ? (
                    <div>
                      <p className="font-semibold">Sessão expirada</p>
                      <p>Faça login novamente para acessar as conversas.</p>
                      <Button 
                        onClick={() => window.location.href = '/login'} 
                        className="mt-2"
                        size="sm"
                      >
                        Ir para Login
                      </Button>
                    </div>
                  ) : (
                    `Erro ao carregar conversas: ${conversationsError}`
                  )}
                </AlertDescription>
              </Alert>
            </div>
          )}
          
          {conversationsLoading ? (
            <div className="p-4 space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center space-x-3 p-3">
                  <Skeleton className="h-12 w-12 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="p-4 text-center">
              <MessageCircle className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {searchTerm ? 'Nenhuma conversa encontrada' : 'Nenhuma conversa disponível'}
              </h3>
              <p className="text-gray-500">
                {searchTerm ? 'Tente ajustar os termos de busca' : 'As conversas aparecerão aqui quando houver atividade'}
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredConversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => handleSelectConversation(conversation)}
                  className={`p-4 cursor-pointer hover:bg-gray-50 border-l-4 ${
                    selectedConversationId === conversation.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-transparent'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                        <MessageCircle className="h-6 w-6 text-blue-600" />
                      </div>
                      <div className="absolute -bottom-1 -right-1">
                        {getStatusIcon(conversation.status)}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-gray-900 truncate">
                          {conversation.user_name || 'Usuário sem nome'}
                        </h3>
                        <span className="text-xs text-gray-500">
                          {conversation.last_message_at ? formatDate(conversation.last_message_at) : '--:--'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <p className="text-sm text-gray-600 truncate">
                          {conversation.last_message || 'Sem mensagens'}
                        </p>
                        {conversation.total_messages > 0 && (
                          <Badge variant="secondary" className="text-xs">
                            {conversation.total_messages}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center space-x-2 mt-1">
                        <Phone className="h-3 w-3 text-gray-400" />
                        <span className="text-xs text-gray-500">
                          {conversation.user_phone}
                        </span>
                        <span className="text-xs text-gray-400">•</span>
                        <span className="text-xs text-gray-500">
                          {getStatusText(conversation.status)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Área principal da conversa */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <>
            {/* Header da conversa */}
            <div className="p-4 border-b bg-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <MessageCircle className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h2 className="font-medium text-gray-900">
                      {selectedConversation.user_name || 'Usuário sem nome'}
                    </h2>
                    <div className="flex items-center space-x-2">
                      <Phone className="h-3 w-3 text-gray-400" />
                      <span className="text-sm text-gray-500">
                        {selectedConversation.user_phone || 'Telefone não informado'}
                      </span>
                      <span className="text-sm text-gray-400">•</span>
                      <span className="text-sm text-gray-500">
                        {getStatusText(selectedConversation.status)}
                      </span>
                    </div>
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Mensagens */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messagesError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Erro ao carregar mensagens: {messagesError instanceof Error ? messagesError.message : String(messagesError)}
                  </AlertDescription>
                </Alert>
              )}
              
              {messagesLoading ? (
                <div className="flex justify-center items-center h-32">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                </div>
              ) : messages.length === 0 ? (
                <div className="flex justify-center items-center h-32">
                  <div className="text-center">
                    <MessageCircle className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                    <p className="text-gray-500">Nenhuma mensagem nesta conversa</p>
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.direction === 'in' ? 'justify-start' : 'justify-end'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.direction === 'in'
                          ? 'bg-gray-200 text-gray-900'
                          : 'bg-blue-600 text-white'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      <p
                        className={`text-xs mt-1 ${
                          message.direction === 'in' ? 'text-gray-500' : 'text-blue-100'
                        }`}
                      >
                        {formatFullDate(message.created_at)}
                      </p>
                    </div>
                  </div>
                ))
              )}
              {/* Elemento para scroll automático */}
              <div ref={messagesEndRef} />
            </div>

            {/* Input de mensagem */}
            <div className="p-4 border-t bg-white">
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm" disabled={messagesLoading}>
                  <Paperclip className="h-4 w-4" />
                </Button>
                <div className="flex-1 relative">
                  <Input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Digite sua mensagem..."
                    onKeyPress={(e) => e.key === 'Enter' && !messagesLoading && handleSendMessage()}
                    disabled={messagesLoading}
                  />
                </div>
                <Button variant="ghost" size="sm" disabled={messagesLoading}>
                  <Smile className="h-4 w-4" />
                </Button>
                <Button 
                  onClick={handleSendMessage} 
                  disabled={!newMessage.trim() || messagesLoading}
                >
                  {messagesLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageCircle className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Selecione uma conversa
              </h3>
              <p className="text-gray-500">
                Escolha uma conversa da lista para começar a conversar
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
