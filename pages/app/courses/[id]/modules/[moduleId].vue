<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from '#app'
import { useToast } from '#imports'
import type { Module } from '~/types/course'
import { useCourses } from '~/composables/useCourses'

definePageMeta({ layout: 'app', ssr: false })

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { getModule, getConvexFileUrl, listModules } = useCourses()

const courseId = computed(() => String(route.params.id || ''))
const moduleId = computed(() => String(route.params.moduleId || ''))

const loading = ref(true)
const mod = ref<Module | null>(null)
const videoUrl = ref<string | null>(null)
const imageUrl = ref<string | null>(null)
const modules = ref<Module[]>([])

function escapeHtml(s: string) {
  return s.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;')
}
function inlineMd(s: string) {
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/(^|\W)\*(?!\s)([^*]+?)\*(?!\w)/g, '$1<em>$2</em>')
  s = s.replace(/`([^`]+?)`/g, '<code class="px-1 py-0.5 rounded bg-muted/50 border">$1</code>')
  return s
}
function renderMarkdown(src: string): string {
  const parts = (src || '').split(/```/)
  let html = ''
  for (let i = 0; i < parts.length; i++) {
    const chunk = parts[i]
    if (i % 2 === 1) { html += `<pre class=\"rounded-md border border-default p-3 overflow-auto\"><code>${escapeHtml(chunk)}</code></pre>`; continue }
    const lines = chunk.split(/\r?\n/)
    let inList = false
    for (const raw of lines) {
      const line = raw
      if (!line.trim()) { if (inList) { html += '</ul>'; inList = false } continue }
      const h = line.match(/^(#{1,6})\s+(.*)$/)
      if (h) { if (inList) { html += '</ul>'; inList = false }; const lvl = h[1].length; const t = h[2]; html += `<h${lvl} class=\"mt-4 mb-2 font-semibold\">${inlineMd(escapeHtml(t))}</h${lvl}>`; continue }
      const li = line.match(/^\s*[-*+]\s+(.*)$/)
      if (li) { if (!inList) { html += '<ul class=\"list-disc pl-6 my-2 space-y-1\">'; inList = true }; html += `<li>${inlineMd(escapeHtml(li[1]))}</li>`; continue }
      if (inList) { html += '</ul>'; inList = false }
      html += `<p class=\"mb-3 leading-7\">${inlineMd(escapeHtml(line))}</p>`
    }
    if (inList) { html += '</ul>'; inList = false }
  }
  return html
}
const mdHtml = computed(() => renderMarkdown(String(mod.value?.text || '')))

async function load() {
  loading.value = true
  try {
    const data = await getModule(courseId.value, moduleId.value)
    mod.value = data
    // Resolve media URLs if present
    try {
      if ((data as any).videoStorageId) videoUrl.value = await getConvexFileUrl((data as any).videoStorageId as string)
      if ((data as any).imageStorageId) imageUrl.value = await getConvexFileUrl((data as any).imageStorageId as string)
    } catch {}
    // Fetch modules list (for prev/next)
    try {
      const list = await listModules(courseId.value)
      // Sort by numeric moduleId if possible, else lexicographic
      modules.value = [...list].sort((a, b) => {
        const na = parseInt(String(a.moduleId), 10)
        const nb = parseInt(String(b.moduleId), 10)
        if (Number.isFinite(na) && Number.isFinite(nb)) return na - nb
        return String(a.moduleId).localeCompare(String(b.moduleId))
      })
    } catch {}
  } catch (e) {
    toast.add({ title: 'Module not found', color: 'red' })
  } finally { loading.value = false }
}

onMounted(load)

watch(() => route.params.moduleId, () => load())
watch(() => route.params.id, () => load())

const currentIndex = computed(() => modules.value.findIndex(m => String(m.moduleId) === moduleId.value))
const prevId = computed(() => currentIndex.value > 0 ? String(modules.value[currentIndex.value - 1]?.moduleId || '') : '')
const nextId = computed(() => (currentIndex.value >= 0 && currentIndex.value < modules.value.length - 1) ? String(modules.value[currentIndex.value + 1]?.moduleId || '') : '')

function goPrev() {
  if (!prevId.value) return
  router.push({ name: 'app-courses-id-modules-moduleId', params: { id: courseId.value, moduleId: prevId.value } })
}
function goNext() {
  if (!nextId.value) return
  router.push({ name: 'app-courses-id-modules-moduleId', params: { id: courseId.value, moduleId: nextId.value } })
}
</script>

<template>
  <div class="p-2 sm:p-4 lg:p-6 space-y-4 sm:space-y-6">
    <div class="flex items-center justify-between gap-2">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <UButton icon="i-lucide-arrow-left" variant="ghost" color="gray" @click="router.push(`/app/courses/${courseId}`)" />
          <p class="text-xs text-dimmed truncate">Module</p>
        </div>
        <h1 class="mt-1 text-xl sm:text-2xl lg:text-h3 font-semibold text-highlighted truncate">
          {{ mod?.title || 'Loading…' }}
        </h1>
      </div>
      <div class="flex items-center gap-1">
        <UButton icon="i-lucide-chevron-left" variant="ghost" color="gray" :disabled="!prevId" @click="goPrev" />
        <UButton icon="i-lucide-chevron-right" variant="ghost" color="gray" :disabled="!nextId" @click="goNext" />
      </div>
    </div>

    <UCard>
      <div v-if="loading" class="space-y-3">
        <USkeleton class="h-48 w-full" />
        <USkeleton class="h-6 w-1/2" />
        <USkeleton class="h-4 w-2/3" />
      </div>
      <div v-else-if="mod" class="space-y-5">
        <div class="space-y-3">
          <div v-if="videoUrl" class="aspect-video w-full rounded-lg overflow-hidden border">
            <video :src="videoUrl || undefined" controls class="w-full h-full bg-black" />
          </div>
          <div v-else class="rounded-lg border border-dashed p-6 text-center text-sm text-dimmed">
            <UIcon name="i-lucide-video" class="inline-block mr-1" />
            No video available
          </div>
          <div v-if="imageUrl" class="w-full">
            <img :src="imageUrl || undefined" class="rounded-lg border w-full" alt="Module image" />
            <p v-if="(mod as any).imageCaption" class="text-xs text-dimmed mt-1">{{ (mod as any).imageCaption }}</p>
          </div>
        </div>

        <div v-if="mod.outline?.length" class="space-y-2">
          <p class="text-sm text-dimmed uppercase tracking-wide">Outline</p>
          <ul class="list-disc pl-6 space-y-1">
            <li v-for="(item, i) in mod.outline" :key="i">{{ String(item) }}</li>
          </ul>
        </div>

        <div class="prose prose-sm sm:prose-base max-w-none" v-html="mdHtml" />
      </div>
      <div v-else class="text-sm text-dimmed">Module not found.</div>
    </UCard>
  </div>
</template>
