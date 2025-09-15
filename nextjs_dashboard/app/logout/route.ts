import { NextResponse } from 'next/server';

export async function GET() {
  const response = NextResponse.redirect(new URL('/login', 'http://localhost:3000'));

  // Limpar o cookie de autenticação
  response.cookies.delete('auth-token');

  return response;
}
