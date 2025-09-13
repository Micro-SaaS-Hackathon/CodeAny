<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { Course } from '~/types/course'
import { useCourses } from '~/composables/useCourses'
import { useToast } from '#imports'

// Render this page client-side only to avoid any SSR/hydration issues
definePageMeta({ layout: 'app', ssr: false })

const toast = useToast()
const { listCourses, createCourse, createCourseAI, fetchCategories, watchCourseProgress } = useCourses()

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

// --- Create Course (AI) modal ---
const showModal = ref(false)
const loadingAI = ref(false)
const categories = ref<{ label: string, value: string }[]>([])

type AIPayload = {
  topic: string
  title: string
  description: string
  level: string
  instructor?: string
  audience?: string
  level_label?: string
  duration_weeks?: number
  category?: string
  age_range?: string
  language: 'en' | 'az'
  learning_outcomes: string[]
  prerequisites: string[]
  constraints: Record<string, any>
}

const form = ref<AIPayload>({
  topic: '',
  title: '',
  description: '',
  level: 'beginner',
  instructor: '',
  audience: 'University',
  level_label: 'Beginner',
  duration_weeks: 8,
  category: '',
  age_range: '18–24',
  language: 'en',
  learning_outcomes: [],
  prerequisites: [],
  constraints: { images: true }
})

onMounted(async () => {
  try { categories.value = await fetchCategories() } catch {}
})

async function submitAI() {
  if (form.value.title.length < 4 || form.value.title.length > 80) {
    toast.add({ title: 'Title length', description: 'Title must be 4–80 chars', color: 'orange' })
    return
  }
  const words = form.value.description.trim().split(/\s+/).length
  if (words < 30 || words > 300) {
    toast.add({ title: 'Description length', description: 'Description must be 30–300 words', color: 'orange' })
    return
  }
  if (!confirm('This will use AI credits and may take a few minutes. Proceed?')) return
  try {
    loadingAI.value = true
    const resp = await createCourseAI({
      topic: form.value.topic || form.value.title,
      title: form.value.title,
      description: form.value.description,
      level: form.value.level,
      instructor: form.value.instructor,
      audience: form.value.audience,
      level_label: form.value.level_label,
      duration_weeks: form.value.duration_weeks,
      category: form.value.category,
      age_range: form.value.age_range,
      language: form.value.language,
      learning_outcomes: form.value.learning_outcomes,
      prerequisites: form.value.prerequisites,
      constraints: form.value.constraints
    })
    toast.add({ title: 'Started', description: 'AI course generation started', icon: 'i-lucide-robot' })
    showModal.value = false
    await load()
    // Start polling progress for table updates
    const stop = watchCourseProgress(4000, (rows) => { courses.value = rows })
    // Stop polling after some time
    setTimeout(() => stop(), 5 * 60 * 1000)
  } catch (e: any) {
    toast.add({ title: 'AI error', description: String(e?.data?.detail || e?.message || e), color: 'red' })
  } finally {
    loadingAI.value = false
  }
}
</script>

<template>
  <div class="p-4 lg:p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-h3 font-semibold text-highlighted">Courses</h1>
      <div class="flex items-center gap-2">
        <UButton color="primary" icon="i-lucide-sparkles" @click="showModal = true">Create Course</UButton>
      </div>
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
                  <UBadge :color="row.status === 'ready' || row.status === 'published' ? 'green' : (row.status === 'failed' ? 'red' : 'gray')" :label="row.status" />
                </td>
                <td class="px-3 py-2">{{ fmt(row.created_at) }}</td>
                <td class="px-3 py-2">{{ fmt(row.updated_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ClientOnly>
    </UCard>

    <!-- Create Course Modal -->
    <UModal v-model="showModal">
      <UCard>
        <template #header>
          <div class="flex items-center justify-between">
            <p class="font-medium">Create Course</p>
            <UButton icon="i-lucide-x" variant="ghost" size="xs" @click="showModal=false" />
          </div>
        </template>
        <div class="space-y-4">
          <UFormGroup label="Course title">
            <UInput v-model="form.title" placeholder="Introduction to Python for Data Analysis" />
          </UFormGroup>
          <UFormGroup label="Brief description">
            <UTextarea v-model="form.description" :rows="3" placeholder="Teach beginners… focus on NumPy, pandas, plotting; no calculus required." />
          </UFormGroup>
          <div class="grid sm:grid-cols-2 gap-3">
            <UFormGroup label="Audience">
              <USelect v-model="form.audience" :options="['School','University','Bootcamp','Corporate','Self-paced']" />
            </UFormGroup>
            <UFormGroup label="Level">
              <USelect v-model="form.level" :options="['beginner','intermediate','advanced']" />
            </UFormGroup>
            <UFormGroup label="Level label">
              <USelect v-model="form.level_label" :options="['Beginner','Intermediate','Advanced']" />
            </UFormGroup>
            <UFormGroup label="Duration (weeks)">
              <USelect v-model.number="form.duration_weeks" :options="[2,4,6,8,10,12,16]" />
            </UFormGroup>
            <UFormGroup label="Category">
              <USelect v-model="form.category" :options="categories.map(c=>c.label)" />
            </UFormGroup>
            <UFormGroup label="Age range">
              <USelect v-model="form.age_range" :options="['6–10','11–14','15–18','18–24','25–34','35+']" />
            </UFormGroup>
            <UFormGroup label="Language">
              <USelect v-model="form.language" :options="['en','az']" />
            </UFormGroup>
            <UFormGroup label="Instructor (optional)">
              <UInput v-model="form.instructor" />
            </UFormGroup>
          </div>
          <UFormGroup label="Learning outcomes (comma-separated)">
            <UInput v-model="(form.learning_outcomes as any)" placeholder="e.g., Solve systems, Use matrices" @change="(e:any)=>{ form.learning_outcomes = String(form.learning_outcomes||'').split(',').map((s:any)=>String(s).trim()).filter(Boolean) }" />
          </UFormGroup>
          <UFormGroup label="Prerequisites (comma-separated)">
            <UInput v-model="(form.prerequisites as any)" placeholder="e.g., Basic algebra" @change="(e:any)=>{ form.prerequisites = String(form.prerequisites||'').split(',').map((s:any)=>String(s).trim()).filter(Boolean) }" />
          </UFormGroup>
          <UCheckbox v-model="(form.constraints as any).images" label="Generate didactic images" />
        </div>
        <template #footer>
          <div class="flex items-center justify-end gap-2">
            <UButton variant="ghost" @click="showModal=false">Cancel</UButton>
            <UButton color="primary" :loading="loadingAI" icon="i-lucide-sparkles" @click="submitAI">Generate course</UButton>
          </div>
        </template>
      </UCard>
    </UModal>
  </div>
</template>
