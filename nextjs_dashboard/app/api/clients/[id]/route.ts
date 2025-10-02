import { NextRequest, NextResponse } from 'next/server';

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const resolvedParams = await params;
    const clientId = resolvedParams.id;
    const body = await request.json();
    const { nome, telefone, email, status, notas } = body;

    console.log(`👤 Atualizando cliente ${clientId}...`);

    // Fazer requisição para o backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/clients/${clientId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('Authorization') || '',
      },
      body: JSON.stringify({
        nome,
        telefone,
        email,
        status,
        notas
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro ao atualizar cliente');
    }

    const result = await response.json();
    console.log('✅ Cliente atualizado:', result);

    return NextResponse.json({
      success: true,
      data: result,
      message: 'Cliente atualizado com sucesso'
    });

  } catch (error) {
    console.error('❌ Erro ao atualizar cliente:', error);
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

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const resolvedParams = await params;
    const clientId = resolvedParams.id;

    console.log(`🗑️ Excluindo cliente ${clientId}...`);

    // Fazer requisição para o backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/clients/${clientId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': request.headers.get('Authorization') || '',
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erro ao excluir cliente');
    }

    const result = await response.json();
    console.log('✅ Cliente excluído:', result);

    return NextResponse.json({
      success: true,
      data: result,
      message: 'Cliente excluído com sucesso'
    });

  } catch (error) {
    console.error('❌ Erro ao excluir cliente:', error);
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



