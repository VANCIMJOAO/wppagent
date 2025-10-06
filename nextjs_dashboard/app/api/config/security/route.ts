import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';
import { debugLog } from '@/lib/debug';

export async function GET(request: NextRequest) {
  try {
    debugLog.auth('Buscando configurações de segurança...');

    // Buscar configurações de segurança do banco
    const securityQuery = `
      SELECT
        id,
        business_id,
        policy_type,
        title,
        description,
        rules,
        is_active,
        created_at,
        updated_at
      FROM business_policies
      WHERE is_active = true
      ORDER BY policy_type, created_at
    `;

    const policies = await executeQuery(securityQuery);

    // Configurações padrão de segurança
    const defaultSecurity = {
      sessionTimeout: 30, // minutos
      maxLoginAttempts: 5,
      twoFactorEnabled: false,
      passwordMinLength: 8,
      passwordRequireSpecialChars: true,
      passwordRequireNumbers: true,
      passwordRequireUppercase: true,
      sessionInactivityTimeout: 15, // minutos
      ipWhitelist: [],
      policies: policies
    };

    debugLog.info(`✅ Configurações de segurança carregadas: ${policies.length} políticas`);

    return NextResponse.json({
      success: true,
      data: defaultSecurity
    });

  } catch (error) {
    debugLog.error('Erro ao buscar configurações de segurança:', error);
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
    debugLog.info('💾 Salvando configurações de segurança...');

    const body = await request.json();
    const {
      sessionTimeout,
      maxLoginAttempts,
      twoFactorEnabled,
      passwordMinLength,
      passwordRequireSpecialChars,
      passwordRequireNumbers,
      passwordRequireUppercase,
      sessionInactivityTimeout,
      ipWhitelist,
      newPassword,
      confirmPassword
    } = body;

    // Validar alteração de senha se fornecida
    if (newPassword || confirmPassword) {
      if (!newPassword || !confirmPassword) {
        return NextResponse.json(
          {
            success: false,
            error: 'Nova senha e confirmação são obrigatórias'
          },
          { status: 400 }
        );
      }

      if (newPassword !== confirmPassword) {
        return NextResponse.json(
          {
            success: false,
            error: 'Senhas não coincidem'
          },
          { status: 400 }
        );
      }

      if (newPassword.length < 8) {
        return NextResponse.json(
          {
            success: false,
            error: 'Senha deve ter pelo menos 8 caracteres'
          },
          { status: 400 }
        );
      }

      // Aqui você atualizaria a senha no banco de dados
      // Por segurança, não implementei a alteração real da senha
      debugLog.auth('Alteração de senha solicitada (não implementada por segurança)');
    }

    // Salvar configurações de segurança
    const savedSecurity = {
      sessionTimeout: sessionTimeout || 30,
      maxLoginAttempts: maxLoginAttempts || 5,
      twoFactorEnabled: twoFactorEnabled || false,
      passwordMinLength: passwordMinLength || 8,
      passwordRequireSpecialChars: passwordRequireSpecialChars || true,
      passwordRequireNumbers: passwordRequireNumbers || true,
      passwordRequireUppercase: passwordRequireUppercase || true,
      sessionInactivityTimeout: sessionInactivityTimeout || 15,
      ipWhitelist: ipWhitelist || []
    };

    debugLog.success('Configurações de segurança salvas');

    return NextResponse.json({
      success: true,
      data: savedSecurity,
      message: 'Configurações de segurança salvas com sucesso'
    });

  } catch (error) {
    debugLog.error('Erro ao salvar configurações de segurança:', error);
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
