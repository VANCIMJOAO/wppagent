import { NextRequest, NextResponse } from 'next/server';
import { Pool } from 'pg';
import { debugLog } from '@/lib/debug';

// Force dynamic rendering for this route since it uses cookies
export const dynamic = 'force-dynamic';

// Configuração do banco PostgreSQL
const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://postgres:UGARTPCwAADBBeBLctoRnQXLsoUvLJxz@caboose.proxy.rlwy.net:13910/railway',
  ssl: {
    rejectUnauthorized: false
  }
});

export async function GET(request: NextRequest) {
  let client;
  
  try {
    debugLog.info('🔍 API Services: Buscando dados reais do PostgreSQL');

    // ✅ Extrair token do cookie HTTP-only para validação
    const authToken = request.cookies.get('access_token')?.value;
    debugLog.info('🔍 Token encontrado no cookie:', authToken ? 'Sim' : 'Não');

    if (!authToken) {
      debugLog.error('Token não encontrado');
      return NextResponse.json(
        { error: 'Token de autenticação não encontrado' },
        { status: 401 }
      );
    }

    // ✅ Extrair query params
    const searchParams = request.nextUrl.searchParams;
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');
    const search = searchParams.get('search');

    debugLog.info('📊 Parâmetros:', { limit, offset, search });

    client = await pool.connect();
    
    // Query para buscar serviços
    let servicesQuery = `
      SELECT 
        s.id,
        s.name,
        s.description,
        s.duration_minutes,
        s.price,
        s.is_active,
        s.created_at,
        COUNT(DISTINCT a.id) as total_appointments
      FROM services s
      LEFT JOIN appointments a ON s.id = a.service_id
    `;

    const conditions = [];
    const params = [];
    let paramCount = 0;

    // Aplicar filtro de busca
    if (search) {
      paramCount++;
      conditions.push(`(s.name ILIKE $${paramCount} OR s.description ILIKE $${paramCount})`);
      params.push(`%${search}%`);
    }

    // Apenas serviços ativos
    paramCount++;
    conditions.push(`s.is_active = $${paramCount}`);
    params.push(true);

    if (conditions.length > 0) {
      servicesQuery += ` WHERE ${conditions.join(' AND ')}`;
    }

    servicesQuery += `
      GROUP BY s.id, s.name, s.description, s.duration_minutes, s.price, s.is_active, s.created_at
      ORDER BY s.name ASC
      LIMIT $${paramCount + 1} OFFSET $${paramCount + 2}
    `;
    
    params.push(limit, offset);

    debugLog.info('🔍 Executando query de serviços...');
    const servicesResult = await client.query(servicesQuery, params);
    
    // Buscar total de serviços para paginação
    let totalQuery = `SELECT COUNT(*) as total FROM services s WHERE s.is_active = true`;
    const totalParams = [];
    let totalParamCount = 0;

    if (search) {
      totalParamCount++;
      totalQuery += ` AND (s.name ILIKE $${totalParamCount} OR s.description ILIKE $${totalParamCount})`;
      totalParams.push(`%${search}%`);
    }

    const totalResult = await client.query(totalQuery, totalParams);
    const total = parseInt(totalResult.rows[0].total);

    // Formatear resposta
    const services = servicesResult.rows.map(row => ({
      id: row.id,
      name: row.name,
      description: row.description,
      duration_minutes: parseInt(row.duration_minutes) || 60,
      price: parseFloat(row.price) || 0,
      is_active: row.is_active,
      created_at: row.created_at,
      total_appointments: parseInt(row.total_appointments) || 0,
    }));

    debugLog.info(`✅ Encontrados ${services.length} serviços de ${total} totais`);

    const responseData = {
      services,
      total,
      limit,
      offset,
      has_more: (offset + services.length) < total,
    };

    return NextResponse.json(responseData, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      },
    });

  } catch (error) {
    debugLog.error('Erro na API services:', error);
    return NextResponse.json(
      { error: 'Erro interno do servidor' },
      { status: 500 }
    );
  } finally {
    if (client) {
      client.release();
    }
  }
}
