/**
 * 🔐 API Route Segura para Login Admin
 * Autenticação local via PostgreSQL
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import authCache from '@/lib/auth-cache';
import { executeQueryWithRetry } from '@/lib/database-optimized';
import { debugLog } from '@/lib/debug';

// Configuração do banco PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway',
  ssl: {
    rejectUnauthorized: false
  }
});

export async function POST(request: NextRequest) {
  try {
    debugLog.auth('Login admin via autenticação local PostgreSQL...');

    // Obter credenciais do body da requisição
    let username, password;
    try {
      const body = await request.json();
      username = body.username;
      password = body.password;
    } catch (jsonError) {
      debugLog.error('Erro ao fazer parse do JSON:', jsonError);
      return NextResponse.json(
        { error: 'Dados inválidos no corpo da requisição' },
        { status: 400 }
      );
    }

    if (!username || !password) {
      debugLog.error('Username ou password ausentes:', { username: !!username, password: !!password });
      return NextResponse.json(
        { error: 'Username e password são obrigatórios' },
        { status: 400 }
      );
    }

    debugLog.info('🔍 Tentando login para usuário:', username);

    // Verificar credenciais na database
    let client;
    try {
      client = await pool.connect();
      debugLog.success('Conectado ao banco PostgreSQL');
    } catch (dbError) {
      debugLog.error('Erro ao conectar com o banco:', dbError);
      return NextResponse.json(
        { error: 'Erro de conexão com o banco de dados' },
        { status: 500 }
      );
    }
    
    try {
      const startTime = Date.now();
      
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

      // 🚀 OTIMIZAÇÃO: Verificar cache de token primeiro
      let token = authCache.getCachedToken(admin.id);
      
      if (!token) {
        // 🚀 OTIMIZAÇÃO: Gerar JWT local (sem requisição externa)
        const { SignJWT } = await import('jose');
        const JWT_SECRET = new TextEncoder().encode(
          process.env.JWT_SECRET || 'fallback-secret-key'
        );

        token = await new SignJWT({
          sub: admin.id.toString(), // Campo obrigatório para o backend
          username: admin.username,
          role: 'admin',
          full_name: admin.full_name,
          type: 'access' // Adicionar campo obrigatório para o backend
        })
          .setProtectedHeader({ alg: 'HS256' })
          .setIssuedAt()
          .setExpirationTime('2h')
          .sign(JWT_SECRET);
        
        // Cachear token para próximas requisições
        authCache.setCachedToken(admin.id, token, 2 * 60 * 60); // 2 horas
      } else {
        debugLog.info('⚡ Token encontrado no cache para admin:', admin.username);
      }
      const totalTime = Date.now() - startTime;
      debugLog.info('🔑 Token Railway obtido, length:', token.length);
      debugLog.info('🔑 Token primeiros 50 chars:', token.substring(0, 50));
      debugLog.info(`⚡ Login otimizado concluído em ${totalTime}ms`);

      // ✅ SEGURO: Definir cookies HttpOnly seguros
      const loginResponse = NextResponse.json({
        success: true,
        message: 'Login realizado com sucesso',
        access_token: token, // Adicionar token na resposta
        user: {
          id: admin.id,
          username: admin.username,
          role: 'admin',
          full_name: admin.full_name
        }
      });

      // Definir cookie de autenticação (2 horas para coincidir com o token)
          loginResponse.cookies.set('access_token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 2 * 60 * 60 * 1000, // 2 horas (coincide com token)
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
            maxAge: 2 * 60 * 60 * 1000, // 2 horas (coincide com token)
            path: '/'
          });

      return loginResponse;

    } finally {
      client.release();
    }

  } catch (error: any) {
    debugLog.error('Erro geral na API route de login:', error.message);
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    );
  }
}

// Método GET não permitido para segurança
export async function GET() {
  return NextResponse.json(
    { error: 'Método não permitido' },
    { status: 405 }
  );
}
