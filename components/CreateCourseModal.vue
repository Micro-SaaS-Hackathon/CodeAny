<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { useToast, navigateTo } from '#imports'
import { useCourses } from '~/composables/useCourses'
import MaterialSelect from '~/components/MaterialSelect.vue'

const toast = useToast()
const { createCourseAI, fetchCategories } = useCourses()

const props = withDefaults(defineProps<{ modelValue?: boolean }>(), { modelValue: false })
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()
const isOpen = computed({ get: () => props.modelValue, set: (v: boolean) => emit('update:modelValue', v) })
function close() { isOpen.value = false }

function scrollToBottom() {
  if (modalContentRef.value) {
    modalContentRef.value.scrollTo({
      top: modalContentRef.value.scrollHeight,
      behavior: 'smooth'
    })
  }
}

const loadingAI = ref(false)
const categories = ref<{ label: string, value: string }[]>([])
const categoriesLoading = ref(false)

// Dropdown options
const audienceOptions = ['School', 'University', 'Bootcamp', 'Corporate', 'Self-paced']
const levelOptions = ['beginner', 'intermediate', 'advanced']
const durationOptions = [2, 4, 6, 8, 10, 12, 16]
const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Azerbaijani', value: 'az' }
]

// UI helpers & validation
const titleMin = 4
const titleMax = 80
const descMinWords = 30
const descMaxWords = 300
const learningOutcomesInput = ref('')
const prerequisitesInput = ref('')
const titleRef = ref<any>(null)
const showAdvanced = ref(false)
const modalContentRef = ref<any>(null)

// Tags-style editors for outcomes & prerequisites
const learningChips = ref<string[]>([])
const prereqChips = ref<string[]>([])

function sanitizeChip(s: string) {
  return s.replace(/[.,;:]+$/, '').trim()
}

function addChip(kind: 'outcome' | 'prereq') {
  const src = kind === 'outcome' ? learningOutcomesInput : prerequisitesInput
  const chips = kind === 'outcome' ? learningChips : prereqChips
  const parts = String(src.value || '')
    .split(/[\n,]/)
    .map(s => sanitizeChip(s))
    .filter(Boolean)
  if (!parts.length) return
  for (const p of parts) {
    if (!chips.value.includes(p)) chips.value.push(p)
  }
  src.value = ''
}

function removeChip(kind: 'outcome' | 'prereq', idx: number) {
  const chips = kind === 'outcome' ? learningChips : prereqChips
  chips.value.splice(idx, 1)
}

function onChipsKeydown(kind: 'outcome' | 'prereq', e: KeyboardEvent) {
  if (e.key === 'Enter' || e.key === ',' || e.key === 'Tab') {
    e.preventDefault()
    addChip(kind)
  } else if (e.key === 'Backspace') {
    const src = kind === 'outcome' ? learningOutcomesInput : prerequisitesInput
    const chips = kind === 'outcome' ? learningChips : prereqChips
    if (!src.value && chips.value.length) chips.value.pop()
  }
}

const titleChars = computed(() => form.value.title.trim().length)
const descriptionWords = computed(() => form.value.description.trim().split(/\s+/).filter(Boolean).length)
const isTitleValid = computed(() => titleChars.value >= titleMin && titleChars.value <= titleMax)
const isDescValid = computed(() => descriptionWords.value >= descMinWords && descriptionWords.value <= descMaxWords)
const titleColor = computed(() => (isTitleValid.value || !form.value.title) ? undefined : 'red')
const descColor = computed(() => (isDescValid.value || !form.value.description) ? undefined : 'red')
const canSubmit = computed(() => isTitleValid.value && isDescValid.value && !loadingAI.value)

function onKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'enter') {
    e.preventDefault()
    if (isOpen.value && canSubmit.value && !loadingAI.value) submitAI()
  }
}

function prefillExample() {
  form.value.title = 'Introduction to Python for Data Analysis'
  form.value.description = 'Teach beginners the essentials of Python for data analysis. Cover data types, control flow, functions, and working with NumPy and pandas. Include practical exercises with datasets and simple visualizations using matplotlib. No prior calculus required; focus on intuition and hands-on practice.'
  form.value.audience = 'University'
  form.value.level = 'beginner'
  form.value.duration_weeks = 8
  form.value.age_range = '18–24'
  form.value.language = 'en'
  form.value.instructor = ''
  learningOutcomesInput.value = 'Use NumPy arrays, Manipulate DataFrames, Plot basic charts'
  prerequisitesInput.value = 'Basic computer literacy'
  learningChips.value = ['Use NumPy arrays', 'Manipulate DataFrames', 'Plot basic charts']
  prereqChips.value = ['Basic computer literacy']
}

function resetForm() {
  form.value = {
    topic: '',
    title: '',
    description: '',
    level: 'beginner',
    instructor: '',
    audience: 'University',
    duration_weeks: 8,
    category: '',
    age_range: '18–24',
    language: 'en',
    learning_outcomes: [],
    prerequisites: [],
    constraints: { images: true }
  }
  learningOutcomesInput.value = ''
  prerequisitesInput.value = ''
  showAdvanced.value = false
  learningChips.value = []
  prereqChips.value = []
}

watch(isOpen, (v) => {
  if (v) {
    window.addEventListener('keydown', onKeydown)
    // Prefill string inputs from arrays when reopening
    learningOutcomesInput.value = (form.value.learning_outcomes || []).join(', ')
    prerequisitesInput.value = (form.value.prerequisites || []).join(', ')
    learningChips.value = [...(form.value.learning_outcomes || [])]
    prereqChips.value = [...(form.value.prerequisites || [])]
    nextTick(() => titleRef.value?.focus?.())
  } else {
    // When closed, clear the loading state just in case
    loadingAI.value = false
    window.removeEventListener('keydown', onKeydown)
  }
})

onUnmounted(() => window.removeEventListener('keydown', onKeydown))

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
  duration_weeks: 8,
  category: '',
  age_range: '18–24',
  language: 'en',
  learning_outcomes: [],
  prerequisites: [],
  constraints: { images: true }
})

onMounted(async () => {
  try {
    categoriesLoading.value = true
    categories.value = await fetchCategories()
  } catch {}
  finally { categoriesLoading.value = false }
})

async function submitAI() {
  if (!isTitleValid.value) {
    toast.add({ title: 'Title length', description: `Title must be ${titleMin}–${titleMax} chars`, color: 'orange' })
    return
  }
  if (!isDescValid.value) {
    toast.add({ title: 'Description length', description: `Description must be ${descMinWords}–${descMaxWords} words`, color: 'orange' })
    return
  }

  // Consolidate chips + any pending input into arrays
  const pendingOutcomes = String(learningOutcomesInput.value || '')
    .split(',')
    .map(s => sanitizeChip(String(s)))
    .filter(Boolean)
  const pendingPrereqs = String(prerequisitesInput.value || '')
    .split(',')
    .map(s => sanitizeChip(String(s)))
    .filter(Boolean)

  form.value.learning_outcomes = Array.from(new Set([...(learningChips.value || []), ...pendingOutcomes]))
  form.value.prerequisites = Array.from(new Set([...(prereqChips.value || []), ...pendingPrereqs]))
  try {
    loadingAI.value = true
    await createCourseAI({
      topic: form.value.topic || form.value.title,
      title: form.value.title,
      description: form.value.description,
      level: form.value.level,
      instructor: form.value.instructor,
      audience: form.value.audience,
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
  <UModal v-model:open="isOpen" :prevent-close="loadingAI" title="Create Course" description="Fill the form to generate a course with AI" :ui="{ width: 'max-w-4xl', height: 'max-h-[90vh]', container: 'overflow-y-auto' }" class="z-50">
    <template #content>
    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <p class="font-medium">Create Course</p>
            <UBadge color="violet" variant="subtle" size="xs" class="uppercase">AI</UBadge>
          </div>
          <div class="flex items-center gap-2">
            <UTooltip text="Fill with a high-quality example">
              <UButton variant="ghost" size="xs" icon="i-lucide-wand-2" @click="prefillExample">Prefill example</UButton>
            </UTooltip>
            <UButton icon="i-lucide-x" variant="ghost" size="xs" @click="close()" />
          </div>
        </div>
      </template>
      <div ref="modalContentRef" class="space-y-5 max-h-[70vh] overflow-y-auto relative">
        <UAlert icon="i-lucide-sparkles" color="primary" variant="soft" title="AI generation"
          description="Cursly will generate modules, quizzes, assignments and a schedule. This may take a few minutes." />

        <UFormField :color="titleColor" :help="`${titleChars}/${titleMax} characters`" label="Course title">
          <UInput ref="titleRef" v-model="form.title" :maxlength="titleMax" icon="i-lucide-type" :disabled="loadingAI" placeholder="Introduction to Python for Data Analysis" size="lg" class="w-full" />
        </UFormField>
        <UFormField label="Topic (optional)" help="Keyword that guides generation (defaults to title)">
          <UInput v-model="form.topic" icon="i-lucide-hash" :disabled="loadingAI" placeholder="e.g., Python, Data Analysis" size="lg" class="w-full" />
        </UFormField>
        <UFormField :color="descColor" :help="`${descriptionWords} words (recommended ${descMinWords}–${descMaxWords})`" label="Brief description">
          <UTextarea v-model="form.description" :disabled="loadingAI" :rows="6" placeholder="Teach beginners… focus on NumPy, pandas, plotting; no calculus required." size="lg" class="w-full" autoresize />
        </UFormField>

        <UFormField label="Instructor (optional)">
          <UInput v-model="form.instructor" icon="i-lucide-user-2" :disabled="loadingAI" placeholder="Dr. Ada Lovelace" size="lg" class="w-full" />
        </UFormField>

        <UFormField label="Learning outcomes" help="Press Enter, Comma, or Tab to add multiple outcomes">
          <div class="space-y-2">
            <UInput
              v-model="learningOutcomesInput"
              :disabled="loadingAI"
              placeholder="Type an outcome and press Enter to add more"
              size="lg"
              class="w-full"
              @keydown="onChipsKeydown('outcome', $event)"
            />
            <div class="flex flex-wrap gap-2">
              <UBadge v-for="(chip, i) in learningChips" :key="chip + i" variant="soft" class="gap-1">
                {{ chip }}
                <UButton v-if="!loadingAI" icon="i-lucide-x" variant="ghost" size="xs" @click="removeChip('outcome', i)" />
              </UBadge>
            </div>
          </div>
        </UFormField>

        <UFormField label="Prerequisites" help="Press Enter, Comma, or Tab to add multiple prerequisites">
          <div class="space-y-2">
            <UInput
              v-model="prerequisitesInput"
              :disabled="loadingAI"
              placeholder="Type a prerequisite and press Enter to add more"
              size="lg"
              class="w-full"
              @keydown="onChipsKeydown('prereq', $event)"
            />
            <div class="flex flex-wrap gap-2">
              <UBadge v-for="(chip, i) in prereqChips" :key="chip + i" variant="soft" class="gap-1">
                {{ chip }}
                <UButton v-if="!loadingAI" icon="i-lucide-x" variant="ghost" size="xs" @click="removeChip('prereq', i)" />
              </UBadge>
            </div>
          </div>
        </UFormField>
        <p class="text-xs text-dimmed">Tip: Press <kbd class="px-1 py-0.5 rounded border">Cmd/Ctrl + Enter</kbd> to generate</p>
        <div class="flex items-center gap-3 select-none" aria-hidden="true">
          <div class="h-px bg-default/50 flex-1" />
          <span class="text-[11px] uppercase tracking-wide text-dimmed">Targeting</span>
          <div class="h-px bg-default/50 flex-1" />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <MaterialSelect v-model="form.audience" :disabled="loadingAI" :options="audienceOptions" label="Audience" />
          <MaterialSelect v-model="form.level" :disabled="loadingAI" :options="levelOptions" label="Level" />
          <MaterialSelect v-model="form.duration_weeks" :disabled="loadingAI" :options="durationOptions" label="Duration (weeks)" />
          <MaterialSelect v-model="form.language" :disabled="loadingAI" :options="languageOptions" label="Language" />
        </div>
        <div class="py-2">
          <UButton variant="link" size="sm" :disabled="loadingAI" :icon="showAdvanced ? 'i-lucide-chevron-down' : 'i-lucide-chevron-right'" @click="showAdvanced = !showAdvanced">
            {{ showAdvanced ? 'Hide advanced options' : 'Show advanced options' }}
          </UButton>
        </div>
        <div v-if="showAdvanced" class="space-y-4">
          <div class="flex items-center gap-3 select-none" aria-hidden="true">
            <div class="h-px bg-default/50 flex-1" />
            <span class="text-[11px] uppercase tracking-wide text-dimmed">Advanced</span>
            <div class="h-px bg-default/50 flex-1" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <MaterialSelect v-model="form.category" :disabled="loadingAI || categoriesLoading" :options="categories" label="Category" :help="categoriesLoading ? 'Fetching categories…' : ''" />
            <MaterialSelect v-model="form.age_range" :disabled="loadingAI" :options="['6–10','11–14','15–18','18–24','25–34','35+']" label="Age range" />
          </div>
          <UCheckbox v-model="(form.constraints as any).images" :disabled="loadingAI" label="Generate didactic images" />
        </div>
        
        <!-- Floating scroll to bottom button -->
        <div class="absolute bottom-4 right-4 z-10">
          <UTooltip text="Scroll to bottom">
            <UButton 
              icon="i-lucide-arrow-down" 
              variant="outline" 
              size="sm" 
              class="shadow-lg bg-white dark:bg-gray-800 border-2" 
              @click="scrollToBottom"
              :disabled="loadingAI"
            />
          </UTooltip>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between gap-2 w-full">
          <div class="flex items-center gap-2">
            <UButton variant="ghost" size="sm" :disabled="loadingAI" icon="i-lucide-rotate-ccw" @click="resetForm">Reset</UButton>
          </div>
          <div class="flex items-center gap-2">
            <UButton variant="ghost" :disabled="loadingAI" @click="close()">Cancel</UButton>
            <UButton color="primary" :disabled="!canSubmit" :loading="loadingAI" icon="i-lucide-sparkles" @click="submitAI">Generate course</UButton>
          </div>
        </div>
        <div v-if="loadingAI" class="mt-3">
          <UProgress :indeterminate="true" />
        </div>
      </template>
    </UCard>
    </template>
  </UModal>
</template>
