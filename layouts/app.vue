<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from '#app'
import { useSupabaseUser, useSupabaseClient, useToast, navigateTo } from '#imports'
import CreateCourseModal from '~/components/CreateCourseModal.vue'
import { useCreateCourseModal } from '~/composables/useCreateCourseModal'

const q = ref('')
const user = useSupabaseUser()
const supabase = useSupabaseClient()
const toast = useToast()
const avatarName = computed(() => (user.value?.user_metadata as any)?.name || user.value?.email || 'User')
const avatarSrc = computed(() => (user.value?.user_metadata as any)?.avatar_url || (user.value?.user_metadata as any)?.picture || null)
const avatarInitial = computed(() => {
  const raw = ((user.value?.user_metadata as any)?.name || user.value?.email || 'U').toString().trim()
  return raw ? raw[0].toUpperCase() : 'U'
})

const route = useRoute()
const isDashboard = computed(() => route.path.startsWith('/app/dashboard'))
const isCourses = computed(() => route.path.startsWith('/app/courses'))

// Global control for Create Course modal (shared via composable)
const { isOpen: showCreateCourse, open: openCreateCourse } = useCreateCourseModal()

async function handleLogout() {
  try {
    await supabase.auth.signOut()
    toast.add({
      title: 'Signed out successfully',
      color: 'green'
    })
    navigateTo('/auth')
  } catch (error) {
    console.error('Error signing out:', error)
    toast.add({
      title: 'Error signing out',
      description: 'Please try again',
      color: 'red'
    })
  }
}
</script>

<template>
  <div class="min-h-screen bg-default text-default">
    <!-- Topbar -->
    <header class="sticky top-0 z-40 border-b border-default bg-default/90 backdrop-blur">
      <UContainer class="h-14 flex items-center justify-between gap-3">
        <NuxtLink to="/app/dashboard" class="flex items-center gap-2 shrink-0">
          <img src="~/assets/images/cursly-logo-small.png" alt="Cursly" class="h-6 w-auto" />
          <span class="font-semibold">Teacher Hub</span>
        </NuxtLink>
        <div class="flex-1 min-w-0 px-2 hidden sm:block">
          <UInput v-model="q" placeholder="Search…" icon="i-lucide-search" class="w-full max-w-xl" size="lg" />
        </div>
        <div class="flex items-center gap-2 sm:gap-3 shrink-0">
          <UButton color="primary" icon="i-lucide-plus" label="Create Course" class="sm:px-4" @click="openCreateCourse()" />
          <!-- Avoid SSR hydration differences by rendering avatar on client only -->
          <ClientOnly>
            <template #fallback>
              <UAvatar :alt="avatarName" size="md" class="bg-primary text-white ring-2 ring-primary/60">
                <span class="text-xs font-semibold">{{ avatarInitial }}</span>
              </UAvatar>
            </template>
            <UDropdownMenu :items="[{ label: 'Sign out', icon: 'i-lucide-log-out', onSelect: handleLogout }]" mode="click">
              <UButton variant="ghost" :padded="false" class="p-1">
                <template v-if="avatarSrc">
                  <UAvatar :src="avatarSrc" :alt="avatarName" size="md" class="ring-2 ring-primary/60" />
                </template>
                <template v-else>
                  <UAvatar :alt="avatarName" size="md" class="bg-primary text-white ring-2 ring-primary/60">
                    <span class="text-xs font-semibold">{{ avatarInitial }}</span>
                  </UAvatar>
                </template>
              </UButton>
            </UDropdownMenu>
          </ClientOnly>
        </div>
      </UContainer>
    </header>

    <!-- Body with slim sidebar -->
    <div class="grid grid-cols-1 lg:grid-cols-[220px_1fr]">
      <aside class="border-r border-default min-h-[calc(100vh-3.5rem)] hidden lg:block">
        <nav class="p-2 space-y-1">
          <NuxtLink
            to="/app/dashboard"
            :aria-current="isDashboard ? 'page' : undefined"
            :class="[
              'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
              isDashboard ? 'bg-primary/10 text-primary' : 'hover:bg-gray-50 dark:hover:bg-gray-800'
            ]">
            <UIcon name="i-lucide-home" :class="isDashboard ? 'text-primary' : ''" />
            <span class="font-medium" :class="isDashboard ? 'text-primary' : ''">Dashboard</span>
          </NuxtLink>
          <NuxtLink
            to="/app/courses/list"
            :aria-current="isCourses ? 'page' : undefined"
            :class="[
              'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
              isCourses ? 'bg-primary/10 text-primary' : 'hover:bg-gray-50 dark:hover:bg-gray-800'
            ]">
            <UIcon name="i-lucide-book-open" :class="isCourses ? 'text-primary' : ''" />
            <span class="font-medium" :class="isCourses ? 'text-primary' : ''">Courses</span>
          </NuxtLink>
        </nav>
      </aside>
      <main class="p-2 sm:p-4 lg:p-6">
        <slot />
      </main>
    </div>
    <CreateCourseModal v-model="showCreateCourse" />
  </div>
  
</template>
