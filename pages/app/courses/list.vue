<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { Course } from '~/types/course'
import { useCourses } from '~/composables/useCourses'
import { useToast } from '#imports'

// Render this page client-side only to avoid any SSR/hydration issues
definePageMeta({ layout: 'app', ssr: false })

const toast = useToast()
const { listCourses, createCourse } = useCourses()

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

async function onCreateCourse() {
  const course = await createCourse()
  toast.add({ title: 'Course created', description: `“${course.title}” is ready.`, color: 'success', icon: 'i-lucide-check' })
  await load()
}

onMounted(load)

const total = computed(() => courses.value.length)

function fmt(d: string) {
  try {
    return new Date(d).toLocaleString()
  } catch { return d }
}
</script>

<template>
  <div class="p-4 lg:p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-h3 font-semibold text-highlighted">Courses</h1>
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
        <div v-else class="overflow-x-auto">
          <table class="min-w-full text-sm">
            <thead>
              <tr class="text-left text-dimmed">
                <th class="px-3 py-2">Title</th>
                <th class="px-3 py-2">Progress</th>
                <th class="px-3 py-2">Status</th>
                <th class="px-3 py-2">Created</th>
                <th class="px-3 py-2">Updated</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in courses" :key="row.id" class="border-t border-default">
                <td class="px-3 py-2 font-medium">{{ row.title }}</td>
                <td class="px-3 py-2">
                  <div class="flex items-center gap-3 w-56">
                    <UProgress :value="row.progress" class="flex-1" />
                    <span class="text-sm text-toned w-10 text-right">{{ row.progress }}%</span>
                  </div>
                </td>
                <td class="px-3 py-2">
                  <UBadge :color="row.status === 'published' ? 'green' : 'gray'" :label="row.status" />
                </td>
                <td class="px-3 py-2">{{ fmt(row.created_at) }}</td>
                <td class="px-3 py-2">{{ fmt(row.updated_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ClientOnly>
    </UCard>
  </div>
</template>
