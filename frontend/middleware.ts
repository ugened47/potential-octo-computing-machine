import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = ['/dashboard', '/profile']

// Routes that should redirect authenticated users away
const authRoutes = ['/login', '/register', '/forgot-password', '/reset-password']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check if route is protected
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  )

  // Check if route is an auth route
  const isAuthRoute = authRoutes.some((route) => pathname.startsWith(route))

  // Get access token from cookie or header
  // Note: Since we're using localStorage, we can't access it in middleware
  // This middleware will mainly handle route structure
  // Actual auth check happens client-side via ProtectedRoute component
  const accessToken = request.cookies.get('access_token')?.value

  // For protected routes, we'll let the client-side ProtectedRoute handle auth
  // This middleware just ensures the route structure is correct
  if (isProtectedRoute && !accessToken) {
    // Redirect to login with returnUrl
    const returnUrl = encodeURIComponent(pathname)
    return NextResponse.redirect(
      new URL(`/login?returnUrl=${returnUrl}`, request.url)
    )
  }

  // For auth routes, if user is authenticated, redirect to dashboard
  // Note: This check is limited since we can't access localStorage in middleware
  // The client-side components handle this more reliably

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}

