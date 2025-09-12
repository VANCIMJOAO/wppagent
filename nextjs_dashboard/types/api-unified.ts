/**
 * 🔄 CF001 - API Types Unificados com Padronização snake_case ↔ camelCase
 * ======================================================================
 * 
 * Tipos TypeScript sincronizados com schemas Pydantic CF001.
 * Implementa os 15 campos críticos da tabela de mapeamento.
 * 
 * Funcionalidades:
 * - ✅ camelCase padrão para frontend
 * - ✅ Backward compatibility com snake_case
 * - ✅ Tipos estritamente tipados
 * - ✅ Enums sincronizados com backend
 */

// CF001 - Enums sincronizados com backend
export type AppointmentStatus = 'agendado' | 'confirmado' | 'realizado' | 'cancelado' | 'pendente';
export type ConversationStatus = 'active' | 'closed' | 'pending';
export type MessageDirection = 'in' | 'out';

// CF001 - Interface principal para appointments
export interface UnifiedAppointment {
  id: number;
  
  // CF001 - Campos críticos em camelCase
  userId: number;           // ✅ CF001 - user_id serialized
  businessId: number;       // ✅ CF001 - business_id serialized
  serviceId?: number;       // ✅ CF001 - service_id serialized
  
  dateTime: string;         // ✅ CF001 - date_time serialized (ISO 8601)
  durationMinutes: number;  // ✅ CF001 - duration_minutes serialized
  createdAt: string;        // ✅ CF001 - created_at serialized (ISO 8601)
  updatedAt?: string;       // ✅ CF001 - updated_at serialized (ISO 8601)
  
  status: AppointmentStatus;
  
  // Campos opcionais
  notes?: string;
  price?: number;
  clientName?: string;      // ✅ CF001 - client_name serialized
  clientPhone?: string;     // ✅ CF001 - client_phone serialized
  serviceName?: string;     // ✅ CF001 - service_name serialized
  businessName?: string;    // ✅ CF001 - business_name serialized
}

// CF001 - Request interface (aceita ambos formatos)
export interface UnifiedAppointmentRequest {
  userId?: number;
  businessId?: number;
  serviceId?: number;
  
  dateTime?: string;        // ✅ CF001 - Aceita camelCase
  durationMinutes?: number; // ✅ CF001 - Aceita camelCase
  
  status?: AppointmentStatus;
  notes?: string;
  price?: number;
  clientName?: string;
  clientPhone?: string;
  
  // Backward compatibility - API aceita ambos formatos
  user_id?: number;         // Alias para userId
  business_id?: number;     // Alias para businessId  
  service_id?: number;      // Alias para serviceId
  date_time?: string;       // Alias para dateTime
  duration_minutes?: number; // Alias para durationMinutes
  client_name?: string;     // Alias para clientName
  client_phone?: string;    // Alias para clientPhone
}

// CF001 - Interface para conversations
export interface UnifiedConversation {
  id: number;
  
  // CF001 - Campos críticos em camelCase
  userId: number;           // ✅ CF001 - user_id serialized
  businessId?: number;      // ✅ CF001 - business_id serialized
  status: ConversationStatus;
  
  lastMessageAt?: string;   // ✅ CF001 - last_message_at serialized
  createdAt: string;        // ✅ CF001 - created_at serialized
  updatedAt?: string;       // ✅ CF001 - updated_at serialized
  
  // CF001 - Campos computados
  totalMessages: number;    // ✅ CF001 - total_messages computed
  unreadMessages: number;   // ✅ CF001 - unread_messages computed
  lastInteraction?: string; // ✅ CF001 - last_interaction computed
}

// CF001 - Request interface para conversations
export interface UnifiedConversationRequest {
  userId?: number;
  businessId?: number;
  status?: ConversationStatus;
  
  // Backward compatibility
  user_id?: number;         // Alias para userId
  business_id?: number;     // Alias para businessId
}

// CF001 - Interface para messages
export interface UnifiedMessage {
  id: number;
  
  // CF001 - Campos críticos em camelCase
  conversationId: number;   // ✅ CF001 - conversation_id serialized
  content: string;
  messageType: string;      // ✅ CF001 - message_type serialized
  direction: MessageDirection;
  
  isRead: boolean;          // ✅ CF001 - is_read serialized
  isActive: boolean;        // ✅ CF001 - is_active serialized
  createdAt: string;        // ✅ CF001 - created_at serialized
  updatedAt?: string;       // ✅ CF001 - updated_at serialized
  
  // Campos opcionais
  senderName?: string;      // ✅ CF001 - sender_name serialized
  mediaUrl?: string;        // ✅ CF001 - media_url serialized
  whatsappId?: string;      // ✅ CF001 - whatsapp_id serialized
}

// CF001 - Request interface para messages
export interface UnifiedMessageRequest {
  conversationId?: number;
  content: string;
  messageType?: string;
  direction?: MessageDirection;
  isRead?: boolean;
  
  // Backward compatibility
  conversation_id?: number; // Alias para conversationId
  message_type?: string;    // Alias para messageType
  is_read?: boolean;        // Alias para isRead
}

// CF001 - Tipos utilitários para conversão
export type SnakeToCamelCase<T extends Record<string, any>> = {
  [K in keyof T as K extends `${infer A}_${infer B}` 
    ? `${A}${Capitalize<B>}` 
    : K]: T[K];
};

export type CamelToSnakeCase<T extends Record<string, any>> = {
  [K in keyof T as K extends `${infer A}${Capitalize<infer B>}` 
    ? `${A}_${Lowercase<B>}` 
    : K]: T[K];
};

// CF001 - Mapeamento dos 15 campos críticos
export const CF001_FIELD_MAPPING = {
  // Backend snake_case -> Frontend camelCase
  "date_time": "dateTime",
  "duration_minutes": "durationMinutes", 
  "user_id": "userId",
  "business_id": "businessId",
  "service_id": "serviceId",
  "created_at": "createdAt",
  "updated_at": "updatedAt",
  "last_message_at": "lastMessageAt",
  "message_type": "messageType",
  "conversation_id": "conversationId",
  "is_active": "isActive",
  "is_read": "isRead",
  "total_messages": "totalMessages",
  "unread_messages": "unreadMessages",
  "last_interaction": "lastInteraction"
} as const;

// CF001 - Função utilitária para conversão
export function convertSnakeToCamel<T extends Record<string, any>>(data: T): SnakeToCamelCase<T> {
  const converted = {} as any;
  for (const [key, value] of Object.entries(data)) {
    const camelKey = key.includes('_') 
      ? key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
      : key;
    converted[camelKey] = value;
  }
  return converted;
}

export function convertCamelToSnake<T extends Record<string, any>>(data: T): CamelToSnakeCase<T> {
  const converted = {} as any;
  for (const [key, value] of Object.entries(data)) {
    const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    converted[snakeKey] = value;
  }
  return converted;
}
