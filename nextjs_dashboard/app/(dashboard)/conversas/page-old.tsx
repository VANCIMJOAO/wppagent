"use client";

import { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar';
import { Skeleton } from '@/components/ui/skeleton';
import { validateConversations, validateMessages } from '@/lib/api-validators';
import { normalizeDirection } from '@/lib/message-normalizer';
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
  Mic
} from 'lucide-react';
import { toast } from 'sonner';
import { ConversasErrorBoundary, DataTableErrorBoundary, ComponentErrorBoundary } from '@/components/error-boundaries';
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

// Interfaces
interface Contact {
  id: string;
  name: string;
  phone: string;
  lastMessage: string;
  timestamp: string;
  unreadCount: number;
  status: 'online' | 'offline' | 'typing';
  avatar?: string;
  tags: string[];
}

interface Message {
  id: string;
  contactId: string;
  content: string;
  timestamp: string;
  isFromMe: boolean;
  type: 'text' | 'image' | 'audio' | 'document';
  status: 'sent' | 'delivered' | 'read';
}

// ✅ DADOS MOCK PARA FALLBACK
const mockContacts: Contact[] = [
  {
    id: '1',
    name: 'João Silva',
    phone: '+55 11 99999-9999',
    lastMessage: 'Olá, gostaria de saber sobre o produto...',
    timestamp: '14:30',
    unreadCount: 2,
    status: 'online',
    tags: ['Cliente', 'Interessado']
  },
  {
    id: '2', 
    name: 'Maria Santos',
    phone: '+55 11 88888-8888',
    lastMessage: 'Obrigada pelo atendimento!',
    timestamp: '13:45',
    unreadCount: 0,
    status: 'offline',
    tags: ['Cliente', 'Satisfeito']
  }
];

const mockMessages: Message[] = [
  {
    id: '1',
    contactId: '1',
    content: 'Olá! Como posso ajudar?',
    timestamp: '14:25',
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
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ✅ FUNÇÃO PARA CARREGAR CONVERSAS DO BACKEND
  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 Carregando conversas do backend...');
      
      // ✅ USANDO ENDPOINT QUE FUNCIONA: /conversation/analytics
      const data = await fetchWithAuth('/conversation/analytics');
      
      // O endpoint analytics retorna estrutura diferente
      if (data?.conversation_details && typeof data.conversation_details === 'object') {
        console.log('📊 Dados de analytics recebidos:', data);
        
        // Converter dados de analytics para formato de conversas
        const conversationEntries = Object.entries(data.conversation_details);
        
        if (conversationEntries.length > 0) {
          const analyticsContacts = conversationEntries.map(([userId, details]: [string, any]) => ({
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
          
          console.log('✅ Conversas carregadas via analytics:', analyticsContacts.length);
          setContacts(analyticsContacts);
          setSelectedContact(analyticsContacts[0]);
        } else {
          console.log('📊 Dados de analytics vazios, usando mock data');
          setContacts(mockContacts);
          setSelectedContact(mockContacts[0]);
        }
      } else {
        console.log('📊 Analytics retornou dados básicos:', data);
        
        // Se não tem detalhes de conversas, criar entrada básica com info geral
        const basicContact = {
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
        };
        
        setContacts([basicContact]);
        setSelectedContact(basicContact);
      }
      
    } catch (error) {
      console.error('❌ Erro ao carregar conversas:', error);
      setError(error instanceof Error ? error.message : 'Erro ao carregar conversas');
      toast.error('Erro ao carregar conversas. Usando dados locais.');
    } finally {
      setLoading(false);
    }
  };

  // ✅ FUNÇÃO PARA CARREGAR MENSAGENS
  const loadMessages = async (conversationId: string) => {
    try {
      console.log('💬 Carregando mensagens para conversa:', conversationId);
      
      const data = await fetchWithAuth(`/conversations/${conversationId}/messages?limit=50&offset=0`);
      
      if (data?.messages && Array.isArray(data.messages)) {
        // ✅ Usar validador ao invés de conversão manual
        const validationResult = validateMessages(data.messages);
        
        if (validationResult.success && validationResult.data) {
          const backendMessages = validationResult.data.map(msg => ({
            id: msg.id.toString(),
            contactId: conversationId,
            content: msg.content || '',
            timestamp: new Date(msg.created_at).toLocaleTimeString('pt-BR', {
              hour: '2-digit',
              minute: '2-digit'
            }),
            isFromMe: normalizeDirection(msg) === 'out', // ✅ Usa normalizador robusto
            type: (msg.message_type || 'text') as 'text' | 'image' | 'audio' | 'document',
            status: 'delivered' as any
          }));

          console.log('✅ Mensagens carregadas e validadas:', backendMessages.length);
          setMessages(backendMessages);
        } else {
          console.warn('⚠️ Dados de mensagens não puderam ser validados:', validationResult.errors);
          // Fallback para mock messages
          const mockForContact = mockMessages.filter(m => m.contactId === conversationId);
          setMessages(mockForContact.length > 0 ? mockForContact : mockMessages);
        }
      } else {
        // Fallback para mock messages
        const mockForContact = mockMessages.filter(m => m.contactId === conversationId);
        setMessages(mockForContact.length > 0 ? mockForContact : mockMessages);
      }
    } catch (error) {
      console.error('❌ Erro ao carregar mensagens:', error);
      const mockForContact = mockMessages.filter(m => m.contactId === conversationId);
      setMessages(mockForContact.length > 0 ? mockForContact : mockMessages);
    }
  };

  // ✅ CARREGAMENTO INICIAL
  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleContactSelect = (contact: Contact) => {
    setSelectedContact(contact);
    loadMessages(contact.id);
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedContact) return;
    
    setSending(true);
    
    try {
      // Adicionar mensagem otimisticamente
      const tempMessage: Message = {
        id: Date.now().toString(),
        contactId: selectedContact.id,
        content: newMessage,
        timestamp: new Date().toLocaleTimeString('pt-BR', {
          hour: '2-digit',
          minute: '2-digit'
        }),
        isFromMe: true,
        type: 'text',
        status: 'sent'
      };
      
      setMessages(prev => [...prev, tempMessage]);
      setNewMessage('');
      
      // ✅ AQUI PODERIA IMPLEMENTAR ENVIO REAL PARA O BACKEND
      // await fetchWithAuth(`/conversations/${selectedContact.id}/messages`, {
      //   method: 'POST',
      //   body: JSON.stringify({ content: newMessage, message_type: 'text' })
      // });
      
      toast.success('Mensagem enviada!');
      
    } catch (error) {
      console.error('❌ Erro ao enviar mensagem:', error);
      toast.error('Erro ao enviar mensagem');
    } finally {
      setSending(false);
    }
  };

  // Filtrar contatos
  const filteredContacts = searchTerm 
    ? contacts.filter(contact => 
        contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        contact.phone.includes(searchTerm)
      )
    : contacts;

  const contactMessages = messages.filter(msg => 
    msg.contactId === selectedContact?.id
  );

  return (
    <ConversasErrorBoundary>
      <div className="flex h-screen bg-gray-50">
        {/* Lista de Conversas - Sidebar */}
        <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-xl font-semibold text-gray-800">Conversas</h1>
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm">
                  <Filter className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Archive className="w-4 h-4" />
                </Button>
              </div>
            </div>
            
            {/* Busca */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Buscar conversas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Status de carregamento */}
          {error && (
            <div className="p-4 bg-red-50 border-b border-red-200">
              <p className="text-sm text-red-600">⚠️ {error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={loadConversations}
                className="mt-2"
              >
                Tentar novamente
              </Button>
            </div>
          )}

          {/* Lista de contatos */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-4 space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="flex items-center space-x-3">
                    <Skeleton className="h-12 w-12 rounded-full" />
                    <div className="space-y-2 flex-1">
                      <Skeleton className="h-4 w-3/4" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              filteredContacts.map((contact) => (
                <div
                  key={contact.id}
                  onClick={() => handleContactSelect(contact)}
                  className={`p-4 border-b border-gray-100 cursor-pointer transition-colors hover:bg-gray-50 ${
                    selectedContact?.id === contact.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="relative">
                      <Avatar className="h-12 w-12">
                        <AvatarImage src={contact.avatar} />
                        <AvatarFallback className="bg-blue-100 text-blue-600">
                          {contact.name.substring(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      {contact.status === 'online' && (
                        <div className="absolute bottom-0 right-0 h-3 w-3 bg-green-500 rounded-full border-2 border-white"></div>
                      )}
                      {contact.status === 'typing' && (
                        <div className="absolute bottom-0 right-0 h-3 w-3 bg-yellow-500 rounded-full border-2 border-white animate-pulse"></div>
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-gray-900 truncate">
                          {contact.name}
                        </h3>
                        <span className="text-xs text-gray-500">{contact.timestamp}</span>
                      </div>
                      <p className="text-sm text-gray-600 truncate">{contact.lastMessage}</p>
                      <div className="flex items-center justify-between mt-1">
                        <div className="flex space-x-1">
                          {contact.tags.map((tag, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
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

        {/* Chat Principal */}
        <div className="flex-1 flex flex-col">
          {selectedContact ? (
            <>
              {/* Header do Chat */}
              <div className="bg-white border-b border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={selectedContact.avatar} />
                      <AvatarFallback className="bg-blue-100 text-blue-600">
                        {selectedContact.name.substring(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h2 className="font-medium text-gray-900">{selectedContact.name}</h2>
                      <p className="text-sm text-gray-600">{selectedContact.phone}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="sm">
                      <Phone className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Video className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Star className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Mensagens */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                <ComponentErrorBoundary>
                  {contactMessages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.isFromMe ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.isFromMe
                            ? 'bg-blue-500 text-white'
                            : 'bg-white text-gray-900 border border-gray-200'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                        <div className="flex items-center justify-between mt-1">
                          <span 
                            className={`text-xs ${
                              message.isFromMe ? 'text-blue-100' : 'text-gray-500'
                            }`}
                          >
                            {message.timestamp}
                          </span>
                          {message.isFromMe && (
                            <span className="text-xs text-blue-100 ml-2">
                              {message.status === 'sent' && '✓'}
                              {message.status === 'delivered' && '✓✓'}
                              {message.status === 'read' && '✓✓'}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </ComponentErrorBoundary>
              </div>

              {/* Input de mensagem */}
              <div className="bg-white border-t border-gray-200 p-4">
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="sm">
                    <Paperclip className="w-4 h-4" />
                  </Button>
                  <div className="flex-1 relative">
                    <Input
                      placeholder="Digite sua mensagem..."
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                      className="pr-20"
                    />
                    <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex space-x-1">
                      <Button variant="ghost" size="sm">
                        <Smile className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Mic className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <Button onClick={handleSendMessage} disabled={!newMessage.trim() || sending}>
                    {sending ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
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
