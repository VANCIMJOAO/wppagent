"use client";

import { useState, useEffect, useRef } from 'react';
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
  Mic
} from 'lucide-react';
import { toast } from 'sonner';
import { 
  getConversations, 
  getConversationMessages,
  convertConversationToContact,
  convertMessageToConversationMessage,
  type Conversation,
  type Message as BackendMessage,
  type ConversationMessage
} from '@/lib/api-service';

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
  },
  {
    id: '3',
    name: 'Pedro Costa',
    phone: '+55 11 77777-7777',
    lastMessage: 'Quando vai chegar meu pedido?',
    timestamp: '12:20',
    unreadCount: 1,
    status: 'typing',
    tags: ['Cliente', 'Urgente']
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
  },
  {
    id: '3',
    contactId: '1',
    content: 'Temos várias opções disponíveis. Qual tipo de produto você procura?',
    timestamp: '14:30',
    isFromMe: true,
    type: 'text',
    status: 'read'
  }
];

export default function ConversationsPage() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load conversations and contacts
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Fetch real conversations from backend
        const { conversations } = await getConversations(50, 0, 'active');
        
        // Convert backend conversations to frontend Contact format
        const contactsData = conversations.map(convertConversationToContact);
        
        setContacts(contactsData);
        
        // Set the first contact as selected if available
        if (contactsData.length > 0) {
          const firstContact = contactsData[0];
          setSelectedContact(firstContact);
          
          // Load messages for the first conversation
          const conversationId = parseInt(firstContact.id);
          const { messages: backendMessages } = await getConversationMessages(conversationId);
          
          // Convert backend messages to frontend format
          const messagesData = backendMessages.map(convertMessageToConversationMessage);
          setMessages(messagesData);
        }
        
      } catch (error) {
        console.error('Erro ao carregar conversas:', error);
        toast.error('Erro ao carregar conversas');
        
        // Fallback to mock data if real data fails
        const mockContactsData: Contact[] = [
          {
            id: '1',
            name: 'João Silva',
            phone: '+55 11 99999-9999',
            lastMessage: 'Olá, gostaria de agendar um horário',
            timestamp: '10:30',
            unreadCount: 2,
            status: 'online',
            tags: ['cliente', 'vip']
          },
          {
            id: '2',
            name: 'Maria Santos',
            phone: '+55 11 88888-8888',
            lastMessage: 'Obrigada pelo atendimento!',
            timestamp: '09:45',
            unreadCount: 0,
            status: 'offline',
            tags: ['cliente']
          }
        ];

      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const filteredContacts = contacts.filter(contact => 
    contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.phone.includes(searchTerm)
  );

  const contactMessages = messages.filter(msg => msg.contactId === selectedContact?.id);

  // Function to load messages for selected contact
  const loadMessagesForContact = async (contact: Contact) => {
    try {
      const conversationId = parseInt(contact.id);
      const { messages: backendMessages } = await getConversationMessages(conversationId);
      const messagesData = backendMessages.map(convertMessageToConversationMessage);
      setMessages(messagesData);
    } catch (error) {
      console.error('Erro ao carregar mensagens:', error);
      toast.error('Erro ao carregar mensagens');
    }
  };

  // Handle contact selection
  const handleContactSelect = (contact: Contact) => {
    setSelectedContact(contact);
    loadMessagesForContact(contact);
  };

  const sendMessage = () => {
    if (!newMessage.trim() || !selectedContact) return;

    const message: Message = {
      id: Date.now().toString(),
      contactId: selectedContact.id,
      content: newMessage,
      timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
      isFromMe: true,
      type: 'text',
      status: 'sent'
    };

    setMessages(prev => [...prev, message]);
    setNewMessage('');

    // Simular resposta automática
    setTimeout(() => {
      const autoReply: Message = {
        id: (Date.now() + 1).toString(),
        contactId: selectedContact.id,
        content: 'Obrigado pela mensagem! Vou analisar sua solicitação.',
        timestamp: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
        isFromMe: false,
        type: 'text',
        status: 'delivered'
      };
      setMessages(prev => [...prev, autoReply]);
    }, 2000);
  };

  const getStatusColor = (status: Contact['status']) => {
    switch (status) {
      case 'online': return 'bg-green-500';
      case 'typing': return 'bg-blue-500 animate-pulse';
      default: return 'bg-gray-400';
    }
  };

  const getTagColor = (tag: string) => {
    switch (tag.toLowerCase()) {
      case 'urgente': return 'bg-red-100 text-red-800';
      case 'interessado': return 'bg-yellow-100 text-yellow-800';
      case 'cliente': return 'bg-blue-100 text-blue-800';
      case 'satisfeito': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="fixed inset-0 left-80 bg-gray-50"> {/* Use fixed positioning, accounting for sidebar width */}
      <div className="flex h-full">
        {/* Lista de Conversas */}
        <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
          {/* Header da Lista */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Conversas</h2>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm">
                <Filter className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <Archive className="w-4 h-4" />
              </Button>
            </div>
          </div>
          
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

        {/* Lista de Contatos */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            // Loading skeleton
            Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="p-4 border-b border-gray-100">
                <div className="flex items-start space-x-3">
                  <Skeleton className="w-12 h-12 rounded-full" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="h-3 w-12" />
                    </div>
                    <Skeleton className="h-4 w-full max-w-48" />
                    <div className="flex items-center mt-2 space-x-2">
                      <Skeleton className="h-5 w-16" />
                      <Skeleton className="h-5 w-12" />
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            filteredContacts.map((contact) => (
              <div
                key={contact.id}
                onClick={() => handleContactSelect(contact)}
                className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  selectedContact?.id === contact.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className="relative">
                    <Avatar className="w-12 h-12">
                      <AvatarImage src={contact.avatar} />
                      <AvatarFallback>{contact.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                    </Avatar>
                    <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${getStatusColor(contact.status)}`} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                    <h3 className="font-medium text-gray-900 truncate">{contact.name}</h3>
                    <span className="text-xs text-gray-500">{contact.timestamp}</span>
                  </div>
                  
                  <p className="text-sm text-gray-600 truncate mt-1">{contact.lastMessage}</p>
                  
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex flex-wrap gap-1">
                      {contact.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className={`text-xs ${getTagColor(tag)}`}>
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

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {selectedContact ? (
          <>
            {/* Header do Chat */}
            <div className="bg-white border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Avatar className="w-10 h-10">
                    <AvatarImage src={selectedContact.avatar} />
                    <AvatarFallback>{selectedContact.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                  </Avatar>
                  
                  <div>
                    <h3 className="font-medium text-gray-900">{selectedContact.name}</h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{selectedContact.phone}</span>
                      <div className={`w-2 h-2 rounded-full ${getStatusColor(selectedContact.status)}`} />
                      <span className="text-sm text-gray-500 capitalize">{selectedContact.status}</span>
                    </div>
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

            {/* Área de Mensagens */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
              {contactMessages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.isFromMe ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.isFromMe 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-white text-gray-900 border border-gray-200'
                  }`}>
                    <p className="text-sm">{message.content}</p>
                    <div className={`flex items-center justify-end mt-1 space-x-1 ${
                      message.isFromMe ? 'text-blue-100' : 'text-gray-500'
                    }`}>
                      <span className="text-xs">{message.timestamp}</span>
                      {message.isFromMe && (
                        <div className="text-xs">
                          {message.status === 'sent' && '✓'}
                          {message.status === 'delivered' && '✓✓'}
                          {message.status === 'read' && <span className="text-blue-200">✓✓</span>}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input de Mensagem */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="flex items-end space-x-3">
                <Button variant="ghost" size="sm" className="mb-2">
                  <Paperclip className="w-4 h-4" />
                </Button>
                
                <div className="flex-1">
                  <Input
                    placeholder="Digite sua mensagem..."
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    className="resize-none"
                  />
                </div>
                
                <Button variant="ghost" size="sm" className="mb-2">
                  <Smile className="w-4 h-4" />
                </Button>
                
                <Button variant="ghost" size="sm" className="mb-2">
                  <Mic className="w-4 h-4" />
                </Button>
                
                <Button 
                  onClick={sendMessage}
                  className="bg-blue-500 hover:bg-blue-600 text-white"
                  disabled={!newMessage.trim()}
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhuma conversa selecionada</h3>
              <p className="text-gray-600">Selecione uma conversa para começar a chatear</p>
            </div>
          </div>
        )}
      </div>
    </div>
    </div>
  );
}