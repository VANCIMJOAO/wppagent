import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';

export async function GET(request: NextRequest) {
  try {
    console.log('🏢 Buscando configurações da empresa...');

    const companyQuery = `
      SELECT
        id,
        name,
        phone,
        email,
        address,
        description,
        business_hours,
        created_at,
        updated_at
      FROM businesses
      ORDER BY id
      LIMIT 1
    `;

    const companies = await executeQuery(companyQuery);

    if (companies.length === 0) {
      return NextResponse.json({
        success: true,
        data: {
          id: null,
          name: '',
          phone: '',
          email: '',
          address: '',
          description: '',
          business_hours: null,
          website: ''
        }
      });
    }

    const company = companies[0];

    const formattedCompany = {
      id: company.id,
      name: company.name || '',
      phone: company.phone || '',
      email: company.email || '',
      address: company.address || '',
      description: company.description || '',
      business_hours: company.business_hours,
      website: '', // Campo não existe na tabela, manter vazio
      created_at: company.created_at,
      updated_at: company.updated_at
    };

    console.log(`✅ Configurações da empresa carregadas: ${formattedCompany.name}`);

    return NextResponse.json({
      success: true,
      data: formattedCompany
    });

  } catch (error) {
    console.error('❌ Erro ao buscar configurações da empresa:', error);
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
    console.log('💾 Salvando configurações da empresa...');

    const body = await request.json();
    const { name, phone, email, address, description, website } = body;

    if (!name) {
      return NextResponse.json(
        {
          success: false,
          error: 'Nome da empresa é obrigatório'
        },
        { status: 400 }
      );
    }

    // Verificar se já existe uma empresa
    const existingQuery = 'SELECT id FROM businesses LIMIT 1';
    const existing = await executeQuery(existingQuery);

    let result;
    if (existing.length > 0) {
      // Atualizar empresa existente
      const updateQuery = `
        UPDATE businesses 
        SET 
          name = $1,
          phone = $2,
          email = $3,
          address = $4,
          description = $5,
          updated_at = NOW()
        WHERE id = $6
        RETURNING id, name, phone, email, address, description, updated_at
      `;
      
      result = await executeQuery(updateQuery, [
        name, phone, email, address, description, existing[0].id
      ]);
    } else {
      // Criar nova empresa
      const insertQuery = `
        INSERT INTO businesses (name, phone, email, address, description, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
        RETURNING id, name, phone, email, address, description, created_at, updated_at
      `;
      
      result = await executeQuery(insertQuery, [name, phone, email, address, description]);
    }

    if (result.length === 0) {
      throw new Error('Falha ao salvar configurações da empresa');
    }

    const savedCompany = result[0];

    console.log(`✅ Configurações da empresa salvas: ${savedCompany.name}`);

    return NextResponse.json({
      success: true,
      data: {
        id: savedCompany.id,
        name: savedCompany.name,
        phone: savedCompany.phone,
        email: savedCompany.email,
        address: savedCompany.address,
        description: savedCompany.description,
        website: website || '', // Campo não existe na tabela
        created_at: savedCompany.created_at,
        updated_at: savedCompany.updated_at
      },
      message: 'Configurações da empresa salvas com sucesso'
    });

  } catch (error) {
    console.error('❌ Erro ao salvar configurações da empresa:', error);
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
