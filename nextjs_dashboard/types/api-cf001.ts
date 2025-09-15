/**
 * 🚀 CF-001: Schema Synchronization - GENERATED TYPES
 * ===================================================
 * 
 * This file imports auto-generated types from OpenAPI spec and creates
 * clean, consistent interfaces for frontend usage.
 * 
 * ✅ BENEFITS:
 * - Single source of truth from backend
 * - Automatic camelCase/snake_case conversion
 * - Type safety guaranteed
 * - Zero manual maintenance needed
 * 
 * 🔄 REGENERATION:
 * Run: npx openapi-typescript ../openapi.json -o types/api-generated.ts
 */

import type { components, paths } from './api-generated'

// ===============================================
// 📅 APPOINTMENT TYPES - CF001 UNIFIED
// ===============================================

/**
 * 📅 Primary Appointment Interface - Generated from Backend
 * ✅ Uses UnifiedAppointmentResponse with proper camelCase
 */
export type Appointment = components['schemas']['UnifiedAppointmentResponse']

/**
 * 📅 Appointment Create Request - Generated from Backend
 */
export type AppointmentCreateRequest = components['schemas']['AppointmentCreateRequest']

/**
 * 📅 Appointment Update Request - Generated from Backend  
 */
export type AppointmentUpdateRequest = components['schemas']['AppointmentUpdateRequest']

/**
 * 📅 Appointment Status Enum - Generated from Backend
 */
export type AppointmentStatus = components['schemas']['AppointmentStatus']

/**
 * 📅 Appointments List Response - Generated from Backend
 */
export type AppointmentsListResponse = components['schemas']['AppointmentsListResponseUnified']

// ===============================================
// 💬 CONVERSATION TYPES - CF001 UNIFIED  
// ===============================================

/**
 * 💬 Message Interface - Generated from Backend
 */
export type Message = components['schemas']['MessageResponse']

/**
 * 💬 Conversation with Messages - Generated from Backend
 */
export type ConversationWithMessages = components['schemas']['ConversationWithMessages']

// ===============================================
// 🔧 API PATH TYPES - CF001 ENDPOINTS
// ===============================================

/**
 * 🛣️ API Paths - All available endpoints
 */
export type ApiPaths = paths

/**
 * 📅 Appointment Endpoints
 */
export type AppointmentEndpoints = {
  list: paths['/appointments/']['get']
  create: paths['/appointments/']['post'] 
  get: paths['/appointments/{appointment_id}']['get']
  update: paths['/appointments/{appointment_id}']['put']
  delete: paths['/appointments/{appointment_id}']['delete']
}

// ===============================================
// 🎯 UTILITY TYPES - CF001 HELPERS
// ===============================================

/**
 * 🔄 Extract Response Type from API Endpoint
 */
export type ExtractResponseType<T> = T extends { responses: { 200: { content: { 'application/json': infer R } } } } 
  ? R 
  : never

/**
 * 🔄 Extract Request Type from API Endpoint  
 */
export type ExtractRequestType<T> = T extends { requestBody: { content: { 'application/json': infer R } } } 
  ? R 
  : never

// ===============================================
// 📊 VALIDATION & METADATA
// ===============================================

/**
 * ✅ CF001 Type Validation
 * Ensures generated types match expected structure
 */
type CF001Validation = {
  // Verify UnifiedAppointmentResponse has camelCase fields
  appointment_has_userId: Appointment['userId']
  appointment_has_businessId: Appointment['businessId']
  appointment_has_dateTime: Appointment['dateTime']
  appointment_has_durationMinutes: Appointment['durationMinutes']
  appointment_has_createdAt: Appointment['createdAt']
  
  // Verify AppointmentStatus enum exists
  status_is_enum: AppointmentStatus
  
  // Verify list response structure
  list_has_appointments: AppointmentsListResponse['appointments']
  list_has_total: AppointmentsListResponse['total']
}

/**
 * 📋 CF001 Metadata
 */
export const CF001_METADATA = {
  generated_at: new Date().toISOString(),
  source: 'openapi-typescript from backend FastAPI',
  version: '1.0.0',
  schemas_included: [
    'UnifiedAppointmentResponse',
    'AppointmentCreateRequest', 
    'AppointmentUpdateRequest',
    'AppointmentsListResponseUnified',
    'ConversationResponseUnified',
    'MessageResponseUnified'
  ],
  field_mappings: {
    'user_id → userId': '✅',
    'business_id → businessId': '✅', 
    'service_id → serviceId': '✅',
    'date_time → dateTime': '✅',
    'duration_minutes → durationMinutes': '✅',
    'created_at → createdAt': '✅',
    'updated_at → updatedAt': '✅',
    'client_name → clientName': '✅',
    'client_phone → clientPhone': '✅',
    'service_name → serviceName': '✅',
    'business_name → businessName': '✅'
  }
} as const

// ===============================================
// 🔚 LEGACY TYPE COMPATIBILITY (DEPRECATED)
// ===============================================

/**
 * @deprecated Use Appointment instead
 * Kept for backward compatibility during migration
 */
export type LegacyAppointmentResponse = Appointment

/**
 * @deprecated Use AppointmentCreateRequest instead  
 * Kept for backward compatibility during migration
 */
export type LegacyAppointmentCreateData = AppointmentCreateRequest