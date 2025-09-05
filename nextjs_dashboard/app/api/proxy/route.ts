import { NextResponse } from 'next/server';

// Handle any HTTP method at /api/proxy/*
export async function GET(request: Request) {
  return handleProxyRequest(request, 'GET');
}

export async function POST(request: Request) {
  return handleProxyRequest(request, 'POST');
}

export async function PUT(request: Request) {
  return handleProxyRequest(request, 'PUT');
}

export async function DELETE(request: Request) {
  return handleProxyRequest(request, 'DELETE');
}

async function handleProxyRequest(request: Request, method: string) {
  const url = new URL(request.url);
  
  // Extract the endpoint path after /api/proxy
  const endpoint = url.pathname.replace('/api/proxy', '');
  const queryString = url.search;
  
  if (!endpoint || endpoint === '/') {
    return NextResponse.json({ error: 'Missing endpoint path' }, { status: 400 });
  }

  try {
    const backendUrl = `https://wppagent-production.up.railway.app${endpoint}${queryString}`;
    console.log('Proxy request to:', backendUrl);
    
    const requestBody = method !== 'GET' ? await request.text() : undefined;
    
    const response = await fetch(backendUrl, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('authorization') || '',
      },
      body: requestBody,
    });

    const contentType = response.headers.get('content-type');
    let data;
    
    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

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

export async function OPTIONS(request: Request) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
