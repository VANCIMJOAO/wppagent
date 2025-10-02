import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';
import { logger } from './lib/logger';

const isDev = process.env.NODE_ENV === 'development';

// Função para verificar se o JWT é válido
async function verifyJWT(token: string): Promise<boolean> {
  try {
    const secret = process.env.JWT_SECRET;
  if (!secret) {
    console.error('🚨 JWT_SECRET não configurado!');
    throw new Error('JWT_SECRET must be configured');
  }
    logger.debug('Middleware: Verificando JWT com secret:', secret);
    logger.debug('Middleware: Token preview:', token.substring(0, 20) + '...');
    
    const result = await jwtVerify(token, new TextEncoder().encode(secret));
    logger.debug('Middleware: JWT válido, payload:', result.payload);
    return true;
  } catch (error) {
    logger.debug('Middleware: JWT inválido:', error);
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  logger.debug('Middleware: Verificando rota:', pathname)

  // ✅ Intercepção especial para rotas de proxy - adicionar token automaticamente
  if (pathname.startsWith('/api/proxy/')) {
    logger.debug('Middleware: Interceptando rota de proxy')

    // Obter o token de autenticação - ✅ CORRIGIDO: Usar access_token
    const authToken = request.cookies.get('access_token')?.value;
    logger.debug('Middleware: Token encontrado:', !!authToken);

    if (authToken) {
      logger.debug('Middleware: Adicionando token ao header de autorização')

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
      logger.debug('Middleware: Token não encontrado para proxy')
    }
  }

  // Pular verificações para arquivos estáticos e outras APIs
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.') ||
    pathname === '/favicon.ico'
  ) {
    logger.debug('Middleware: Pulando verificação para arquivo estático/API')
    return NextResponse.next();
  }

  // Verificar se existe um token de autenticação e se é válido
  const authToken = request.cookies.get('access_token')?.value;
  let isAuthenticated = false;
  
  logger.debug('Middleware: Cookie access_token encontrado:', !!authToken);
  if (isDev && authToken) console.log('Middleware: Token preview:', authToken.substring(0, 20) + '...');
  
  if (authToken) {
    // Verificar se o JWT é válido
    isAuthenticated = await verifyJWT(authToken);
    logger.debug('Middleware: Token válido:', isAuthenticated)
  } else {
    logger.debug('Middleware: Sem token, usuário não autenticado')
  }
  
  logger.debug('Middleware: Status de autenticação:', isAuthenticated)

  // ✅ SECURITY FIX: Removidas exceções para páginas de debug - todas páginas precisam de autenticação

  // Rotas que requerem autenticação
  const protectedRoutes = ['/dashboard', '/conversas', '/agendamentos', '/monitoring', '/clientes', '/analytics', '/relatorios', '/configuracoes', '/perfil', '/suporte', '/horarios-bloqueados', '/exportar-relatorios'];
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));

  logger.debug('Middleware: É rota protegida?', isProtectedRoute)

  // Se não está autenticado e tenta acessar rota protegida
  if (!isAuthenticated && isProtectedRoute) {
    logger.debug('Middleware: Redirecionando para login (não autenticado)')
    logger.debug('Middleware: Cookies disponíveis:', request.cookies.getAll().map(c => c.name));
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // ✅ CORREÇÃO: Permitir acesso a /login mesmo com token presente
  // O auth-context irá validar se o token é válido e redirecionar se necessário
  if (isAuthenticated && pathname === '/login') {
    logger.debug('Middleware: Token presente, mas permitindo acesso a /login para validação pelo auth-context')
    // Não redirecionar automaticamente - deixar auth-context validar
    return NextResponse.next();
  }

  logger.debug('Middleware: Permitindo acesso')
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
