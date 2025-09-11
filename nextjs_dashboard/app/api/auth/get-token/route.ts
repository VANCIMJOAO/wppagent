import { NextRequest, NextResponse } from 'next/server'

// Force dynamic rendering for this route since it uses cookies
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value
  
  return NextResponse.json({ token: token || null })
}
