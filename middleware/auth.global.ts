import { defineNuxtRouteMiddleware, navigateTo } from '#app'
import { useSupabaseUser, useSupabaseClient } from '#imports'

// Client-side guard that waits for Supabase session before redirecting
export default defineNuxtRouteMiddleware(async (to) => {
  if (process.server) return

  const user = useSupabaseUser()
  const supabase = useSupabaseClient()

  // Public → app redirect when already authenticated
  if (to.path === '/' || to.path === '/auth' || to.path === '/confirm') {
    if (!user.value) {
      const { data } = await supabase.auth.getSession()
      if (data.session) user.value = data.session.user as any
    }
    if (user.value) return navigateTo('/app/dashboard')
    return
  }

  // Protect /app/** but wait for session to initialize once
  if (to.path.startsWith('/app')) {
    if (!user.value) {
      const { data } = await supabase.auth.getSession()
      if (data.session) user.value = data.session.user as any
    }
    if (!user.value) return navigateTo('/auth')
  }
})
