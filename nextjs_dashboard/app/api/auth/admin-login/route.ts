/**
 * 🔐 API Route Segura para Login Admin
 * Autenticação local via PostgreSQL
 */

import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';

// Configuração do banco PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway',
  ssl: {
    rejectUnauthorized: false
  }
});

export async function POST(request: NextRequest) {
  try {
    console.log('🔐 Login admin via autenticação local PostgreSQL...');

    // Obter credenciais do body da requisição
    let username, password;
    try {
      const body = await request.json();
      username = body.username;
      password = body.password;
    } catch (jsonError) {
      console.error('❌ Erro ao fazer parse do JSON:', jsonError);
      return NextResponse.json(
        { error: 'Dados inválidos no corpo da requisição' },
        { status: 400 }
      );
    }

    if (!username || !password) {
      console.log('❌ Username ou password ausentes:', { username: !!username, password: !!password });
      return NextResponse.json(
        { error: 'Username e password são obrigatórios' },
        { status: 400 }
      );
    }

    console.log('🔍 Tentando login para usuário:', username);

    // Verificar credenciais na database
    let client;
    try {
      client = await pool.connect();
      console.log('✅ Conectado ao banco PostgreSQL');
    } catch (dbError) {
      console.error('❌ Erro ao conectar com o banco:', dbError);
      return NextResponse.json(
        { error: 'Erro de conexão com o banco de dados' },
        { status: 500 }
      );
    }
    
    try {
      // Buscar usuário admin na tabela admin_users
      const adminResult = await client.query(
        'SELECT id, username, password_hash, full_name, is_active FROM admin_users WHERE username = $1 AND is_active = true',
        [username]
      );

      if (adminResult.rows.length === 0) {
        console.log('❌ Usuário admin não encontrado:', username);
        return NextResponse.json(
          { error: 'Credenciais inválidas' },
          { status: 401 }
        );
      }

      const admin = adminResult.rows[0];
      console.log('✅ Usuário admin encontrado:', admin.username);

      // Verificar senha (usando bcrypt)
      const bcrypt = require('bcryptjs');
      const isValidPassword = await bcrypt.compare(password, admin.password_hash);

      if (!isValidPassword) {
        console.log('❌ Senha inválida para usuário:', username);
        return NextResponse.json(
          { error: 'Credenciais inválidas' },
          { status: 401 }
        );
      }

      console.log('✅ Login realizado com sucesso para:', admin.username);

      // ✅ CORREÇÃO: Fazer login no Railway para obter token real
      console.log('🚀 Fazendo login no Railway...');
      const railwayLoginResponse = await fetch('https://wppagent-production.up.railway.app/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: admin.username,
          password: password // Usar a senha original
        })
      });

      if (!railwayLoginResponse.ok) {
        console.error('❌ Erro ao fazer login no Railway:', railwayLoginResponse.status);
        const railwayError = await railwayLoginResponse.text();
        console.error('❌ Erro Railway:', railwayError);
        
        return NextResponse.json(
          { error: 'Erro ao autenticar com o servidor Railway' },
          { status: 500 }
        );
      }

      const railwayData = await railwayLoginResponse.json();
      console.log('✅ Login Railway realizado com sucesso');
      
      if (!railwayData.success || !railwayData.data?.access_token) {
        console.error('❌ Railway não retornou token válido:', railwayData);
        return NextResponse.json(
          { error: 'Token inválido do Railway' },
          { status: 500 }
        );
      }

      const token = railwayData.data.access_token;
      console.log('🔑 Token Railway obtido, length:', token.length);
      console.log('🔑 Token primeiros 50 chars:', token.substring(0, 50));

      // ✅ SEGURO: Definir cookies HttpOnly seguros
      const loginResponse = NextResponse.json({
        success: true,
        message: 'Login realizado com sucesso'
      });

      // Definir cookie de autenticação
          loginResponse.cookies.set('access_token', token, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 24 * 60 * 60 * 1000, // 24 horas
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
        tokenExpiry: Date.now() + (24 * 60 * 60 * 1000) // 24 horas
      };

          loginResponse.cookies.set('session-info', JSON.stringify(sessionInfo), {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
            maxAge: 24 * 60 * 60 * 1000, // 24 horas
            path: '/'
          });

      return loginResponse;

    } finally {
      client.release();
    }

  } catch (error: any) {
    console.error('❌ Erro geral na API route de login:', error.message);
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
