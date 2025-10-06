import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';
import { logger } from './lib/logger';
import { debugLog } from './lib/debug';

const isDev = process.env.NODE_ENV === 'development';

// ✅ CORREÇÃO #2: Verificar JWT_SECRET no início, antes de qualquer uso
// Se não estiver configurado, a aplicação não deve continuar
const JWT_SECRET = process.env.JWT_SECRET;

if (!JWT_SECRET) {
  // 🚨 ERRO FATAL: JWT_SECRET não configurado
  debugLog.error('🚨🚨🚨 ERRO CRÍTICO: JWT_SECRET não está configurado!');
  debugLog.error('🚨 A aplicação não pode funcionar sem JWT_SECRET.');
  debugLog.error('🚨 Configure JWT_SECRET nas variáveis de ambiente.');
  throw new Error('FATAL: JWT_SECRET must be configured in environment variables');
}

// Validar que o secret tem comprimento mínimo seguro
if (JWT_SECRET.length < 32) {
  debugLog.error('🚨🚨🚨 ERRO CRÍTICO: JWT_SECRET muito curto!');
  debugLog.error('🚨 JWT_SECRET deve ter pelo menos 32 caracteres para segurança.');
  throw new Error('FATAL: JWT_SECRET must be at least 32 characters long');
}

debugLog.success('JWT_SECRET configurado e validado');

// Função para verificar se o JWT é válido
async function verifyJWT(token: string): Promise<boolean> {
  try {
    // 🔒 SECURITY: Não logar secrets ou tokens
    logger.debug('Middleware: Verificando JWT');
    
    // ✅ CORREÇÃO #2: JWT_SECRET já foi validado no topo do arquivo
    // Não precisa verificar novamente aqui
    const result = await jwtVerify(token, new TextEncoder().encode(JWT_SECRET));
    logger.debug('Middleware: JWT válido');
    return true;
  } catch (error) {
    // 🔒 SECURITY: Não logar detalhes do erro que podem expor informações sensíveis
    logger.debug('Middleware: JWT inválido');
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
    // 🔒 SECURITY: Logar apenas presença do token, não o valor
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
  
  // 🔒 SECURITY: Logar apenas presença do token, não o valor
  logger.debug('Middleware: Cookie access_token encontrado:', !!authToken);
  
  if (authToken) {
    // Verificar se o JWT é válido
    isAuthenticated = await verifyJWT(authToken);
    logger.debug('Middleware: Token válido:', isAuthenticated)
  } else {
    logger.debug('Middleware: Sem token, usuário não autenticado')
  }
  
  logger.debug('Middleware: Status de autenticação:', isAuthenticated)

  // ✅ CORREÇÃO #3: Simplificar lógica de redirecionamento
  
  // Rotas que requerem autenticação
  const protectedRoutes = [
    '/dashboard', 
    '/conversas', 
    '/agendamentos', 
    '/monitoring', 
    '/clientes', 
    '/analytics', 
    '/relatorios', 
    '/configuracoes', 
    '/perfil', 
    '/suporte', 
    '/horarios-bloqueados', 
    '/exportar-relatorios'
  ];
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));

  logger.debug('Middleware: É rota protegida?', isProtectedRoute)

  // Caso 1: Usuário NÃO autenticado tentando acessar rota protegida
  if (!isAuthenticated && isProtectedRoute) {
    logger.debug('Middleware: ❌ Não autenticado → Redirecionando para /login')
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Caso 2: Usuário autenticado tentando acessar /login
  if (isAuthenticated && pathname === '/login') {
    logger.debug('Middleware: ✅ Já autenticado → Redirecionando para /dashboard')
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // Caso 3: Acesso permitido (autenticado em rota protegida, ou rota pública)
  logger.debug('Middleware: ✅ Permitindo acesso')
  return NextResponse.next();
}

// ✅ CORREÇÃO #4: Matcher refinado para ser mais específico
// Aplica middleware apenas em rotas que realmente precisam de verificação de autenticação
export const config = {
  matcher: [
    // Rotas de dashboard (protegidas)
    '/dashboard/:path*',
    '/conversas/:path*',
    '/agendamentos/:path*',
    '/monitoring/:path*',
    '/clientes/:path*',
    '/analytics/:path*',
    '/relatorios/:path*',
    '/configuracoes/:path*',
    '/perfil/:path*',
    '/suporte/:path*',
    '/horarios-bloqueados/:path*',
    '/exportar-relatorios/:path*',
    '/admin/:path*',
    '/bloqueados/:path*',
    
    // Rotas de autenticação (redirecionamento)
    '/login',
    
    // Rotas de API que precisam de token injection (proxy)
    '/api/proxy/:path*',
  ],
};
