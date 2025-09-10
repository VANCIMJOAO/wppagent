/**
 * Backend Diagnostics API - Mapeia endpoints disponíveis no Railway
 * Solução profissional para identificar problemas de integração
 */
import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'https://wppagent-production.up.railway.app';
const ADMIN_USERNAME = 'admin';
const ADMIN_PASSWORD = 'senha_admin_segura';

async function getAuthToken(): Promise<string> {
  const loginResponse = await fetch(`${BACKEND_URL}/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: ADMIN_USERNAME,
      password: ADMIN_PASSWORD
    }),
    signal: AbortSignal.timeout(10000)
  });

  if (!loginResponse.ok) {
    throw new Error(`Login failed: ${loginResponse.status}`);
  }

  const loginData = await loginResponse.json();
  return loginData.access_token;
}

export async function GET() {
  try {
    console.log('🔍 Starting comprehensive backend diagnostics...');
    
    // Get auth token
    const token = await getAuthToken();
    console.log('✅ Authentication successful');

    // Test comprehensive endpoint list
    const endpointsToTest = [
      // Admin endpoints
      { path: '/admin/status', method: 'GET' },
      { path: '/admin/dashboard', method: 'GET' },
      { path: '/admin/metrics', method: 'GET' },
      { path: '/admin/health', method: 'GET' },
      
      // API endpoints - GET
      { path: '/api/status', method: 'GET' },
      { path: '/api/health', method: 'GET' },
      { path: '/api/customers', method: 'GET' },
      { path: '/api/leads', method: 'GET' },
      { path: '/api/appointments', method: 'GET' },
      { path: '/api/messages', method: 'GET' },
      
      // Direct resource endpoints - GET
      { path: '/customers', method: 'GET' },
      { path: '/leads', method: 'GET' },
      { path: '/appointments', method: 'GET' },
      { path: '/messages', method: 'GET' },
      
      // Try with query parameters
      { path: '/customers?limit=1', method: 'GET' },
      { path: '/leads?limit=1', method: 'GET' },
      
      // POST attempts
      { path: '/api/customers/search', method: 'POST', body: { limit: 1 } },
      { path: '/api/leads/search', method: 'POST', body: { limit: 1 } },
    ];

    const results: any[] = [];
    const successful: any[] = [];
    const errors: any[] = [];

    for (const endpoint of endpointsToTest) {
      try {
        console.log(`🧪 Testing ${endpoint.method} ${endpoint.path}`);
        
        const options: RequestInit = {
          method: endpoint.method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          signal: AbortSignal.timeout(8000)
        };

        if (endpoint.body) {
          options.body = JSON.stringify(endpoint.body);
        }

        const response = await fetch(`${BACKEND_URL}${endpoint.path}`, options);
        
        const result = {
          endpoint: `${endpoint.method} ${endpoint.path}`,
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries()),
          success: response.ok
        };

        // Try to get response body (limited to avoid huge responses)
        try {
          const text = await response.text();
          if (text.length < 2000) {
            try {
              result.body = JSON.parse(text);
            } catch {
              result.body = text;
            }
          } else {
            result.body = `[Large response: ${text.length} chars] ${text.substring(0, 200)}...`;
          }
        } catch {
          result.body = '[Unable to read response body]';
        }

        results.push(result);
        
        if (response.ok) {
          successful.push(result);
          console.log(`✅ SUCCESS: ${endpoint.method} ${endpoint.path} -> ${response.status}`);
        } else {
          errors.push(result);
          console.log(`❌ FAILED: ${endpoint.method} ${endpoint.path} -> ${response.status} ${response.statusText}`);
        }
        
      } catch (error: any) {
        const errorResult = {
          endpoint: `${endpoint.method} ${endpoint.path}`,
          error: error.message,
          success: false
        };
        
        results.push(errorResult);
        errors.push(errorResult);
        console.log(`💥 ERROR: ${endpoint.method} ${endpoint.path} -> ${error.message}`);
      }
    }

    // Summary
    const summary = {
      total_tested: endpointsToTest.length,
      successful_endpoints: successful.length,
      failed_endpoints: errors.length,
      success_rate: Math.round((successful.length / endpointsToTest.length) * 100),
      authentication_status: 'SUCCESS',
      backend_url: BACKEND_URL
    };

    console.log(`📊 Diagnostics complete: ${successful.length}/${endpointsToTest.length} endpoints working`);

    return NextResponse.json({
      success: true,
      summary,
      successful_endpoints: successful,
      failed_endpoints: errors,
      all_results: results,
      recommendations: generateRecommendations(successful, errors)
    });

  } catch (error: any) {
    console.error('❌ Diagnostics failed:', error.message);
    return NextResponse.json(
      { 
        success: false, 
        error: error.message,
        authentication_status: error.message.includes('Login failed') ? 'FAILED' : 'SUCCESS',
        backend_url: BACKEND_URL
      },
      { status: 500 }
    );
  }
}

function generateRecommendations(successful: any[], errors: any[]): string[] {
  const recommendations: string[] = [];
  
  if (successful.length === 0) {
    recommendations.push('❌ CRITICAL: No endpoints are working. Backend may be down or misconfigured.');
    recommendations.push('🔧 Check Railway service logs and deployment status');
    recommendations.push('🔧 Verify backend is properly deployed and running');
  } else if (successful.length < 3) {
    recommendations.push('⚠️ WARNING: Very few endpoints working. Backend may have partial issues.');
    recommendations.push('🔧 Focus on using working endpoints for data retrieval');
  } else {
    recommendations.push('✅ GOOD: Multiple endpoints working. Use these for data integration.');
  }
  
  // Analyze error patterns
  const status500Count = errors.filter(e => e.status === 500).length;
  const status405Count = errors.filter(e => e.status === 405).length;
  const status404Count = errors.filter(e => e.status === 404).length;
  
  if (status500Count > 0) {
    recommendations.push(`🔧 ${status500Count} endpoints return 500 errors - Backend internal issues`);
  }
  
  if (status405Count > 0) {
    recommendations.push(`🔧 ${status405Count} endpoints return 405 - Wrong HTTP method, try different methods`);
  }
  
  if (status404Count > 0) {
    recommendations.push(`🔧 ${status404Count} endpoints return 404 - Endpoints don't exist, check API documentation`);
  }
  
  return recommendations;
}