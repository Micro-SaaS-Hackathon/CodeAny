<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSupabaseClient, useSupabaseUser, useToast, navigateTo } from '#imports'

const supabase = useSupabaseClient()
const user = useSupabaseUser()
const toast = useToast()

const email = ref('')
const password = ref('')
const loadingSignUp = ref(false)
const loadingSignIn = ref(false)
const loadingGoogle = ref(false)

onMounted(() => {
  if (user.value) {
    navigateTo('/')
  }
})

function getConfirmRedirect() {
  // Build an absolute URL for Supabase redirect/magic link
  if (typeof window !== 'undefined' && window.location?.origin) {
    return new URL('/confirm', window.location.origin).toString()
  }
  return '/confirm'
}

async function onEmailSignUp() {
  loadingSignUp.value = true
  try {
    const { error } = await supabase.auth.signUp({
      email: email.value,
      password: password.value,
      options: {
        emailRedirectTo: getConfirmRedirect()
      }
    })
    if (error) throw error
    toast.add({
      title: 'Confirm your email',
      description: 'We sent you a confirmation link. Please check your inbox to finish creating your account.',
      icon: 'i-lucide-mail-check',
      color: 'primary'
    })
  } catch (e: any) {
    toast.add({ title: 'Sign up failed', description: e.message ?? String(e), color: 'error', icon: 'i-lucide-alert-triangle' })
  } finally {
    loadingSignUp.value = false
  }
}

async function onEmailSignIn() {
  loadingSignIn.value = true
  try {
    const { error } = await supabase.auth.signInWithPassword({
      email: email.value,
      password: password.value
    })
    if (error) throw error
    toast.add({ title: 'Signed in', description: 'Welcome back!', color: 'success', icon: 'i-lucide-badge-check' })
    navigateTo('/')
  } catch (e: any) {
    toast.add({ title: 'Sign in failed', description: e.message ?? String(e), color: 'error', icon: 'i-lucide-alert-triangle' })
  } finally {
    loadingSignIn.value = false
  }
}

async function onGoogleSignIn() {
  loadingGoogle.value = true
  try {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: getConfirmRedirect()
      }
    })
    if (error) throw error
    // Redirect will occur automatically
  } catch (e: any) {
    toast.add({ title: 'Google sign-in failed', description: e.message ?? String(e), color: 'error', icon: 'i-lucide-alert-triangle' })
  } finally {
    loadingGoogle.value = false
  }
}
</script>

<template>
  <main class="bg-default text-default min-h-screen">
    <UContainer class="py-10">
      <div class="max-w-md mx-auto">
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-user-plus" class="text-primary" aria-hidden="true" />
              <h1 class="text-h3 text-highlighted">Sign up / Sign in</h1>
            </div>
          </template>

          <div class="space-y-4">
            <UInput v-model="email" type="email" placeholder="you@example.com" label="Email" required />
            <UInput v-model="password" type="password" placeholder="••••••••" label="Password" required />

            <div class="flex flex-col gap-2">
              <UButton :loading="loadingSignUp" :loading-auto="true" color="primary" icon="i-lucide-mail-plus" label="Create account (email)" @click="onEmailSignUp" />
              <UButton :loading="loadingSignIn" :loading-auto="true" color="neutral" variant="outline" icon="i-lucide-log-in" label="Sign in (email)" @click="onEmailSignIn" />
            </div>

            <div class="flex items-center gap-2">
              <div class="h-px bg-default flex-1" />
              <span class="text-dimmed text-sm">or</span>
              <div class="h-px bg-default flex-1" />
            </div>

            <UButton :loading="loadingGoogle" :loading-auto="true" color="neutral" icon="i-simple-icons-google" label="Continue with Google" @click="onGoogleSignIn" />
          </div>
        </UCard>
      </div>
    </UContainer>
  </main>
</template>
