import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const isDev = process.env.NODE_ENV === 'development';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  if (isDev) console.log('Middleware: Verificando rota:', pathname)
  
  // ✅ Intercepção especial para rotas de proxy - adicionar token automaticamente
  if (pathname.startsWith('/api/proxy/')) {
    if (isDev) console.log('Middleware: Interceptando rota de proxy')
    
    // Obter o token de autenticação
    const authToken = request.cookies.get('auth-token')?.value;
    
    if (authToken) {
      if (isDev) console.log('Middleware: Adicionando token ao header de autorização')
      
      // Criar nova request com header de autorização
      const requestHeaders = new Headers(request.headers);
      requestHeaders.set('Authorization', `Bearer ${authToken}`);
      
      // Retornar com os headers modificados
      return NextResponse.next({
        request: {
          headers: requestHeaders,
        },
      });
    } else {
      if (isDev) console.log('Middleware: Token não encontrado para proxy')
    }
  }
  
  // Pular verificações para arquivos estáticos e outras APIs
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
  const protectedRoutes = ['/dashboard', '/conversas', '/agendamentos', '/monitoring'];
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