import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // Proxy para a API de agendamentos
  return NextResponse.json({ 
    appointments: [],
    message: 'Endpoint de agendamentos - implementar proxy se necessário'
  });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  
  return NextResponse.json({ 
    success: true,
    message: 'Agendamento criado - implementar proxy se necessário',
    data: body
  });
}