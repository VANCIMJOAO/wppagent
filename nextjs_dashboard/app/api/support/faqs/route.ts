import { NextRequest, NextResponse } from 'next/server';
import { executeQuery } from '@/lib/database';

export async function GET(request: NextRequest) {
  try {
    console.log('📚 Buscando FAQs do PostgreSQL...');

    const searchParams = request.nextUrl.searchParams;
    const category = searchParams.get('category') || '';

    let whereClause = '';
    let queryParams: any[] = [];

    if (category) {
      whereClause = 'WHERE category = $1';
      queryParams.push(category);
    }

    const faqsQuery = `
      SELECT
        id,
        question,
        answer,
        category,
        created_at,
        updated_at,
        is_active
      FROM support_faqs
      ${whereClause}
      ORDER BY created_at DESC
    `;

    const faqs = await executeQuery(faqsQuery, queryParams);

    const formattedFAQs = faqs.map(faq => ({
      id: faq.id,
      question: faq.question,
      answer: faq.answer,
      category: faq.category,
      created_at: faq.created_at,
      updated_at: faq.updated_at,
      is_active: faq.is_active
    }));

    console.log(`✅ Encontrados ${formattedFAQs.length} FAQs`);

    return NextResponse.json({
      success: true,
      data: formattedFAQs,
      faqs: formattedFAQs // For compatibility
    });

  } catch (error) {
    console.error('❌ Erro ao buscar FAQs:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Erro interno do servidor',
        details: error instanceof Error ? error.message : 'Erro desconhecido',
        data: []
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    console.log('📝 Criando novo FAQ...');

    const body = await request.json();
    const { question, answer, category } = body;

    if (!question || !answer || !category) {
      return NextResponse.json(
        {
          success: false,
          error: 'Campos obrigatórios: question, answer, category'
        },
        { status: 400 }
      );
    }

    const insertQuery = `
      INSERT INTO support_faqs (question, answer, category, is_active, created_at, updated_at)
      VALUES ($1, $2, $3, true, NOW(), NOW())
      RETURNING id, question, answer, category, created_at, updated_at, is_active
    `;

    const result = await executeQuery(insertQuery, [question, answer, category]);

    if (result.length === 0) {
      throw new Error('Falha ao criar FAQ');
    }

    const newFAQ = result[0];

    console.log(`✅ FAQ criado com ID: ${newFAQ.id}`);

    return NextResponse.json({
      success: true,
      data: newFAQ,
      message: 'FAQ criado com sucesso'
    });

  } catch (error) {
    console.error('❌ Erro ao criar FAQ:', error);
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
