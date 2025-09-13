import { defineEventHandler, sendRedirect, getRequestURL } from 'h3'
import { serverSupabaseUser } from '#supabase/server'

// Server-side redirects to keep SSR and client in sync
export default defineEventHandler(async (event) => {
  const { pathname } = getRequestURL(event)

  // Skip non-HTML requests (assets, APIs, etc.)
  const accept = event.node.req.headers.accept || ''
  if (!accept.includes('text/html')) return

  // Do not SSR-redirect /app/**; these routes are client-rendered
  if (pathname.startsWith('/app')) return

  // For specific public entry points, check auth to optionally redirect
  if (pathname === '/' || pathname === '/auth' || pathname === '/confirm') {
    let user: any = null
    try {
      user = await serverSupabaseUser(event)
    } catch (_err) {
      user = null
    }
    if (user) {
      return sendRedirect(event, '/app/dashboard')
    }
  }
})
