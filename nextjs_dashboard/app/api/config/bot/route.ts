import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.info('🤖 Buscando configurações do bot...');

    const botQuery = `
      SELECT
        id,
        business_id,
        auto_response_enabled,
        response_delay_min,
        response_delay_max,
        max_retries,
        language,
        timezone,
        max_message_length,
        working_hours_only,
        weekend_support,
        appointment_enabled,
        min_advance_booking_hours,
        max_advance_booking_days,
        max_appointments_per_day,
        appointment_buffer_minutes,
        auto_confirm_bookings,
        slot_duration_minutes,
        break_between_appointments_minutes,
        notification_lead_time_hours,
        send_confirmation_messages,
        send_reminder_messages,
        reminder_hours_before,
        follow_up_enabled,
        follow_up_delay_minutes,
        max_retries_data_collection,
        timeout_minutes_user_response,
        enable_human_handoff,
        data_collection_enabled,
        required_fields,
        optional_fields,
        created_at,
        updated_at
      FROM bot_configurations
      ORDER BY id
      LIMIT 1
    `;

    const botConfigs = await executeQuery(botQuery);

    if (botConfigs.length === 0) {
      // Retornar configurações padrão
      return NextResponse.json({
        success: true,
        data: {
          id: null,
          business_id: 1,
          name: 'Assistente Virtual',
          welcomeMessage: 'Olá! Como posso ajudar você hoje?',
          defaultResponse: 'Desculpe, não entendi sua mensagem. Pode reformular?',
          aiEnabled: false,
          responseDelay: 2,
          maxTokens: 150,
          temperature: 0.7,
          auto_response_enabled: false,
          response_delay_min: 1,
          response_delay_max: 3,
          max_retries: 3,
          language: 'pt-BR',
          timezone: 'America/Sao_Paulo',
          max_message_length: 500,
          working_hours_only: true,
          weekend_support: false,
          appointment_enabled: true,
          min_advance_booking_hours: 2,
          max_advance_booking_days: 30,
          max_appointments_per_day: 10,
          appointment_buffer_minutes: 15,
          auto_confirm_bookings: false,
          slot_duration_minutes: 60,
          break_between_appointments_minutes: 0,
          notification_lead_time_hours: 24,
          send_confirmation_messages: true,
          send_reminder_messages: true,
          reminder_hours_before: 2,
          follow_up_enabled: true,
          follow_up_delay_minutes: 60,
          max_retries_data_collection: 3,
          timeout_minutes_user_response: 10,
          enable_human_handoff: true,
          data_collection_enabled: true,
          required_fields: [],
          optional_fields: []
        }
      });
    }

    const bot = botConfigs[0];

    const formattedBot = {
      id: bot.id,
      business_id: bot.business_id,
      name: 'Assistente Virtual', // Campo não existe na tabela
      welcomeMessage: 'Olá! Como posso ajudar você hoje?', // Campo não existe na tabela
      defaultResponse: 'Desculpe, não entendi sua mensagem. Pode reformular?', // Campo não existe na tabela
      aiEnabled: bot.auto_response_enabled || false,
      responseDelay: bot.response_delay_min || 2,
      maxTokens: bot.max_message_length || 150,
      temperature: 0.7, // Campo não existe na tabela
      auto_response_enabled: bot.auto_response_enabled,
      response_delay_min: bot.response_delay_min,
      response_delay_max: bot.response_delay_max,
      max_retries: bot.max_retries,
      language: bot.language,
      timezone: bot.timezone,
      max_message_length: bot.max_message_length,
      working_hours_only: bot.working_hours_only,
      weekend_support: bot.weekend_support,
      appointment_enabled: bot.appointment_enabled,
      min_advance_booking_hours: bot.min_advance_booking_hours,
      max_advance_booking_days: bot.max_advance_booking_days,
      max_appointments_per_day: bot.max_appointments_per_day,
      appointment_buffer_minutes: bot.appointment_buffer_minutes,
      auto_confirm_bookings: bot.auto_confirm_bookings,
      slot_duration_minutes: bot.slot_duration_minutes,
      break_between_appointments_minutes: bot.break_between_appointments_minutes,
      notification_lead_time_hours: bot.notification_lead_time_hours,
      send_confirmation_messages: bot.send_confirmation_messages,
      send_reminder_messages: bot.send_reminder_messages,
      reminder_hours_before: bot.reminder_hours_before,
      follow_up_enabled: bot.follow_up_enabled,
      follow_up_delay_minutes: bot.follow_up_delay_minutes,
      max_retries_data_collection: bot.max_retries_data_collection,
      timeout_minutes_user_response: bot.timeout_minutes_user_response,
      enable_human_handoff: bot.enable_human_handoff,
      data_collection_enabled: bot.data_collection_enabled,
      required_fields: bot.required_fields || [],
      optional_fields: bot.optional_fields || [],
      created_at: bot.created_at,
      updated_at: bot.updated_at
    };

    debugLog.info(`✅ Configurações do bot carregadas`);

    return NextResponse.json({
      success: true,
      data: formattedBot
    });

  } catch (error) {
    debugLog.error('Erro ao buscar configurações do bot:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    debugLog.info('💾 Salvando configurações do bot...');

    const body = await request.json();
    const {
      name, welcomeMessage, defaultResponse, aiEnabled, responseDelay, maxTokens, temperature,
      auto_response_enabled, response_delay_min, response_delay_max, max_retries,
      language, timezone, max_message_length, working_hours_only, weekend_support,
      appointment_enabled, min_advance_booking_hours, max_advance_booking_days,
      max_appointments_per_day, appointment_buffer_minutes, auto_confirm_bookings,
      slot_duration_minutes, break_between_appointments_minutes, notification_lead_time_hours,
      send_confirmation_messages, send_reminder_messages, reminder_hours_before,
      follow_up_enabled, follow_up_delay_minutes, max_retries_data_collection,
      timeout_minutes_user_response, enable_human_handoff, data_collection_enabled,
      required_fields, optional_fields
    } = body;

    // Verificar se já existe uma configuração de bot
    const existingQuery = 'SELECT id FROM bot_configurations LIMIT 1';
    const existing = await executeQuery(existingQuery);

    let result;
    if (existing.length > 0) {
      // Atualizar configuração existente
      const updateQuery = `
        UPDATE bot_configurations 
        SET 
          auto_response_enabled = $1,
          response_delay_min = $2,
          response_delay_max = $3,
          max_retries = $4,
          language = $5,
          timezone = $6,
          max_message_length = $7,
          working_hours_only = $8,
          weekend_support = $9,
          appointment_enabled = $10,
          min_advance_booking_hours = $11,
          max_advance_booking_days = $12,
          max_appointments_per_day = $13,
          appointment_buffer_minutes = $14,
          auto_confirm_bookings = $15,
          slot_duration_minutes = $16,
          break_between_appointments_minutes = $17,
          notification_lead_time_hours = $18,
          send_confirmation_messages = $19,
          send_reminder_messages = $20,
          reminder_hours_before = $21,
          follow_up_enabled = $22,
          follow_up_delay_minutes = $23,
          max_retries_data_collection = $24,
          timeout_minutes_user_response = $25,
          enable_human_handoff = $26,
          data_collection_enabled = $27,
          required_fields = $28,
          optional_fields = $29,
          updated_at = NOW()
        WHERE id = $30
        RETURNING *
      `;
      
      result = await executeQuery(updateQuery, [
        auto_response_enabled || aiEnabled, response_delay_min || responseDelay, response_delay_max,
        max_retries, language, timezone, max_message_length || maxTokens, working_hours_only,
        weekend_support, appointment_enabled, min_advance_booking_hours, max_advance_booking_days,
        max_appointments_per_day, appointment_buffer_minutes, auto_confirm_bookings,
        slot_duration_minutes, break_between_appointments_minutes, notification_lead_time_hours,
        send_confirmation_messages, send_reminder_messages, reminder_hours_before,
        follow_up_enabled, follow_up_delay_minutes, max_retries_data_collection,
        timeout_minutes_user_response, enable_human_handoff, data_collection_enabled,
        JSON.stringify(required_fields || []), JSON.stringify(optional_fields || []),
        existing[0].id
      ]);
    } else {
      // Criar nova configuração (apenas campos essenciais)
      const insertQuery = `
        INSERT INTO bot_configurations (
          business_id, auto_response_enabled, response_delay_min, language, timezone, 
          max_message_length, working_hours_only, appointment_enabled, created_at, updated_at
        )
        VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW()
        )
        RETURNING *
      `;
      
      result = await executeQuery(insertQuery, [
        3, // business_id padrão (usar um que existe)
        auto_response_enabled || aiEnabled || false,
        response_delay_min || responseDelay || 2,
        language || 'pt-BR',
        timezone || 'America/Sao_Paulo',
        max_message_length || maxTokens || 150,
        working_hours_only || true,
        appointment_enabled || true
      ]);
    }

    if (result.length === 0) {
      throw new Error('Falha ao salvar configurações do bot');
    }

    const savedBot = result[0];

    debugLog.info(`✅ Configurações do bot salvas`);

    return NextResponse.json({
      success: true,
      data: {
        id: savedBot.id,
        business_id: savedBot.business_id,
        name: name || 'Assistente Virtual',
        welcomeMessage: welcomeMessage || 'Olá! Como posso ajudar você hoje?',
        defaultResponse: defaultResponse || 'Desculpe, não entendi sua mensagem. Pode reformular?',
        aiEnabled: savedBot.auto_response_enabled,
        responseDelay: savedBot.response_delay_min,
        maxTokens: savedBot.max_message_length,
        temperature: temperature || 0.7,
        ...savedBot
      },
      message: 'Configurações do bot salvas com sucesso'
    });

  } catch (error) {
    debugLog.error('Erro ao salvar configurações do bot:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      },
      { status: 500 }
    );
  }
}
