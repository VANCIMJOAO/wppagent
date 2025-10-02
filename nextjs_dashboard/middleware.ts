import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

const isDev = process.env.NODE_ENV === 'development';

// Função para verificar se o JWT é válido
async function verifyJWT(token: string): Promise<boolean> {
  try {
    const secret = process.env.JWT_SECRET;
  if (!secret) {
    console.error('🚨 JWT_SECRET não configurado!');
    throw new Error('JWT_SECRET must be configured');
  }
    if (isDev) console.log('Middleware: Verificando JWT com secret:', secret);
    if (isDev) console.log('Middleware: Token preview:', token.substring(0, 20) + '...');
    
    const result = await jwtVerify(token, new TextEncoder().encode(secret));
    if (isDev) console.log('Middleware: JWT válido, payload:', result.payload);
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
    if (isDev) console.log('Middleware: Token encontrado:', !!authToken);

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
  
  if (isDev) console.log('Middleware: Cookie access_token encontrado:', !!authToken);
  if (isDev && authToken) console.log('Middleware: Token preview:', authToken.substring(0, 20) + '...');
  
  if (authToken) {
    // Verificar se o JWT é válido
    isAuthenticated = await verifyJWT(authToken);
    if (isDev) console.log('Middleware: Token válido:', isAuthenticated)
  } else {
    if (isDev) console.log('Middleware: Sem token, usuário não autenticado')
  }
  
  if (isDev) console.log('Middleware: Status de autenticação:', isAuthenticated)

  // ✅ SECURITY FIX: Removidas exceções para páginas de debug - todas páginas precisam de autenticação

  // Rotas que requerem autenticação
  const protectedRoutes = ['/dashboard', '/conversas', '/agendamentos', '/monitoring', '/clientes', '/analytics', '/relatorios', '/configuracoes', '/perfil', '/suporte', '/horarios-bloqueados', '/exportar-relatorios'];
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));

  if (isDev) console.log('Middleware: É rota protegida?', isProtectedRoute)

  // Se não está autenticado e tenta acessar rota protegida
  if (!isAuthenticated && isProtectedRoute) {
    if (isDev) console.log('Middleware: Redirecionando para login (não autenticado)')
    if (isDev) console.log('Middleware: Cookies disponíveis:', request.cookies.getAll().map(c => c.name));
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
