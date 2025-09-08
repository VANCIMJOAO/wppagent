import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const isDev = process.env.NODE_ENV === 'development';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  if (isDev) console.log('Middleware: Verificando rota:', pathname)
  
  // Pular verificações para arquivos estáticos e API
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.') ||
    pathname === '/favicon.ico'
  ) {
    if (isDev) console.log('Middleware: Pulando verificação para arquivo estático/API')
    return NextResponse.next();
  }
  
  // Verificar se existe um token de autenticação
  const isAuthenticated = request.cookies.get('auth-token')?.value;
  if (isDev) console.log('Middleware: Token existe:', !!isAuthenticated)
  
  // Rotas que requerem autenticação
  const protectedRoutes = ['/dashboard'];
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  
  if (isDev) console.log('Middleware: É rota protegida?', isProtectedRoute)
  
  // Se não está autenticado e tenta acessar rota protegida
  if (!isAuthenticated && isProtectedRoute) {
    if (isDev) console.log('Middleware: Redirecionando para login (não autenticado)')
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // Se está autenticado e tenta acessar login
  if (isAuthenticated && pathname === '/login') {
    if (isDev) console.log('Middleware: Redirecionando para dashboard (já autenticado)')
    return NextResponse.redirect(new URL('/dashboard/dashboard', request.url));
  }
  
  if (isDev) console.log('Middleware: Permitindo acesso')
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};