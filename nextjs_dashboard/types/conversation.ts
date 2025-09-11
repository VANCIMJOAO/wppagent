// Tipos para conversas e mensagens
export interface Message {
  id: number;
  content: string;
  sender_type: 'user' | 'agent';
  created_at: string;
  phone_number?: string;
  direction?: 'in' | 'out';
  message_type?: string;
}

export interface Conversation {
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
