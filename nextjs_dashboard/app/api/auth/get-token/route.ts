import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value
  
  return NextResponse.json({ token: token || null })
}
