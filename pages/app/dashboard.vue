<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useStats } from '~/composables/useStats'
import { } from '#imports'

// Render client-side only for consistent state with Supabase
definePageMeta({ layout: 'app', ssr: false })

const { getStats } = useStats()

const loading = ref(true)
const stats = ref<{ total_courses: number; active_teachers: number; recent_activity: any[] } | null>(null)

async function load() {
  loading.value = true
  try {
    stats.value = await getStats()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="p-2 sm:p-4 lg:p-6 space-y-4 sm:space-y-6">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
      <h1 class="text-xl sm:text-2xl lg:text-h3 font-semibold text-highlighted">Dashboard</h1>
    </div>

    <!-- Welcome / CTA -->
    <UCard>
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <p class="text-xl font-medium">Welcome to Teacher Hub</p>
          <p class="text-muted">Generate and manage your courses. Use the Create Course button in the top bar when you're ready.</p>
        </div>
      </div>
    </UCard>

    <!-- Stats cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
      <UCard>
        <p class="text-dimmed text-xs sm:text-sm">Total courses</p>
        <div class="text-2xl sm:text-3xl font-bold mt-1">
          <USkeleton v-if="loading" class="h-8 w-16" />
          <span v-else>{{ stats?.total_courses ?? 0 }}</span>
        </div>
      </UCard>
      <UCard>
        <p class="text-dimmed text-xs sm:text-sm">Active teachers</p>
        <div class="text-2xl sm:text-3xl font-bold mt-1">
          <USkeleton v-if="loading" class="h-8 w-16" />
          <span v-else>{{ stats?.active_teachers ?? 0 }}</span>
        </div>
      </UCard>
      <UCard>
        <p class="text-dimmed text-xs sm:text-sm">Recent activity</p>
        <div class="text-2xl sm:text-3xl font-bold mt-1">
          <USkeleton v-if="loading" class="h-8 w-24" />
          <span v-else>{{ (stats?.recent_activity?.length || 0) }} events</span>
        </div>
      </UCard>
    </div>

    <!-- Activity feed -->
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <p class="font-medium">Recent activity</p>
          <UButton variant="ghost" icon="i-lucide-refresh-ccw" @click="load" />
        </div>
      </template>
      <div class="divide-y divide-default">
        <div v-if="loading" class="space-y-2">
          <USkeleton class="h-4 w-1/2" />
          <USkeleton class="h-4 w-2/3" />
          <USkeleton class="h-4 w-1/3" />
        </div>
        <div v-else-if="!stats?.recent_activity?.length" class="text-muted">No recent activity yet.</div>
        <div v-else v-for="(a, i) in stats?.recent_activity" :key="i" class="py-2 sm:py-3 flex items-center gap-2 sm:gap-3">
          <UIcon name="i-lucide-activity" class="text-primary flex-shrink-0" />
          <div class="flex-1 min-w-0">
            <div class="text-xs sm:text-sm truncate">Course <span class="font-medium">{{ a.course_id }}</span> <span class="text-toned">{{ a.event }}</span></div>
            <div class="text-xs text-dimmed">{{ a.timestamp }}</div>
          </div>
        </div>
      </div>
    </UCard>
  </div>
</template>
