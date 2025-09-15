import { NextRequest, NextResponse } from 'next/server';

// Force dynamic rendering for this route since it handles proxy requests
export const dynamic = 'force-dynamic';

const isDev = process.env.NODE_ENV === 'development';

// Backend URL para Railway
const BACKEND_URL = process.env.BACKEND_URL || 'https://wppagent-production.up.railway.app';

export async function GET(
  request: Request,
  { params }: { params: { path: string[] } }
) {
  return handleProxyRequest(request, 'GET', params.path);
}

export async function POST(
  request: Request,
  { params }: { params: { path: string[] } }
) {
  return handleProxyRequest(request, 'POST', params.path);
}

export async function PUT(
  request: Request,
  { params }: { params: { path: string[] } }
) {
  return handleProxyRequest(request, 'PUT', params.path);
}

export async function DELETE(
  request: Request,
  { params }: { params: { path: string[] } }
) {
  return handleProxyRequest(request, 'DELETE', params.path);
}

async function handleProxyRequest(request: Request, method: string, pathSegments: string[]) {
  const url = new URL(request.url);
  const endpoint = '/' + pathSegments.join('/');
  const queryString = url.search;

  try {
    // Construir URL do backend
    const backendUrl = `${BACKEND_URL}${endpoint}${queryString}`;
    if (isDev) console.log(`[Proxy] ${method} request to:`, backendUrl);

    // Extrair Authorization header
    const authHeader = request.headers.get('Authorization') || request.headers.get('authorization');
    if (isDev) console.log('[Proxy] Authorization header presente:', !!authHeader);

    // Extrair cookies do frontend
    const cookieHeader = request.headers.get('Cookie');
    if (isDev) console.log('[Proxy] Cookies present:', !!cookieHeader);

    if (authHeader && isDev) {
      console.log('[Proxy] Authorization header preview:', authHeader.substring(0, 10) + '...');
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
        if (isDev) console.log('[Proxy] Request body length:', body?.length || 0);
      } catch (e) {
        console.log('[Proxy] No body or error reading body');
      }
    }

    console.log('[Proxy] Sending request with headers:', Object.keys(headers));

    // Fazer requisição para o backend
    const response = await fetch(backendUrl, {
      method,
      headers,
      body,
      // NÃO seguir redirects automaticamente para preservar headers
      redirect: 'manual'
    });

    console.log(`[Proxy] Backend response status:`, response.status);

    // Tratar redirect 307/308 manualmente
    if (response.status === 307 || response.status === 308) {
      const locationHeader = response.headers.get('location');
      if (locationHeader) {
        console.log(`[Proxy] Following redirect to:`, locationHeader);

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
          console.error('[Proxy] Error parsing redirect response:', e);
          data = { error: 'Failed to parse response' };
        }

        console.log(`[Proxy] Redirect response status:`, redirectResponse.status);

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
      console.error('[Proxy] Error parsing response:', e);
      data = { error: 'Failed to parse response from backend' };
    }

    // Log de debug para respostas de erro
    if (response.status >= 400) {
      console.error(`[Proxy] Error response ${response.status}:`, data);
    }

    // Extrair cookies Set-Cookie do backend para repassar
    const setCookieHeader = response.headers.get('set-cookie');
    const responseHeaders: HeadersInit = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Repassar cookies Set-Cookie se existirem
    if (setCookieHeader) {
      responseHeaders['Set-Cookie'] = setCookieHeader;
      if (isDev) console.log('[Proxy] Repassing Set-Cookie to frontend');
    }

    return NextResponse.json(data, {
      status: response.status,
      headers: responseHeaders
    });

  } catch (error) {
    console.error('[Proxy] Fatal error:', error);
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
  { params }: { params: { path: string[] } }
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
