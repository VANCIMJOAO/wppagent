import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.info('🔔 Buscando configurações de notificações...');

    // Por enquanto, retornar configurações padrão
    // Em um sistema real, isso viria de uma tabela de configurações de notificações
    const defaultNotifications = {
      emailNotifications: true,
      smsNotifications: false,
      pushNotifications: true,
      appointmentReminders: true,
      newMessageAlerts: true,
      emailSettings: {
        smtp_server: '',
        smtp_port: 587,
        smtp_username: '',
        smtp_password: '',
        from_email: '',
        from_name: ''
      },
      smsSettings: {
        provider: '',
        api_key: '',
        phone_number: ''
      },
      pushSettings: {
        enabled: true,
        sound: true,
        vibration: true
      }
    };

    debugLog.success('Configurações de notificações carregadas (padrão)');

    return NextResponse.json({
      success: true,
      data: defaultNotifications
    });

  } catch (error) {
    debugLog.error('Erro ao buscar configurações de notificações:', error);
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
    debugLog.info('💾 Salvando configurações de notificações...');

    const body = await request.json();
    const {
      emailNotifications,
      smsNotifications,
      pushNotifications,
      appointmentReminders,
      newMessageAlerts,
      emailSettings,
      smsSettings,
      pushSettings
    } = body;

    // Por enquanto, apenas simular o salvamento
    // Em um sistema real, isso seria salvo em uma tabela de configurações
    const savedNotifications = {
      emailNotifications: emailNotifications || false,
      smsNotifications: smsNotifications || false,
      pushNotifications: pushNotifications || false,
      appointmentReminders: appointmentReminders || false,
      newMessageAlerts: newMessageAlerts || false,
      emailSettings: emailSettings || {
        smtp_server: '',
        smtp_port: 587,
        smtp_username: '',
        smtp_password: '',
        from_email: '',
        from_name: ''
      },
      smsSettings: smsSettings || {
        provider: '',
        api_key: '',
        phone_number: ''
      },
      pushSettings: pushSettings || {
        enabled: true,
        sound: true,
        vibration: true
      }
    };

    debugLog.success('Configurações de notificações salvas');

    return NextResponse.json({
      success: true,
      data: savedNotifications,
      message: 'Configurações de notificações salvas com sucesso'
    });

  } catch (error) {
    debugLog.error('Erro ao salvar configurações de notificações:', error);
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
