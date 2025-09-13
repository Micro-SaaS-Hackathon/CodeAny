<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast, navigateTo } from '#imports'
import { useCourses } from '~/composables/useCourses'

const toast = useToast()
const { createCourseAI, fetchCategories } = useCourses()

const props = withDefaults(defineProps<{ modelValue?: boolean }>(), { modelValue: false })
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()
const isOpen = computed({ get: () => props.modelValue, set: (v: boolean) => emit('update:modelValue', v) })
function close() { isOpen.value = false }

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
    await createCourseAI({
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
    close()
    await navigateTo('/app/courses/list?poll=1')
  } catch (e: any) {
    toast.add({ title: 'AI error', description: String(e?.data?.detail || e?.message || e), color: 'red' })
  } finally {
    loadingAI.value = false
  }
}
</script>

<template>
  <UModal v-model:open="isOpen">
    <template #content>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <p class="font-medium">Create Course</p>
          <UButton icon="i-lucide-x" variant="ghost" size="xs" @click="close()" />
        </div>
      </template>
      <div class="space-y-4">
        <UFormField label="Course title">
          <UInput v-model="form.title" placeholder="Introduction to Python for Data Analysis" />
        </UFormField>
        <UFormField label="Brief description">
          <UTextarea v-model="form.description" :rows="3" placeholder="Teach beginners… focus on NumPy, pandas, plotting; no calculus required." />
        </UFormField>
        <div class="grid sm:grid-cols-2 gap-3">
          <UFormField label="Audience">
            <USelect v-model="form.audience" :options="['School','University','Bootcamp','Corporate','Self-paced']" />
          </UFormField>
          <UFormField label="Level">
            <USelect v-model="form.level" :options="['beginner','intermediate','advanced']" />
          </UFormField>
          <UFormField label="Level label">
            <USelect v-model="form.level_label" :options="['Beginner','Intermediate','Advanced']" />
          </UFormField>
          <UFormField label="Duration (weeks)">
            <USelect v-model.number="form.duration_weeks" :options="[2,4,6,8,10,12,16]" />
          </UFormField>
          <UFormField label="Category">
            <USelect v-model="form.category" :options="categories.map(c=>c.label)" />
          </UFormField>
          <UFormField label="Age range">
            <USelect v-model="form.age_range" :options="['6–10','11–14','15–18','18–24','25–34','35+']" />
          </UFormField>
          <UFormField label="Language">
            <USelect v-model="form.language" :options="['en','az']" />
          </UFormField>
          <UFormField label="Instructor (optional)">
            <UInput v-model="form.instructor" />
          </UFormField>
        </div>
        <UFormField label="Learning outcomes (comma-separated)">
          <UInput v-model="(form.learning_outcomes as any)" placeholder="e.g., Solve systems, Use matrices" @change="(e:any)=>{ form.learning_outcomes = String(form.learning_outcomes||'').split(',').map((s:any)=>String(s).trim()).filter(Boolean) }" />
        </UFormField>
        <UFormField label="Prerequisites (comma-separated)">
          <UInput v-model="(form.prerequisites as any)" placeholder="e.g., Basic algebra" @change="(e:any)=>{ form.prerequisites = String(form.prerequisites||'').split(',').map((s:any)=>String(s).trim()).filter(Boolean) }" />
        </UFormField>
        <UCheckbox v-model="(form.constraints as any).images" label="Generate didactic images" />
      </div>
      <template #footer>
        <div class="flex items-center justify-end gap-2">
          <UButton variant="ghost" @click="close()">Cancel</UButton>
          <UButton color="primary" :loading="loadingAI" icon="i-lucide-sparkles" @click="submitAI">Generate course</UButton>
        </div>
      </template>
    </UCard>
    </template>
  </UModal>
</template>
