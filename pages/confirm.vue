<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useSupabaseClient, useToast, navigateTo } from '#imports'

const route = useRoute()
const supabase = useSupabaseClient()
const toast = useToast()

onMounted(async () => {
  const code = route.query.code as string | undefined
  const error = route.query.error as string | undefined
  const errorDescription = route.query.error_description as string | undefined

  if (error || errorDescription) {
    toast.add({
      title: 'Authentication failed',
      description: errorDescription || error || 'Unknown error',
      color: 'error',
      icon: 'i-lucide-alert-triangle'
    })
    return navigateTo('/auth')
  }

  if (!code) {
    toast.add({ title: 'Missing code', description: 'No code found in the URL.', color: 'warning', icon: 'i-lucide-info' })
    return navigateTo('/auth')
  }

  try {
    const { error: exErr } = await supabase.auth.exchangeCodeForSession(code)
    if (exErr) throw exErr

    toast.add({ title: 'Signed in', description: 'Your account is confirmed. Welcome!', color: 'success', icon: 'i-lucide-badge-check' })
    navigateTo('/')
  } catch (e: any) {
    toast.add({ title: 'Auth exchange failed', description: e.message ?? String(e), color: 'error', icon: 'i-lucide-alert-triangle' })
    navigateTo('/auth')
  }
})
</script>

<template>
  <main class="bg-default text-default min-h-screen">
    <UContainer class="py-10">
      <div class="max-w-md mx-auto">
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-shield-check" class="text-primary" aria-hidden="true" />
              <h1 class="text-h3 text-highlighted">Confirming…</h1>
            </div>
          </template>
          <div class="space-y-3">
            <USkeleton class="h-4 w-2/3" />
            <USkeleton class="h-4 w-1/2" />
          </div>
        </UCard>
      </div>
    </UContainer>
  </main>
</template>
