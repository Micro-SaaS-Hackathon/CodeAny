<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { Course } from '~/types/course'
import { useCourses } from '~/composables/useCourses'
import { useToast } from '#imports'

definePageMeta({ layout: 'app' })

const toast = useToast()
const { listCourses, createCourse } = useCourses()

const loading = ref(true)
const courses = ref<Course[]>([])

async function load() {
  loading.value = true
  try {
    courses.value = await listCourses()
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

const columns = [
  { key: 'title', label: 'Title' },
  { key: 'progress', label: 'Progress' },
  { key: 'status', label: 'Status' },
  { key: 'created_at', label: 'Created' },
  { key: 'updated_at', label: 'Updated' }
]

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
          <p class="font-medium">All courses</p>
          <UButton size="sm" icon="i-lucide-refresh-ccw" variant="ghost" @click="load" />
        </div>
      </template>

      <div v-if="loading" class="space-y-2">
        <USkeleton class="h-10 w-full" />
        <USkeleton class="h-10 w-full" />
        <USkeleton class="h-10 w-full" />
      </div>

      <UTable v-else :rows="courses" :columns="columns" class="min-w-full">
        <template #progress-data="{ row }">
          <div class="flex items-center gap-3 w-56">
            <UProgress :value="row.progress" class="flex-1" />
            <span class="text-sm text-toned w-10 text-right">{{ row.progress }}%</span>
          </div>
        </template>
        <template #status-data="{ row }">
          <UBadge :color="row.status === 'published' ? 'green' : 'gray'" :label="row.status" />
        </template>
        <template #created_at-data="{ row }">{{ fmt(row.created_at) }}</template>
        <template #updated_at-data="{ row }">{{ fmt(row.updated_at) }}</template>
      </UTable>
    </UCard>
  </div>
</template>
