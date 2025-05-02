// src/middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const PROTECTED = [
  '/home',
  '/library',
  '/documents',
  '/advisors',
  '/settings',
]

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl
  const token = req.cookies.get('token')?.value

  if (PROTECTED.some(p => pathname === p || pathname.startsWith(p + '/')) && !token) {
    const loginUrl = req.nextUrl.clone()
    loginUrl.pathname = '/signin'
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: PROTECTED.map(p => `${p}/:path*`).concat(PROTECTED),
}
