import { defineNuxtConfig } from 'nuxt/config'
// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: [
    '@nuxt/ui',
    ['@nuxtjs/supabase', {
      url: process.env.SUPABASE_PROJECT_URL,
      key: process.env.SUPABASE_API_KEY,
      redirect: false,
      useSsrCookies: false,
      clientOptions: {
        auth: {
          flowType: 'pkce',
          detectSessionInUrl: true,
          persistSession: true
        }
      },
      redirectOptions: {
        login: '/auth',
        callback: '/confirm'
      }
    }]
  ],
  css: ['~/assets/css/main.css'],
  devServer: {
    port: 3010,
    host: '0.0.0.0'
  },
  // @ts-expect-error: Provided by @nuxt/ui module schema at runtime
  ui: {
    colorMode: false,
    theme: {
      defaultVariants: {
        color: 'primary',
        size: 'md'
      }
    }
  },
  runtimeConfig: {
    public: {
      supabase: {
        // Map your existing env names to what the module reads at runtime
        url: process.env.SUPABASE_PROJECT_URL,
        key: process.env.SUPABASE_API_KEY
      },
      // FastAPI backend base URL (used by composables)
      backendUrl: process.env.BACKEND_URL || 'http://localhost:8000'
    }
  },
  typescript: {
    strict: true
  },
  // Marketing pages remain prerendered; auth routes run dynamically
  routeRules: {
    '/auth': { prerender: false },
    '/confirm': { prerender: false },
    // Ensure all Teacher Hub routes render on client only
    '/app/**': { prerender: false, ssr: false },
    '/**': { prerender: true }
  },
  compatibilityDate: '2024-09-01'
})
