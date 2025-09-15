/**
 * 💬 Componente Chat Real-Time
 * ============================
 *
 * Componente React para chat em tempo real com WebSocket:
 * - Interface de chat moderna
 * - Mensagens em tempo real
 * - Indicadores de digitação
 * - Status de entrega/leitura
 * - Histórico de mensagens
 * - Integração com WebSocket hook
 */

import React, { useState, useEffect, useRef } from 'react'
import { useMessagesWebSocket } from '../hooks/useRealtimeWebSocket'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// ============= TYPES =============
interface Message {
    id: number
    content: string
    user_id: number
    user_name?: string
    conversation_id: number
    direction: 'in' | 'out'
    message_type: string
    created_at: string
}

interface Conversation {
    id: number
    user_id: number
    status: string
    last_message_at: string
    created_at: string
    user?: {
        id: number
        nome: string
        telefone: string
        email?: string
    }
}

interface ChatProps {
    token?: string
    conversationId?: number
    className?: string
}

// ============= API FUNCTIONS =============
const fetchMessages = async (conversationId?: number): Promise<Message[]> => {
    const url = conversationId
        ? `/api/messages?conversation_id=${conversationId}`
        : '/api/messages'

    const response = await fetch(url, {
        headers: {
            'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}`
        }
    })

    if (!response.ok) {
        throw new Error('Falha ao carregar mensagens')
    }

    return response.json()
}

const fetchConversations = async (): Promise<Conversation[]> => {
    const response = await fetch('/api/conversations', {
        headers: {
            'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}`
        }
    })

    if (!response.ok) {
        throw new Error('Falha ao carregar conversas')
    }

    return response.json()
}

const sendMessageApi = async (data: {
    content: string
    conversation_id?: number
    client_phone?: string
}): Promise<Message> => {
    const response = await fetch('/api/messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${null // ✅ REMOVIDO: Token inseguro}`
        },
        body: JSON.stringify(data)
    })

    if (!response.ok) {
        throw new Error('Falha ao enviar mensagem')
    }

    return response.json()
}

// ============= CHAT COMPONENT =============
export default function RealtimeChat({ token, conversationId, className = '' }: ChatProps) {
    const queryClient = useQueryClient()
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLInputElement>(null)

    // Local state
    const [messageText, setMessageText] = useState('')
    const [isTyping, setIsTyping] = useState(false)
    const [selectedConversation, setSelectedConversation] = useState<number | undefined>(conversationId)

    // WebSocket connection
    const {
        isConnected,
        status,
        typingUsers,
        sendChatMessage,
        sendTypingStart,
        sendTypingStop,
        markMessageRead,
        connectionId
    } = useMessagesWebSocket(token, selectedConversation)

    // Queries
    const { data: conversations = [], isLoading: loadingConversations } = useQuery({
        queryKey: ['conversations'],
        queryFn: fetchConversations,
        enabled: !!token
    })

    const { data: messages = [], isLoading: loadingMessages } = useQuery({
        queryKey: ['messages', selectedConversation],
        queryFn: () => fetchMessages(selectedConversation),
        enabled: !!token && !!selectedConversation
    })

    // Mutations
    const sendMessageMutation = useMutation({
        mutationFn: sendMessageApi,
        onSuccess: () => {
            setMessageText('')
            queryClient.invalidateQueries({ queryKey: ['messages'] })
            queryClient.invalidateQueries({ queryKey: ['conversations'] })
        }
    })

    // Auto scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    // Handle typing indicators
    useEffect(() => {
        let typingTimeout: NodeJS.Timeout

        if (isTyping) {
            sendTypingStart()

            typingTimeout = setTimeout(() => {
                setIsTyping(false)
                sendTypingStop()
            }, 3000)
        }

        return () => {
            if (typingTimeout) {
                clearTimeout(typingTimeout)
            }
            if (isTyping) {
                sendTypingStop()
            }
        }
    }, [isTyping, sendTypingStart, sendTypingStop])

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setMessageText(e.target.value)

        if (!isTyping && e.target.value.trim()) {
            setIsTyping(true)
        } else if (isTyping && !e.target.value.trim()) {
            setIsTyping(false)
        }
    }

    // Handle send message
    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault()

        const content = messageText.trim()
        if (!content || !selectedConversation) return

        try {
            // Send via WebSocket first for immediate feedback
            const wsSuccess = sendChatMessage(
                content,
                conversations.find(c => c.id === selectedConversation)?.user?.telefone,
                selectedConversation
            )

            if (wsSuccess) {
                setMessageText('')
                setIsTyping(false)
            }

            // Also send via API as backup
            await sendMessageMutation.mutateAsync({
                content,
                conversation_id: selectedConversation
            })

        } catch (error) {
            console.error('Erro ao enviar mensagem:', error)
        }
    }

    // Handle message read
    const handleMessageRead = (messageId: number) => {
        markMessageRead(messageId)
    }

    // Get current conversation
    const currentConversation = conversations.find(c => c.id === selectedConversation)

    if (!token) {
        return (
            <div className={`flex items-center justify-center p-8 ${className}`}>
                <div className="text-gray-500">Por favor, faça login para acessar o chat</div>
            </div>
        )
    }

    return (
        <div className={`flex flex-col h-full ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b bg-white">
                <div className="flex items-center space-x-3">
                    <div className="relative">
                        <div className={`w-3 h-3 rounded-full ${
                            isConnected ? 'bg-green-500' : 'bg-red-500'
                        }`} />
                        {isConnected && (
                            <div className="absolute inset-0 w-3 h-3 bg-green-500 rounded-full animate-ping" />
                        )}
                    </div>
                    <div>
                        <h3 className="font-semibold">
                            {currentConversation?.user?.nome || 'Chat em Tempo Real'}
                        </h3>
                        <p className="text-sm text-gray-500">
                            {isConnected ? 'Conectado' : 'Desconectado'} • {status}
                        </p>
                    </div>
                </div>

                {/* Connection Info */}
                <div className="text-xs text-gray-400">
                    {connectionId && `ID: ${connectionId.slice(-8)}`}
                </div>
            </div>

            {/* Conversation List (if no conversation selected) */}
            {!selectedConversation && (
                <div className="flex-1 overflow-y-auto p-4">
                    <h4 className="font-medium mb-4">Conversas Ativas</h4>

                    {loadingConversations ? (
                        <div className="text-center py-8 text-gray-500">Carregando conversas...</div>
                    ) : conversations.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">Nenhuma conversa encontrada</div>
                    ) : (
                        <div className="space-y-2">
                            {conversations.map(conversation => (
                                <div
                                    key={conversation.id}
                                    className="p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100 transition-colors"
                                    onClick={() => setSelectedConversation(conversation.id)}
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="font-medium">
                                                {conversation.user?.nome || 'Usuário Desconhecido'}
                                            </div>
                                            <div className="text-sm text-gray-500">
                                                {conversation.user?.telefone}
                                            </div>
                                        </div>
                                        <div className="text-xs text-gray-400">
                                            {new Date(conversation.last_message_at).toLocaleTimeString()}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Messages */}
            {selectedConversation && (
                <>
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {loadingMessages ? (
                            <div className="text-center py-8 text-gray-500">Carregando mensagens...</div>
                        ) : messages.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">Nenhuma mensagem nesta conversa</div>
                        ) : (
                            messages.map(message => (
                                <div
                                    key={message.id}
                                    className={`flex ${message.direction === 'out' ? 'justify-end' : 'justify-start'}`}
                                    onClick={() => handleMessageRead(message.id)}
                                >
                                    <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                                        message.direction === 'out'
                                            ? 'bg-blue-500 text-white'
                                            : 'bg-gray-200 text-gray-800'
                                    }`}>
                                        <div className="break-words">{message.content}</div>
                                        <div className={`text-xs mt-1 ${
                                            message.direction === 'out'
                                                ? 'text-blue-100'
                                                : 'text-gray-500'
                                        }`}>
                                            {new Date(message.created_at).toLocaleTimeString()}
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}

                        {/* Typing Indicator */}
                        {typingUsers.length > 0 && (
                            <div className="flex justify-start">
                                <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
                                    <div className="flex space-x-1">
                                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Message Input */}
                    <form onSubmit={handleSendMessage} className="p-4 border-t bg-white">
                        <div className="flex space-x-2">
                            <button
                                type="button"
                                onClick={() => setSelectedConversation(undefined)}
                                className="px-3 py-2 text-gray-500 hover:text-gray-700 transition-colors"
                                title="Voltar para lista de conversas"
                            >
                                ←
                            </button>

                            <input
                                ref={inputRef}
                                type="text"
                                value={messageText}
                                onChange={handleInputChange}
                                placeholder={isConnected ? "Digite sua mensagem..." : "Desconectado..."}
                                disabled={!isConnected || sendMessageMutation.isPending}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                            />

                            <button
                                type="submit"
                                disabled={!messageText.trim() || !isConnected || sendMessageMutation.isPending}
                                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {sendMessageMutation.isPending ? 'Enviando...' : 'Enviar'}
                            </button>
                        </div>

                        {/* Status */}
                        <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
                            <div>
                                {isTyping && 'Digitando...'}
                            </div>
                            <div>
                                {isConnected ? '🟢 Online' : '🔴 Offline'} • {messages.length} mensagens
                            </div>
                        </div>
                    </form>
                </>
            )}
        </div>
    )
}

// ============= CHAT WIDGET =============
export function ChatWidget({ token }: { token?: string }) {
    const [isOpen, setIsOpen] = useState(false)
    const { isConnected, status } = useMessagesWebSocket(token)

    return (
        <>
            {/* Chat Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`fixed bottom-6 right-6 w-14 h-14 rounded-full text-white shadow-lg transition-all duration-300 z-50 ${
                    isConnected ? 'bg-green-500 hover:bg-green-600' : 'bg-gray-500 hover:bg-gray-600'
                }`}
            >
                <div className="relative">
                    {isOpen ? '×' : '💬'}
                    {isConnected && !isOpen && (
                        <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-pulse" />
                    )}
                </div>
            </button>

            {/* Chat Window */}
            {isOpen && (
                <div className="fixed bottom-24 right-6 w-96 h-96 bg-white rounded-lg shadow-2xl border border-gray-200 z-40">
                    <RealtimeChat
                        token={token}
                        className="h-full"
                    />
                </div>
            )}
        </>
    )
}
