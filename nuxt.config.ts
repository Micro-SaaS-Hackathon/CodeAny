import { defineNuxtConfig } from 'nuxt/config'
// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  modules: ['@nuxt/ui'],
  css: ['~/assets/css/main.css'],
  devServer: {
    port: 3010,
    host: '0.0.0.0'
  },
  ui: {
    colorMode: false,
    theme: {
      defaultVariants: {
        color: 'primary',
        size: 'md'
      }
    }
  },
  typescript: {
    strict: true
  },
  // Ensure we ship a single public-facing landing page for now
  routeRules: {
    '/**': { prerender: true }
  },
  compatibilityDate: '2024-09-01'
})
