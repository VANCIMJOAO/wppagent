"use client";

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Search, 
  Send, 
  MessageCircle, 
  Phone, 
  Video, 
  MoreVertical,
  Filter,
  Archive,
  Star,
  Paperclip,
  Smile,
  Mic,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { ConversasErrorBoundary } from '@/components/error-boundaries';
import { authService } from '@/lib/auth-service-robust';
import { useConversationEndpoints } from '@/lib/use-conversation-endpoints';

// Interfaces
interface Contact {
  id: string;
  name: string;
  phone: string;
  lastMessage: string;
  timestamp: string;
  unreadCount: number;
  status: 'online' | 'offline' | 'away';
  avatar?: string;
  tags: string[];
}

interface Message {
  id: string;
  contactId: string;
  content: string;
  timestamp: string;
  isFromMe: boolean;
  type: 'text' | 'image' | 'audio' | 'video' | 'document';
  status: 'sent' | 'delivered' | 'read';
}

// Mock data para fallback
const mockContacts: Contact[] = [
  {
    id: '1',
    name: 'João Silva',
    phone: '+55 11 99999-9999',
    lastMessage: 'Olá! Como posso ajudar?',
    timestamp: '14:30',
    unreadCount: 2,
    status: 'online',
    tags: ['Cliente', 'Premium']
  },
  {
    id: '2', 
    name: 'Maria Santos',
    phone: '+55 11 88888-8888',
    lastMessage: 'Obrigada pelo atendimento!',
    timestamp: '13:45',
    unreadCount: 0,
    status: 'offline',
    tags: ['Cliente']
  }
];

const mockMessages: Message[] = [
  {
    id: '1',
    contactId: '1',
    content: 'Olá! Como posso ajudar?',
    timestamp: '14:30',
    isFromMe: true,
    type: 'text',
    status: 'read'
  },
  {
    id: '2',
    contactId: '1', 
    content: 'Gostaria de saber sobre os seus produtos',
    timestamp: '14:28',
    isFromMe: false,
    type: 'text',
    status: 'delivered'
  }
];

export default function ConversationsPage() {
  const [contacts, setContacts] = useState<Contact[]>(mockContacts);
  const [messages, setMessages] = useState<Message[]>(mockMessages);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(mockContacts[0]);
  const [newMessage, setNewMessage] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // ✅ USAR HOOK DE DESCOBERTA DE ENDPOINTS
  const { 
    endpoints, 
    loading: endpointsLoading, 
    error: endpointsError, 
    fetchConversations, 
    reconnect,
    hasWorkingEndpoint 
  } = useConversationEndpoints();

  // Converter dados de analytics para formato de conversas
  const parseAnalyticsData = (data: any): Contact[] => {
    console.log('📊 Processando dados de analytics:', data);
    
    if (data?.conversation_details && typeof data.conversation_details === 'object') {
      const conversationEntries = Object.entries(data.conversation_details);
      
      return conversationEntries.map(([userId, details]: [string, any]) => ({
        id: userId,
        name: details.user_name || details.phone || `Usuário ${userId}`,
        phone: details.phone || userId,
        lastMessage: details.last_message || 'Ver detalhes da conversa',
        timestamp: new Date().toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit'
        }),
        unreadCount: details.message_count || 0,
        status: (details.status === 'active' ? 'online' : 'offline') as any,
        tags: ['Analytics']
      }));
    }
    
    // Fallback: criar entrada básica com info geral
    return [{
      id: 'analytics-summary',
      name: 'Resumo de Conversas',
      phone: 'Sistema',
      lastMessage: `${data.total_conversations || 0} conversas total, ${data.active_conversations || 0} ativas`,
      timestamp: new Date().toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
      }),
      unreadCount: data.active_conversations || 0,
      status: 'online' as any,
      tags: ['Analytics', 'Resumo']
    }];
  };

  // ✅ FUNÇÃO PARA CARREGAR CONVERSAS
  const loadConversations = async () => {
    if (!hasWorkingEndpoint) {
      console.log('⚠️ Nenhum endpoint disponível ainda');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 Carregando conversas...');
      
      const data = await fetchConversations();
      const backendContacts = parseAnalyticsData(data);
      
      if (backendContacts.length > 0) {
        console.log('✅ Conversas carregadas do backend:', backendContacts.length);
        setContacts(backendContacts);
        setSelectedContact(backendContacts[0]);
      } else {
        console.log('ℹ️ Usando dados mock');
        setContacts(mockContacts);
        setSelectedContact(mockContacts[0]);
      }
      
    } catch (error) {
      console.error('❌ Erro ao carregar conversas:', error);
      setError(error instanceof Error ? error.message : 'Erro ao carregar conversas');
      toast.error('Erro ao carregar conversas. Usando dados locais.');
      setContacts(mockContacts);
      setSelectedContact(mockContacts[0]);
    } finally {
      setLoading(false);
    }
  };

  // Carregar conversas quando endpoints estiverem prontos
  useEffect(() => {
    if (hasWorkingEndpoint && !loading) {
      loadConversations();
    }
  }, [hasWorkingEndpoint]);

  // Função para enviar mensagem
  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedContact) return;

    const message: Message = {
      id: Date.now().toString(),
      contactId: selectedContact.id,
      content: newMessage.trim(),
      timestamp: new Date().toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
      }),
      isFromMe: true,
      type: 'text',
      status: 'sent'
    };

    setMessages(prev => [...prev, message]);
    setNewMessage('');
    
    // Simular envio
    toast.success('Mensagem enviada!');
  };

  // Filtrar contatos
  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.phone.includes(searchTerm)
  );

  // Filtrar mensagens do contato selecionado
  const selectedMessages = messages.filter(msg => 
    msg.contactId === selectedContact?.id
  );

  if (endpointsLoading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
            <h2 className="text-lg font-medium mb-2">Descobrindo endpoints...</h2>
            <p className="text-gray-600">Testando conexões com o backend</p>
          </div>
        </div>
      </div>
    );
  }

  if (endpointsError && !hasWorkingEndpoint) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center max-w-md">
            <AlertCircle className="h-8 w-8 mx-auto mb-4 text-red-500" />
            <h2 className="text-lg font-medium mb-2 text-red-700">Erro de Conexão</h2>
            <p className="text-gray-600 mb-4">{endpointsError}</p>
            <Button onClick={reconnect} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Tentar Novamente
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ConversasErrorBoundary>
      <div className="flex h-screen bg-gray-50">
        {/* Lista de Conversas */}
        <div className="w-1/3 bg-white border-r border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-xl font-semibold">Conversas</h1>
              <div className="flex gap-2">
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={loadConversations}
                  disabled={loading || endpointsLoading}
                >
                  <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                </Button>
                <Button variant="ghost" size="sm">
                  <Filter className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar conversas..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            {/* Status dos Endpoints */}
            {hasWorkingEndpoint && (
              <div className="mt-2 text-xs text-green-600">
                ✅ Conectado via {endpoints.list?.path}
              </div>
            )}
            
            {error && (
              <div className="mt-2 text-xs text-red-600">
                ❌ {error}
              </div>
            )}
          </div>

          <div className="overflow-y-auto">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="p-4 border-b border-gray-100">
                  <div className="flex items-center space-x-3">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                </div>
              ))
            ) : (
              filteredContacts.map((contact) => (
                <div
                  key={contact.id}
                  className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                    selectedContact?.id === contact.id ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => setSelectedContact(contact)}
                >
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-12 w-12">
                      <AvatarImage src={contact.avatar} alt={contact.name} />
                      <AvatarFallback>
                        {contact.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-gray-900 truncate">
                          {contact.name}
                        </h3>
                        <span className="text-xs text-gray-500">
                          {contact.timestamp}
                        </span>
                      </div>
                      
                      <p className="text-sm text-gray-600 truncate">
                        {contact.lastMessage}
                      </p>
                      
                      <div className="flex items-center justify-between mt-1">
                        <div className="flex gap-1">
                          {contact.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                        
                        {contact.unreadCount > 0 && (
                          <Badge className="bg-blue-500 text-white text-xs">
                            {contact.unreadCount}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Área da Conversa */}
        <div className="flex-1 flex flex-col">
          {selectedContact ? (
            <>
              {/* Header da Conversa */}
              <div className="bg-white p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Avatar>
                      <AvatarImage src={selectedContact.avatar} alt={selectedContact.name} />
                      <AvatarFallback>
                        {selectedContact.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    
                    <div>
                      <h2 className="font-medium text-gray-900">
                        {selectedContact.name}
                      </h2>
                      <p className="text-sm text-gray-600">
                        {selectedContact.phone} • {selectedContact.status}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="sm">
                      <Phone className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Video className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Mensagens */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {selectedMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.isFromMe ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.isFromMe
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-900'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      <div className={`text-xs mt-1 ${
                        message.isFromMe ? 'text-blue-100' : 'text-gray-500'
                      }`}>
                        {message.timestamp} • {message.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Input de Nova Mensagem */}
              <div className="bg-white p-4 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="sm">
                    <Paperclip className="h-4 w-4" />
                  </Button>
                  
                  <div className="flex-1 relative">
                    <Input
                      placeholder="Digite sua mensagem..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                      className="pr-20"
                    />
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-1">
                      <Button variant="ghost" size="sm">
                        <Smile className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Mic className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  
                  <Button onClick={sendMessage} disabled={!newMessage.trim()}>
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Selecione uma conversa
                </h3>
                <p className="text-gray-600">
                  Escolha uma conversa da lista para começar a visualizar e enviar mensagens.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </ConversasErrorBoundary>
  );
}
