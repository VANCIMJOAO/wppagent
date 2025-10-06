import { NextRequest, NextResponse } from 'next/server';
import { debugLog } from '@/lib/debug';

// Force dynamic rendering for this route since it handles proxy requests
export const dynamic = 'force-dynamic';

const isDev = process.env.NODE_ENV === 'development';

// Backend URL - usar local durante desenvolvimento/testes
const BACKEND_URL = process.env.BACKEND_URL || (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : 'https://wppagent-production.up.railway.app');

export async function GET(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleProxyRequest(request, 'GET', path);
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleProxyRequest(request, 'POST', path);
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleProxyRequest(request, 'PUT', path);
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  return handleProxyRequest(request, 'DELETE', path);
}

async function handleProxyRequest(request: Request, method: string, pathSegments: string[]) {
  const url = new URL(request.url);
  const endpoint = '/' + pathSegments.join('/');
  const queryString = url.search;

  try {
    // Construir URL do backend
    const backendUrl = `${BACKEND_URL}${endpoint}${queryString}`;
    if (isDev) debugLog.info(`[Proxy] ${method} request to:`, backendUrl);

    // Extrair Authorization header
    const authHeader = request.headers.get('Authorization') || request.headers.get('authorization');
    if (isDev) debugLog.info('[Proxy] Authorization header presente:', !!authHeader);

    // Extrair cookies do frontend
    const cookieHeader = request.headers.get('Cookie');
    if (isDev) debugLog.info('[Proxy] Cookies present:', !!cookieHeader);

    if (authHeader && isDev) {
      debugLog.info('[Proxy] Authorization header preview:', authHeader.substring(0, 10) + '...');
    }

    // Preparar headers para o backend
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    // IMPORTANTE: Adicionar Authorization header se existir
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    // IMPORTANTE: Repassar cookies para o backend
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }

    // Preparar body para métodos que precisam
    let body: string | undefined = undefined;
    if (method !== 'GET' && method !== 'HEAD') {
      try {
        body = await request.text();
        if (isDev) debugLog.info('[Proxy] Request body length:', body?.length || 0);
      } catch (e) {
        debugLog.info('[Proxy] No body or error reading body');
      }
    }

    debugLog.info('[Proxy] Sending request with headers:', Object.keys(headers));

    // Fazer requisição para o backend
    const response = await fetch(backendUrl, {
      method,
      headers,
      body,
      // NÃO seguir redirects automaticamente para preservar headers
      redirect: 'manual'
    });

    debugLog.info(`[Proxy] Backend response status:`, response.status);

    // Tratar redirect 307/308 manualmente
    if (response.status === 307 || response.status === 308) {
      const locationHeader = response.headers.get('location');
      if (locationHeader) {
        debugLog.info(`[Proxy] Following redirect to:`, locationHeader);

        // Refazer requisição com mesmos headers
        const redirectResponse = await fetch(locationHeader, {
          method,
          headers, // Manter os mesmos headers incluindo Authorization
          body,
        });

        const contentType = redirectResponse.headers.get('content-type');
        let data;

        try {
          if (contentType && contentType.includes('application/json')) {
            data = await redirectResponse.json();
          } else {
            data = await redirectResponse.text();
          }
        } catch (e) {
          debugLog.error('[Proxy] Error parsing redirect response:', e);
          data = { error: 'Failed to parse response' };
        }

        debugLog.info(`[Proxy] Redirect response status:`, redirectResponse.status);

        // Extrair cookies Set-Cookie do redirect também
        const redirectSetCookie = redirectResponse.headers.get('set-cookie');
        const redirectHeaders: HeadersInit = {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        };

        if (redirectSetCookie) {
          redirectHeaders['Set-Cookie'] = redirectSetCookie;
        }

        return NextResponse.json(data, {
          status: redirectResponse.status,
          headers: redirectHeaders
        });
      }
    }

    // Processar resposta normal
    const contentType = response.headers.get('content-type');
    let data;

    try {
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const textData = await response.text();
        // Tentar fazer parse como JSON se possível
        try {
          data = JSON.parse(textData);
        } catch {
          data = textData;
        }
      }
    } catch (e) {
      debugLog.error('[Proxy] Error parsing response:', e);
      data = { error: 'Failed to parse response from backend' };
    }

    // Log de debug para respostas de erro
    if (response.status >= 400) {
      debugLog.error(`[Proxy] Error response ${response.status}:`, data);
    }

    // Extrair cookies Set-Cookie do backend para repassar
    const setCookieHeader = response.headers.get('set-cookie');
    const responseHeaders: Record<string, string | string[]> = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Repassar cookies Set-Cookie se existirem
    if (setCookieHeader) {
      responseHeaders['Set-Cookie'] = setCookieHeader;
      if (isDev) debugLog.info('[Proxy] Repassing Set-Cookie to frontend');
    }

    // ✅ DETECÇÃO ESPECIAL PARA LOGIN: Extrair token e definir cookie local
    if (method === 'POST' && endpoint.includes('/admin/login') && response.status === 200 && data?.success && data?.data?.access_token) {
      if (isDev) debugLog.info('[Proxy] Login detectado - extraindo token e definindo cookie');
      
      const token = data.data.access_token;
      // ✅ CORRIGIDO: Usar o mesmo nome de cookie que o backend espera
      const cookieValue = `access_token=${token}; HttpOnly; Secure=${process.env.NODE_ENV === 'production'}; SameSite=Strict; Path=/; Max-Age=3600`;
      
      // Adicionar ao Set-Cookie existente ou criar novo
      if (responseHeaders['Set-Cookie']) {
        const existingCookie = responseHeaders['Set-Cookie'];
        responseHeaders['Set-Cookie'] = Array.isArray(existingCookie) 
          ? [...existingCookie, cookieValue]
          : [existingCookie, cookieValue];
      } else {
        responseHeaders['Set-Cookie'] = cookieValue;
      }
      
      if (isDev) debugLog.info('[Proxy] Cookie access_token definido com sucesso');
    }

    return NextResponse.json(data, {
      status: response.status,
      headers: responseHeaders as HeadersInit
    });

  } catch (error) {
    debugLog.error('[Proxy] Fatal error:', error);
    return NextResponse.json({
      error: 'Proxy error',
      message: error instanceof Error ? error.message : 'Unknown error',
      details: `Failed to fetch data from backend`
    }, {
      status: 500,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      }
    });
  }
}

// Handle OPTIONS requests for CORS
export async function OPTIONS(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}
