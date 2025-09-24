import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

const isDev = process.env.NODE_ENV === 'development';

// Função para verificar se o JWT é válido
async function verifyJWT(token: string): Promise<boolean> {
  try {
    const secret = new TextEncoder().encode(process.env.JWT_SECRET || 'whatsapp_agent_super_secret_2024_railway_production');
    await jwtVerify(token, secret);
    return true;
  } catch (error) {
    if (isDev) console.log('Middleware: JWT inválido:', error);
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (isDev) console.log('Middleware: Verificando rota:', pathname)

  // ✅ Intercepção especial para rotas de proxy - adicionar token automaticamente
  if (pathname.startsWith('/api/proxy/')) {
    if (isDev) console.log('Middleware: Interceptando rota de proxy')

    // Obter o token de autenticação - ✅ CORRIGIDO: Usar access_token
    const authToken = request.cookies.get('access_token')?.value;

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

  // Verificar se existe um token de autenticação e se é válido
  const authToken = request.cookies.get('access_token')?.value;
  let isAuthenticated = false;
  
  if (authToken) {
    // Verificar se o JWT é válido
    isAuthenticated = await verifyJWT(authToken);
    if (isDev) console.log('Middleware: Token válido:', isAuthenticated)
  } else {
    if (isDev) console.log('Middleware: Sem token, usuário não autenticado')
  }
  
  if (isDev) console.log('Middleware: Status de autenticação:', isAuthenticated)

  // ✅ Exceções para páginas de debug e fix - permitir acesso sem autenticação
  if (pathname === '/dashboard-debug' || pathname === '/simple-debug' || pathname === '/debug-token' || pathname === '/fix-loop.html' || pathname === '/ultimate-fix.html' || pathname === '/emergency-stop.html' || pathname === '/stop-loop-now.html' || pathname === '/stop-loop-simple.html') {
    if (isDev) console.log('Middleware: Permitindo acesso à página de debug/fix/emergency/stop-loop')
    return NextResponse.next();
  }

  // Rotas que requerem autenticação
  const protectedRoutes = ['/dashboard', '/conversas', '/agendamentos', '/monitoring'];
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));

  if (isDev) console.log('Middleware: É rota protegida?', isProtectedRoute)

  // Se não está autenticado e tenta acessar rota protegida
  if (!isAuthenticated && isProtectedRoute) {
    if (isDev) console.log('Middleware: Redirecionando para login (não autenticado)')
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // ✅ CORREÇÃO: Permitir acesso a /login mesmo com token presente
  // O auth-context irá validar se o token é válido e redirecionar se necessário
  if (isAuthenticated && pathname === '/login') {
    if (isDev) console.log('Middleware: Token presente, mas permitindo acesso a /login para validação pelo auth-context')
    // Não redirecionar automaticamente - deixar auth-context validar
    return NextResponse.next();
  }

  if (isDev) console.log('Middleware: Permitindo acesso')
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
