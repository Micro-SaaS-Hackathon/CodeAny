<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useSupabaseClient, useSupabaseUser, useToast, navigateTo } from '#imports'

const supabase = useSupabaseClient()
const user = useSupabaseUser()
const toast = useToast()

const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const loadingSignUp = ref(false)
const loadingSignIn = ref(false)
const loadingGoogle = ref(false)
const activeTab = ref('signin') // 'signin' or 'signup'
const emailError = ref('')
const passwordError = ref('')
const confirmPasswordError = ref('')
const formValid = ref(true)

onMounted(() => {
  if (user.value) {
    navigateTo('/app/dashboard')
  }
})

function validateEmail() {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email.value) {
    emailError.value = 'Email is required'
    return false
  } else if (!emailRegex.test(email.value)) {
    emailError.value = 'Please enter a valid email'
    return false
  }
  emailError.value = ''
  return true
}

function validatePassword() {
  if (!password.value) {
    passwordError.value = 'Password is required'
    return false
  } else if (password.value.length < 6) {
    passwordError.value = 'Password must be at least 6 characters'
    return false
  }
  passwordError.value = ''
  return true
}

function validateConfirmPassword() {
  if (activeTab.value === 'signup') {
    if (!confirmPassword.value) {
      confirmPasswordError.value = 'Please confirm your password'
      return false
    } else if (confirmPassword.value !== password.value) {
      confirmPasswordError.value = 'Passwords do not match'
      return false
    }
    confirmPasswordError.value = ''
  }
  return true
}

function validateForm() {
  const isEmailValid = validateEmail()
  const isPasswordValid = validatePassword()
  const isConfirmPasswordValid = validateConfirmPassword()
  
  formValid.value = isEmailValid && isPasswordValid && isConfirmPasswordValid
  return formValid.value
}

function getConfirmRedirect() {
  // Build an absolute URL for Supabase redirect/magic link
  if (typeof window !== 'undefined' && window.location?.origin) {
    return new URL('/confirm', window.location.origin).toString()
  }
  return '/confirm'
}

async function onEmailSignUp() {
  if (!validateForm()) return
  
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
  if (!validateEmail() || !validatePassword()) return
  
  loadingSignIn.value = true
  try {
    const { error } = await supabase.auth.signInWithPassword({
      email: email.value,
      password: password.value
    })
    if (error) throw error
    toast.add({ title: 'Signed in', description: 'Welcome back!', color: 'success', icon: 'i-lucide-badge-check' })
    navigateTo('/app/dashboard')
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
  <main class="bg-default text-default min-h-screen flex items-center justify-center py-6">
    <div class="w-full max-w-md px-4">
      <!-- Logo and branding -->
      <div class="flex justify-center mb-6">
        <div class="flex flex-col items-center">
          <img src="~/assets/images/cursly-logo-small.png" alt="Cursly logo" class="h-16 w-auto mb-2" />
          <h1 class="text-h3 text-highlighted font-bold">Cursly</h1>
          <p class="text-sm text-muted mt-1">Build courses in minutes</p>
        </div>
      </div>
      
      <UCard class="border-0 shadow-lg overflow-hidden">
        <!-- Tab navigation -->
        <div class="flex">
          <button 
            class="flex-1 py-3 px-4 text-center transition-all" 
            :class="activeTab === 'signin' ? 'text-primary font-medium' : 'text-muted hover:text-highlighted'" 
            @click="activeTab = 'signin'"
          >
            Sign In
          </button>
          <button 
            class="flex-1 py-3 px-4 text-center transition-all" 
            :class="activeTab === 'signup' ? 'text-primary font-medium' : 'text-muted hover:text-highlighted'" 
            @click="activeTab = 'signup'"
          >
            Create Account
          </button>
        </div>
        
        <!-- Active tab indicator -->
        <div class="relative h-0.5 bg-gray-100 dark:bg-gray-800">
          <div 
            class="absolute h-0.5 bg-primary transition-all duration-300 ease-in-out" 
            :style="{ width: '50%', left: activeTab === 'signin' ? '0' : '50%' }"
          ></div>
        </div>

        <div class="p-6">
          <!-- Sign In Form -->
          <div v-if="activeTab === 'signin'" class="space-y-5">
            <div class="space-y-4">
              <div>
                <UInput 
                  v-model="email" 
                  type="email" 
                  placeholder="you@example.com" 
                  icon="i-lucide-mail" 
                  size="lg"
                  :color="emailError ? 'red' : undefined"
                  @blur="validateEmail"
                  class="auth-input"
                />
                <p v-if="emailError" class="text-xs text-red-500 mt-1 ml-1">{{ emailError }}</p>
              </div>
              
              <div>
                <UInput 
                  v-model="password" 
                  type="password" 
                  placeholder="••••••••" 
                  icon="i-lucide-lock" 
                  size="lg"
                  :color="passwordError ? 'red' : undefined"
                  @blur="validatePassword"
                  class="auth-input"
                />
                <p v-if="passwordError" class="text-xs text-red-500 mt-1 ml-1">{{ passwordError }}</p>
              </div>
            </div>

            <UButton 
              block
              size="lg"
              :loading="loadingSignIn" 
              :loading-auto="true" 
              color="primary" 
              label="Sign in" 
              @click="onEmailSignIn" 
              class="mt-6"
            />
            
            <div class="text-center">
              <button class="text-sm text-primary hover:underline">Forgot password?</button>
            </div>
          </div>

          <!-- Sign Up Form -->
          <div v-if="activeTab === 'signup'" class="space-y-5">
            <div class="space-y-4">
              <div>
                <UInput 
                  v-model="email" 
                  type="email" 
                  placeholder="you@example.com" 
                  icon="i-lucide-mail" 
                  size="lg"
                  :color="emailError ? 'red' : undefined"
                  @blur="validateEmail"
                  class="auth-input"
                />
                <p v-if="emailError" class="text-xs text-red-500 mt-1 ml-1">{{ emailError }}</p>
              </div>
              
              <div>
                <UInput 
                  v-model="password" 
                  type="password" 
                  placeholder="••••••••" 
                  icon="i-lucide-lock" 
                  size="lg"
                  :color="passwordError ? 'red' : undefined"
                  @blur="validatePassword"
                  class="auth-input"
                />
                <p v-if="passwordError" class="text-xs text-red-500 mt-1 ml-1">{{ passwordError }}</p>
              </div>
              
              <div>
                <UInput 
                  v-model="confirmPassword" 
                  type="password" 
                  placeholder="••••••••" 
                  icon="i-lucide-shield-check" 
                  size="lg"
                  :color="confirmPasswordError ? 'red' : undefined"
                  @blur="validateConfirmPassword"
                  class="auth-input"
                />
                <p v-if="confirmPasswordError" class="text-xs text-red-500 mt-1 ml-1">{{ confirmPasswordError }}</p>
              </div>
            </div>

            <UButton 
              block
              size="lg"
              :loading="loadingSignUp" 
              :loading-auto="true" 
              color="primary" 
              label="Create account" 
              @click="onEmailSignUp" 
              class="mt-6"
            />
            
            <div class="text-xs text-center text-muted mt-4">
              <p>By creating an account, you agree to our <a href="#" class="text-primary hover:underline">Terms of Service</a> and <a href="/privacy" class="text-primary hover:underline">Privacy Policy</a>.</p>
            </div>
          </div>
          
          <!-- Divider -->
          <div class="flex items-center gap-2 my-6">
            <div class="h-px bg-gray-200 dark:bg-gray-700 flex-1" />
            <span class="text-dimmed text-sm">or continue with</span>
            <div class="h-px bg-gray-200 dark:bg-gray-700 flex-1" />
          </div>
          
          <!-- Google Sign In -->
          <UButton 
            block
            size="lg"
            :loading="loadingGoogle" 
            :loading-auto="true" 
            color="white" 
            variant="outline"
            icon="i-simple-icons-google" 
            label="Google" 
            @click="onGoogleSignIn" 
            class="border-gray-200 dark:border-gray-700"
          />
        </div>
      </UCard>
      
      <!-- Footer -->
      <div class="text-center mt-6 text-sm text-muted">
        <p>Need help? <a href="mailto:curslyapp@gmail.com" class="text-primary hover:underline">Contact support</a></p>
      </div>
    </div>
  </main>
</template>

<style scoped>
/* Smooth transitions for tab switching */
.tab-enter-active,
.tab-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.tab-enter-from,
.tab-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Custom input styling */
:deep(.auth-input) {
  width: 100%;
  text-align: center;
}

:deep(.auth-input input) {
  border-radius: 999px;
  height: 48px;
  text-align: center;
  padding-left: 2.5rem;
  padding-right: 2.5rem;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
}

:deep(.auth-input .iconify) {
  left: 1rem;
  color: #9ca3af;
}

:deep(.auth-input input:focus) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.1);
}
</style>
