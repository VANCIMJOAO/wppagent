import { NextResponse } from 'next/server';

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
    const backendUrl = `https://wppagent-production.up.railway.app${endpoint}${queryString}`;
    console.log(`Proxy ${method} request to:`, backendUrl);
    
    const authHeader = request.headers.get('Authorization') || request.headers.get('authorization') || '';
    console.log('Authorization header received:', authHeader ? `${authHeader.substring(0, 50)}... (length: ${authHeader.length})` : 'None');
    console.log('Full Authorization header:', authHeader);
    
    const requestBody = method !== 'GET' ? await request.text() : undefined;
    
    const response = await fetch(backendUrl, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authHeader,
      },
      body: requestBody,
      redirect: 'manual', // Lidar com redirects manualmente
    });

    // Se recebeu redirect 307, seguir manualmente preservando headers
    if (response.status === 307) {
      const locationHeader = response.headers.get('location');
      if (locationHeader) {
        console.log(`🔄 Following redirect to: ${locationHeader}`);
        const redirectResponse = await fetch(locationHeader, {
          method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': authHeader, // Preservar Authorization header
          },
          body: requestBody,
        });
        
        const contentType = redirectResponse.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
          data = await redirectResponse.json();
        } else {
          data = await redirectResponse.text();
        }

        console.log(`Redirect response ${redirectResponse.status}:`, data);
        return NextResponse.json(data, { 
          status: redirectResponse.status,
          headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
          }
        });
      }
    }

    const contentType = response.headers.get('content-type');
    let data;
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    console.log(`Backend response ${response.status}:`, data);

    return NextResponse.json(data, { 
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      }
    });

  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json({ 
      error: `Failed to fetch data from backend: ${error}` 
    }, { status: 500 });
  }
}

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
    },
  });
}
