/**
 * 🚀 API Route OTIMIZADA para Login Admin
 * Login local ultra-rápido sem requisições externas
 */

import { NextRequest, NextResponse } from 'next/server';
import { executeQueryWithRetry } from '@/lib/database-optimized';
import authCache from '@/lib/auth-cache';
import { SignJWT } from 'jose';
import { debugLog } from '@/lib/debug';

// Chave secreta para JWT local
const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'whatsapp_agent_super_secret_2024_railway_production'
);

export async function POST(request: NextRequest) {
  try {
    const startTime = Date.now();
    const { username, password } = await request.json();

    if (!username || !password) {
      return NextResponse.json(
        { error: 'Username e password são obrigatórios' },
        { status: 400 }
      );
    }

    // 🚀 OTIMIZAÇÃO: Verificar cache primeiro
    let admin = authCache.getCachedAdmin(username);
    
    if (!admin) {
      debugLog.info('🔍 Buscando admin no banco de dados...');
      // Buscar usuário admin na tabela admin_users
      const adminResult = await executeQueryWithRetry(
        'SELECT id, username, password_hash, full_name, is_active FROM admin_users WHERE username = $1 AND is_active = true',
        [username]
      );

      if (adminResult.length === 0) {
        debugLog.error('Usuário admin não encontrado:', username);
        return NextResponse.json(
          { error: 'Credenciais inválidas' },
          { status: 401 }
        );
      }

      admin = adminResult[0];
      debugLog.success('Usuário admin encontrado:', admin?.username);
      
      // Cachear admin para próximas consultas
      if (admin) {
        authCache.setCachedAdmin(username, admin);
      }
    } else {
      debugLog.info('⚡ Admin encontrado no cache:', admin?.username);
    }

    // Verificar senha (usando bcrypt)
    if (!admin) {
      return NextResponse.json(
        { error: 'Admin não encontrado' },
        { status: 401 }
      );
    }
    
    const bcrypt = require('bcryptjs');
    const isValidPassword = await bcrypt.compare(password, admin.password_hash);

    if (!isValidPassword) {
      debugLog.error('Senha inválida para usuário:', username);
      // Invalidar cache em caso de senha incorreta
      authCache.invalidateAdmin(username);
      return NextResponse.json(
        { error: 'Credenciais inválidas' },
        { status: 401 }
      );
    }

    debugLog.success('Login realizado com sucesso para:', admin.username);

    // 🚀 OTIMIZAÇÃO: Gerar JWT local (sem requisição externa)
    const token = await new SignJWT({
      user_id: admin.id,
      username: admin.username,
      role: 'admin',
      full_name: admin.full_name
    })
      .setProtectedHeader({ alg: 'HS256' })
      .setIssuedAt()
      .setExpirationTime('2h')
      .sign(JWT_SECRET);

    const totalTime = Date.now() - startTime;
    debugLog.info(`⚡ Login ULTRA-RÁPIDO concluído em ${totalTime}ms`);

    // ✅ SEGURO: Definir cookies HttpOnly seguros
    const loginResponse = NextResponse.json({
      success: true,
      message: 'Login realizado com sucesso',
      performance: {
        totalTime: `${totalTime}ms`,
        cacheHit: !!authCache.getCachedAdmin(username)
      }
    });

    // Definir cookie de autenticação (2 horas)
    loginResponse.cookies.set('access_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 2 * 60 * 60 * 1000, // 2 horas
      path: '/'
    });

    // Definir cookie de sessão com informações do usuário
    const sessionInfo = {
      isAuthenticated: true,
      user: {
        id: admin.id,
        name: admin.full_name,
        username: admin.username,
        role: 'admin'
      },
      tokenExpiry: Date.now() + (2 * 60 * 60 * 1000) // 2 horas
    };

    loginResponse.cookies.set('session-info', JSON.stringify(sessionInfo), {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 2 * 60 * 60 * 1000, // 2 horas
      path: '/'
    });

    return loginResponse;

  } catch (error) {
    debugLog.error('Erro no login:', error);
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    );
  }
}
