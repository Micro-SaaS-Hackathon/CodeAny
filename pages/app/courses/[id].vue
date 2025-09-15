<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from '#app'
import { useToast } from '#imports'
import type { CourseDetail, Module } from '~/types/course'
import { useCourses } from '~/composables/useCourses'

definePageMeta({ layout: 'app', ssr: false })

const route = useRoute()
const router = useRouter()
const id = ref<string>('')
const loading = ref(true)
const saving = ref(false)
const { getCourse, updateCourse, listModules, upsertModule, getConvexFileUrl, recompileModule } = useCourses()
const toast = useToast()

const course = ref<CourseDetail | null>(null)
const editOpen = ref(false)
const editDraft = ref<Partial<CourseDetail>>({})

// Module inline edit state
const inlineEditingId = ref<string | null>(null)
const moduleDraft = ref<Partial<Module>>({})
const moduleTarget = ref<Module | null>(null)
const mdMode = ref<'write' | 'preview' | 'split'>('split')
const recompiling: any = ref<Record<string, boolean>>({})

function escapeHtml(s: string) {
  return s
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function renderMarkdown(src: string): string {
  const parts = (src || '').split(/```/)
  let html = ''
  for (let i = 0; i < parts.length; i++) {
    const chunk = parts[i]
    if (i % 2 === 1) {
      html += `<pre class="rounded-md border border-default p-3 overflow-auto"><code>${escapeHtml(chunk)}</code></pre>`
      continue
    }
    const lines = chunk.split(/\r?\n/)
    let inList = false
    for (let raw of lines) {
      let line = raw
      if (!line.trim()) { if (inList) { html += '</ul>'; inList = false } continue }
      // headings
      const h = line.match(/^(#{1,6})\s+(.*)$/)
      if (h) {
        if (inList) { html += '</ul>'; inList = false }
        const level = h[1].length
        const text = h[2]
        html += `<h${level} class="mt-4 mb-2 font-semibold">${inlineMd(escapeHtml(text))}</h${level}>`
        continue
      }
      // list item
      const li = line.match(/^\s*[-*+]\s+(.*)$/)
      if (li) {
        if (!inList) { html += '<ul class="list-disc pl-6 my-2 space-y-1">'; inList = true }
        html += `<li>${inlineMd(escapeHtml(li[1]))}</li>`
        continue
      }
      // paragraph
      if (inList) { html += '</ul>'; inList = false }
      html += `<p class="mb-3 leading-7">${inlineMd(escapeHtml(line))}</p>`
    }
    if (inList) { html += '</ul>'; inList = false }
  }
  return html
}

function inlineMd(s: string) {
  // bold **text**
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // italics *text* or _text_
  s = s.replace(/(^|\W)\*(?!\s)([^*]+?)\*(?!\w)/g, '$1<em>$2</em>')
  s = s.replace(/(^|\W)_(?!\s)([^_]+?)_(?!\w)/g, '$1<em>$2</em>')
  // inline code `code`
  s = s.replace(/`([^`]+?)`/g, '<code class="px-1 py-0.5 rounded bg-muted/50 border">$1</code>')
  return s
}

const mdHtml = computed(() => renderMarkdown(String(moduleDraft.value.text || '')))

const progress = computed(() => course.value?.progress ?? 0)
const isModuleRoute = computed(() => String(route.name || '').startsWith('app-courses-id-modules'))

async function load() {
  if (!id.value) return
  loading.value = true
  try {
    const data = await getCourse(id.value)
    course.value = data
    // Ensure modules list is fresh if backend doesn't include
    if (!Array.isArray(data.modules)) {
      const mods = await listModules(id.value)
      course.value = { ...data, modules: mods }
    }
  } catch (e) {
    console.error(e)
    toast.add({ title: 'Failed to load course', color: 'red' })
  } finally {
    loading.value = false
  }
}

function openEdit() {
  if (!course.value) return
  editDraft.value = {
    title: course.value.title,
    status: course.value.status,
    description: course.value.description,
    instructor: course.value.instructor,
    audience: course.value.audience,
    level_label: course.value.level_label,
    duration_weeks: course.value.duration_weeks,
    category: course.value.category,
    age_range: course.value.age_range,
    language: course.value.language,
  }
  editOpen.value = true
}

async function saveEdit() {
  if (!course.value) return
  saving.value = true
  try {
    const updated = await updateCourse(course.value.id, editDraft.value)
    course.value = updated
    editOpen.value = false
    toast.add({ title: 'Course updated', icon: 'i-lucide-check', color: 'green' })
  } catch (e) {
    console.error(e)
    toast.add({ title: 'Failed to update course', color: 'red' })
  } finally {
    saving.value = false
  }
}

function openModuleEdit(m: Module) {
  moduleTarget.value = m
  moduleDraft.value = { ...m }
  inlineEditingId.value = m.moduleId
  nextTick(() => {
    const el = document.getElementById(`mod-${m.moduleId}`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function openModuleView(m: Module) {
  const cid = id.value || String(route.params.id || '')
  try {
    router.push({ name: 'app-courses-id-modules-moduleId', params: { id: cid, moduleId: String(m.moduleId) } })
  } catch {
    // Fallback to path-based push with encoding
    const path = `/app/courses/${encodeURIComponent(cid)}/modules/${encodeURIComponent(String(m.moduleId))}`
    router.push(path)
  }
}

function addModule() {
  if (!course.value) return
  const existing = course.value.modules || []
  // derive next id as numeric sequence; fallback to timestamp
  const nextId = (() => {
    const nums = existing
      .map(m => parseInt(String(m.moduleId), 10))
      .filter(n => Number.isFinite(n))
    const max = nums.length ? Math.max(...nums) : 0
    return String(max + 1)
  })()
  const blank: Module = { courseId: course.value.id, moduleId: nextId, title: '', text: '' }
  course.value = { ...course.value, modules: [...existing, blank] }
  openModuleEdit(blank)
}

async function saveModule() {
  if (!course.value || !moduleTarget.value) return
  saving.value = true
  try {
    const saved = await upsertModule(course.value.id, moduleTarget.value.moduleId, moduleDraft.value)
    // update in place
    const mods = (course.value.modules || []).map(m => m.moduleId === saved.moduleId ? saved : m)
    course.value = { ...course.value, modules: mods }
    inlineEditingId.value = null
    toast.add({ title: 'Module saved', icon: 'i-lucide-check', color: 'green' })
  } catch (e) {
    console.error(e)
    toast.add({ title: 'Failed to save module', color: 'red' })
  } finally {
    saving.value = false
  }
}

function cancelModuleEdit() {
  inlineEditingId.value = null
  moduleTarget.value = null
}

async function triggerRecompile(m: Module) {
  if (!course.value) return
  recompiling.value[m.moduleId] = true
  try {
    const updated = await recompileModule(course.value.id, m.moduleId)
    const mods = (course.value.modules || []).map(mm => mm.moduleId === updated.moduleId ? updated : mm)
    course.value = { ...course.value, modules: mods }
    toast.add({ title: 'Video recompiled', icon: 'i-lucide-badge-check', color: 'green' })
    if (viewOpen.value && viewTarget.value?.moduleId === m.moduleId && (updated as any).videoStorageId) {
      viewVideoUrl.value = await getConvexFileUrl((updated as any).videoStorageId as string)
    }
  } catch (e: any) {
    toast.add({ title: 'Recompile failed', description: String(e?.data?.detail || e?.message || e), color: 'red' })
  } finally {
    recompiling.value[m.moduleId] = false
  }
}

onMounted(() => {
  id.value = String(route.params.id || '')
  load()
})

watch(() => route.params.id, (v) => { id.value = String(v || ''); load() })
</script>

<template>
  <div v-if="!isModuleRoute" class="p-2 sm:p-4 lg:p-6 space-y-4 sm:space-y-6">
    <div class="flex items-center justify-between gap-2">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <UButton icon="i-lucide-arrow-left" variant="ghost" color="gray" @click="router.push('/app/courses/list')" />
          <p class="text-xs text-dimmed truncate">Course</p>
        </div>
        <h1 class="mt-1 text-xl sm:text-2xl lg:text-h3 font-semibold text-highlighted truncate">
          {{ course?.title || 'Loading…' }}
        </h1>
      </div>
      <div class="flex items-center gap-3">
        <div class="hidden sm:flex items-center gap-2 w-40">
          <UProgress :value="progress" class="flex-1" />
          <span class="text-xs text-toned w-8 text-right">{{ progress }}%</span>
        </div>
        <UBadge :label="course?.status || 'draft'" :color="(course?.status === 'ready' || course?.status === 'published') ? 'green' : (course?.status === 'failed' ? 'red' : 'gray')" />
        <UButton icon="i-lucide-pencil" @click="openEdit" :disabled="!course">Edit</UButton>
      </div>
    </div>

    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <p class="font-medium">Overview</p>
          <UBadge :label="course?.status || 'draft'" :color="(course?.status === 'ready' || course?.status === 'published') ? 'green' : (course?.status === 'failed' ? 'red' : 'gray')" />
        </div>
      </template>
      <div v-if="loading">
        <USkeleton class="h-6 w-1/2 mb-2" />
        <USkeleton class="h-4 w-2/3" />
      </div>
      <div v-else-if="course" class="space-y-3">
        <div class="text-sm text-toned">
          <span class="font-medium">Description:</span>
          <span class="ml-1">{{ course.description || '—' }}</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div>
            <span class="text-dimmed">Instructor</span>
            <div class="font-medium">{{ course.instructor || '—' }}</div>
          </div>
          <div>
            <span class="text-dimmed">Audience</span>
            <div class="font-medium">{{ course.audience || '—' }}</div>
          </div>
          <div>
            <span class="text-dimmed">Level</span>
            <div class="font-medium">{{ course.level_label || '—' }}</div>
          </div>
          <div>
            <span class="text-dimmed">Duration (weeks)</span>
            <div class="font-medium">{{ course.duration_weeks ?? '—' }}</div>
          </div>
        </div>
      </div>
    </UCard>

    <UCard>
      <template #header>
        <div class="flex items-center justify-between">
          <p class="font-medium">Modules</p>
          <UButton size="sm" icon="i-lucide-plus" @click="addModule" :disabled="!course">Add Module</UButton>
        </div>
      </template>
      <div v-if="loading" class="space-y-2">
        <USkeleton class="h-8 w-full" />
        <USkeleton class="h-8 w-full" />
      </div>
      <div v-else>
        <div v-if="!course?.modules?.length" class="text-dimmed text-sm">No modules yet.</div>
        <div v-else class="space-y-3">
          <div v-for="m in course.modules" :key="m.moduleId" :id="`mod-${m.moduleId}`" class="border border-default rounded-md p-3">
            <div class="flex items-start justify-between gap-2">
              <div>
                <div class="font-medium">{{ m.title || `Module ${m.moduleId}` }}</div>
                <div class="text-sm text-toned truncate max-w-prose">{{ m.text || '—' }}</div>
              </div>
              <div class="flex items-center gap-1">
                <UButton size="xs" color="gray" variant="ghost" :loading="recompiling[m.moduleId]" icon="i-lucide-rotate-ccw" @click.stop="triggerRecompile(m)" />
                <UButton size="xs" color="gray" variant="ghost" icon="i-lucide-eye"
                  :to="{ name: 'app-courses-id-modules-moduleId', params: { id: id || String(route.params.id || ''), moduleId: String(m.moduleId) } }"
                  @click.stop
                />
                <UButton size="xs" color="gray" variant="ghost" icon="i-lucide-pencil" @click.stop="openModuleEdit(m)" />
              </div>
            </div>
            <div v-if="inlineEditingId === m.moduleId" class="mt-3 pt-3 border-t border-default">
              <div class="rounded-lg border border-default bg-muted/20 p-4">
                <div class="flex items-center justify-between gap-2 mb-3">
                  <div class="min-w-0">
                    <p class="text-xs text-dimmed">Editing</p>
                    <h3 class="text-lg font-semibold truncate">{{ moduleDraft.title || `Module ${m.moduleId}` }}</h3>
                  </div>
                  <UBadge :label="`#${m.moduleId}`" variant="subtle" />
                </div>
                <UForm :state="moduleDraft" class="space-y-4" @submit.prevent="saveModule">
                  <UFormField label="Title" help="Shown in the module list">
                    <UInput v-model="moduleDraft.title" placeholder="Module title" size="lg" class="w-full" icon="i-lucide-type" />
                  </UFormField>
                  <div class="flex items-center justify-between -mt-1">
                    <UFormField label="Text" help="Markdown supported" />
                    <div class="flex items-center gap-1">
                      <UButton size="xs" :variant="mdMode === 'write' ? 'solid' : 'outline'" @click="mdMode = 'write'">Write</UButton>
                      <UButton size="xs" :variant="mdMode === 'preview' ? 'solid' : 'outline'" @click="mdMode = 'preview'">Preview</UButton>
                      <UButton size="xs" :variant="mdMode === 'split' ? 'solid' : 'outline'" @click="mdMode = 'split'">Split</UButton>
                    </div>
                  </div>
                  <div v-if="mdMode !== 'split'">
                    <UTextarea v-if="mdMode === 'write'" v-model="moduleDraft.text" :rows="18" size="lg" class="w-full min-h-[360px]" autoresize placeholder="# Heading\n\nWrite your content..." />
                    <div v-else class="w-full min-h-[360px] rounded-lg border border-default bg-white dark:bg-gray-900 p-4 overflow-auto prose prose-sm max-w-none" v-html="mdHtml" />
                  </div>
                  <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <UTextarea v-model="moduleDraft.text" :rows="18" size="lg" class="w-full min-h-[360px]" autoresize placeholder="# Heading\n\nWrite your content..." />
                    <div class="w-full min-h-[360px] rounded-lg border border-default bg-white dark:bg-gray-900 p-4 overflow-auto prose prose-sm max-w-none" v-html="mdHtml" />
                  </div>
                  <div class="flex items-center justify-between gap-2">
                    <p class="text-xs text-dimmed">Tip: Press <kbd class="px-1 py-0.5 rounded border">Cmd/Ctrl + S</kbd> to save</p>
                    <div class="flex gap-2">
                      <UButton color="gray" variant="soft" @click="cancelModuleEdit">Cancel</UButton>
                      <UButton :loading="saving" type="submit" icon="i-lucide-save">Save</UButton>
                    </div>
                  </div>
                </UForm>
              </div>
            </div>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Edit Course Panel: ensure not rendered until opened -->
    <ClientOnly>
      <USlideover v-if="editOpen" v-model="editOpen">
        <UCard>
          <template #header>
            <div class="flex items-center justify-between">
              <p class="font-medium">Edit Course</p>
              <UButton icon="i-lucide-x" color="gray" variant="ghost" @click="editOpen = false" />
            </div>
          </template>
          <div class="space-y-4">
            <UForm :state="editDraft" class="space-y-4" @submit.prevent="saveEdit">
              <UFormField label="Title" help="Shown on lists and detail pages.">
                <UInput v-model="editDraft.title" placeholder="Course title" />
              </UFormField>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <UFormField label="Status">
                  <USelect v-model="editDraft.status" :options="[
                    { label: 'Draft', value: 'draft' },
                    { label: 'Ready', value: 'ready' },
                    { label: 'Published', value: 'published' },
                    { label: 'Failed', value: 'failed' },
                  ]" />
                </UFormField>
                <UFormField label="Duration Weeks">
                  <UInput v-model.number="editDraft.duration_weeks" type="number" min="0" />
                </UFormField>
                <UFormField label="Instructor">
                  <UInput v-model="editDraft.instructor" />
                </UFormField>
                <UFormField label="Audience">
                  <UInput v-model="editDraft.audience" />
                </UFormField>
                <UFormField label="Level Label">
                  <UInput v-model="editDraft.level_label" placeholder="Beginner / Intermediate / Advanced" />
                </UFormField>
                <UFormField label="Language">
                  <UInput v-model="editDraft.language" placeholder="en" />
                </UFormField>
                <UFormField label="Category">
                  <UInput v-model="editDraft.category" />
                </UFormField>
                <UFormField label="Age Range">
                  <UInput v-model="editDraft.age_range" placeholder="e.g., 12-18" />
                </UFormField>
              </div>
              <UFormField label="Description">
                <UTextarea v-model="editDraft.description" :rows="6" />
              </UFormField>
              <div class="flex justify-end gap-2">
                <UButton color="gray" variant="soft" @click="editOpen = false">Cancel</UButton>
                <UButton :loading="saving" type="submit">Save</UButton>
              </div>
            </UForm>
          </div>
        </UCard>
      </USlideover>
    </ClientOnly>

    <!-- Viewer moved to dedicated page: /app/courses/:id/modules/:moduleId -->
  </div>
  <NuxtPage v-else />
</template>
