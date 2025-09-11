/**
 * 📋 Index de Tipos TypeScript
 * ============================
 * 
 * Centraliza todos os exports de tipos para imports mais limpos.
 */

// Tipos auto-gerados do backend
export * from './api-generated';

// Tipos manuais específicos do frontend
export * from './analytics';
export * from './conversation';

// Nota: api.ts não é exportado para evitar conflitos com tipos gerados
// Para usar tipos manuais, importe diretamente: import { Type } from 'types/api-manual';

// Re-exports para compatibilidade
export type {
  ApiResponse,
  PaginatedData,
  CreateData,
  UpdateData,
  WithId,
  WithTimestamps
} from './api-generated';
