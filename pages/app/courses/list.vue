<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import type { Course } from '~/types/course'
import { useCourses } from '~/composables/useCourses'
import { useRoute } from '#app'

// Render this page client-side only to avoid any SSR/hydration issues
definePageMeta({ layout: 'app', ssr: false })

const { listCourses, watchCourseProgress } = useCourses()

const loading = ref(true)
const courses = ref<Course[]>([])

async function load() {
  loading.value = true
  try {
    const data = await listCourses()
    courses.value = Array.isArray(data) ? data : []
  } finally {
    loading.value = false
  }
}

onMounted(load)

const total = computed(() => courses.value.length)

function fmt(d: string) {
  try {
    return new Date(d).toLocaleString()
  } catch { return d }
}

// If redirected here after starting AI build, begin polling via ?poll=1
const route = useRoute()
let stopPoll: undefined | (() => void)
onMounted(() => {
  if (route.query.poll) {
    stopPoll = watchCourseProgress(4000, (rows) => { courses.value = rows })
    // Stop polling after some time
    setTimeout(() => { stopPoll && stopPoll() }, 5 * 60 * 1000)
  }
})

onUnmounted(() => { stopPoll && stopPoll() })
</script>

<template>
  <div class="p-2 sm:p-4 lg:p-6 space-y-4 sm:space-y-6">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
      <h1 class="text-xl sm:text-2xl lg:text-h3 font-semibold text-highlighted">Courses</h1>
    </div>

    <!-- Empty state / CTA -->
    <UCard v-if="!loading && courses.length === 0">
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <p class="text-lg font-medium">No courses yet</p>
          <p class="text-muted">Use the Create Course button in the top bar to get started.</p>
        </div>
      </div>
    </UCard>

    <!-- Table -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <p class="font-medium">All courses <span class="text-dimmed">({{ total }})</span></p>
          <UButton size="sm" icon="i-lucide-refresh-ccw" variant="ghost" @click="load" />
        </div>
      </template>

      <ClientOnly>
        <template #fallback>
          <div class="space-y-2">
            <USkeleton class="h-10 w-full" />
            <USkeleton class="h-10 w-full" />
            <USkeleton class="h-10 w-full" />
          </div>
        </template>
        <div v-if="loading" class="space-y-2">
          <USkeleton class="h-10 w-full" />
          <USkeleton class="h-10 w-full" />
          <USkeleton class="h-10 w-full" />
        </div>
        <div v-else class="overflow-x-auto -mx-2 sm:mx-0">
          <table class="min-w-full text-xs sm:text-sm">
            <thead>
              <tr class="text-left text-dimmed">
                <th class="px-2 sm:px-3 py-2">Title</th>
                <th class="px-2 sm:px-3 py-2 hidden sm:table-cell">Progress</th>
                <th class="px-2 sm:px-3 py-2">Status</th>
                <th class="px-2 sm:px-3 py-2 hidden md:table-cell">Created</th>
                <th class="px-2 sm:px-3 py-2 hidden lg:table-cell">Updated</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in courses" :key="row.id" class="border-t border-default">
                <td class="px-2 sm:px-3 py-2 font-medium truncate max-w-32 sm:max-w-none">{{ row.title }}</td>
                <td class="px-2 sm:px-3 py-2 hidden sm:table-cell">
                  <div class="flex items-center gap-2 sm:gap-3 w-32 sm:w-56">
                    <UProgress :value="row.progress" class="flex-1" />
                    <span class="text-xs sm:text-sm text-toned w-8 sm:w-10 text-right">{{ row.progress }}%</span>
                  </div>
                </td>
                <td class="px-2 sm:px-3 py-2">
                  <UBadge :color="row.status === 'ready' || row.status === 'published' ? 'green' : (row.status === 'failed' ? 'red' : 'gray')" :label="row.status" size="xs" class="sm:text-sm" />
                </td>
                <td class="px-2 sm:px-3 py-2 hidden md:table-cell text-xs sm:text-sm">{{ fmt(row.created_at) }}</td>
                <td class="px-2 sm:px-3 py-2 hidden lg:table-cell text-xs sm:text-sm">{{ fmt(row.updated_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ClientOnly>
    </UCard>

    
  </div>
</template>
