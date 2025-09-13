import { defineNuxtRouteMiddleware, navigateTo } from '#app'
import { useSupabaseUser } from '#imports'

export default defineNuxtRouteMiddleware((to) => {
  // Only run on client where Supabase auth state is available
  if (process.server) return

  const user = useSupabaseUser()

  // If authenticated and going to public entry points, send to Teacher Hub
  if (user.value && (to.path === '/' || to.path === '/auth' || to.path === '/confirm')) {
    return navigateTo('/app/dashboard')
  }

  // Protect Teacher Hub routes
  if (!user.value && to.path.startsWith('/app')) {
    return navigateTo('/auth')
  }
})
