<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

type Primitive = string | number
type Option = Primitive | { label: string; value: Primitive; disabled?: boolean }

const props = withDefaults(defineProps<{
  modelValue?: Primitive | null
  options: Option[]
  label?: string
  placeholder?: string
  disabled?: boolean
  name?: string
  id?: string
  required?: boolean
  help?: string
}>(), {
  modelValue: null,
  placeholder: 'Select…',
  disabled: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Primitive | null): void
  (e: 'change', value: Primitive | null): void
  (e: 'focus'): void
  (e: 'blur'): void
}>()

type Item = { label: string; value: Primitive; disabled?: boolean }
const items = computed<Item[]>(() => props.options.map((o) => {
  if (typeof o === 'object' && o !== null && 'label' in o && 'value' in o) {
    return { label: String((o as any).label), value: (o as any).value as Primitive, disabled: !!(o as any).disabled }
  }
  return { label: String(o as Primitive), value: o as Primitive }
}))

const isOpen = ref(false)
const rootRef = ref<HTMLElement | null>(null)
const listRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLElement | null>(null)
const highlighted = ref<number>(-1)

const selectedIndex = computed(() => items.value.findIndex(i => props.modelValue === i.value))
const selectedLabel = computed(() => selectedIndex.value >= 0 ? items.value[selectedIndex.value].label : '')

function open() {
  if (props.disabled) return
  isOpen.value = true
  highlighted.value = selectedIndex.value >= 0 ? selectedIndex.value : 0
  nextTick(() => {
    const el = listRef.value?.querySelector<HTMLElement>(`[data-index='${highlighted.value}']`)
    el?.focus()
  })
}

function close(focusTrigger = true) {
  isOpen.value = false
  if (focusTrigger) nextTick(() => triggerRef.value?.focus())
}

function toggle() {
  isOpen.value ? close(false) : open()
}

function onOutsidePointerDown(e: PointerEvent) {
  if (!rootRef.value) return
  if (!rootRef.value.contains(e.target as Node)) {
    close(false)
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', onOutsidePointerDown)
})
onUnmounted(() => {
  document.removeEventListener('pointerdown', onOutsidePointerDown)
})

function selectAt(index: number) {
  const item = items.value[index]
  if (!item || item.disabled) return
  emit('update:modelValue', item.value)
  emit('change', item.value)
  close()
}

function onTriggerKeydown(e: KeyboardEvent) {
  if (props.disabled) return
  if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
    e.preventDefault()
    if (!isOpen.value) open()
    else {
      const dir = e.key === 'ArrowDown' ? 1 : -1
      moveHighlight(dir)
    }
  } else if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    toggle()
  } else if (e.key === 'Escape') {
    if (isOpen.value) {
      e.preventDefault()
      close()
    }
  }
}

function moveHighlight(delta: number) {
  if (!items.value.length) return
  let next = highlighted.value
  for (let i = 0; i < items.value.length; i++) {
    next = (next + delta + items.value.length) % items.value.length
    if (!items.value[next].disabled) break
  }
  highlighted.value = next
  nextTick(() => {
    const el = listRef.value?.querySelector<HTMLElement>(`[data-index='${highlighted.value}']`)
    el?.focus()
    el?.scrollIntoView({ block: 'nearest' })
  })
}

function onOptionKeydown(e: KeyboardEvent, index: number) {
  if (e.key === 'ArrowDown') { e.preventDefault(); moveHighlight(1) }
  else if (e.key === 'ArrowUp') { e.preventDefault(); moveHighlight(-1) }
  else if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); selectAt(index) }
  else if (e.key === 'Escape') { e.preventDefault(); close() }
  else if (e.key === 'Tab') { close(false) }
}

watch(() => props.modelValue, () => {
  // Keep highlight in sync with selection when value changes externally
  if (!isOpen.value) highlighted.value = selectedIndex.value
})
</script>

<template>
  <div ref="rootRef" class="w-full">
    <label v-if="label" :for="id" class="block text-xs font-medium text-dimmed mb-1">{{ label }}</label>

    <div
      ref="triggerRef"
      :id="id"
      role="combobox"
      :aria-expanded="isOpen ? 'true' : 'false'"
      aria-haspopup="listbox"
      :aria-disabled="disabled ? 'true' : 'false'"
      :tabindex="disabled ? -1 : 0"
      class="relative w-full rounded-md bg-default text-highlighted ring ring-inset ring-accented focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary px-3 py-2 flex items-center justify-between cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
      :class="disabled ? 'opacity-60 cursor-not-allowed' : 'hover:ring-accented/80'"
      @click="toggle"
      @keydown="onTriggerKeydown"
      @focus="emit('focus')"
      @blur="emit('blur')"
    >
      <span class="truncate select-none" :class="!selectedLabel ? 'text-dimmed' : ''">
        {{ selectedLabel || placeholder }}
      </span>
      <span class="i-lucide-chevron-down shrink-0 text-dimmed ml-2"></span>
      <input v-if="name" type="hidden" :name="name" :value="modelValue ?? ''">
    </div>

    <transition name="fade" appear>
      <ul
        v-if="isOpen"
        ref="listRef"
        role="listbox"
        :aria-activedescendant="highlighted >= 0 ? `${id || 'ms'}-opt-${highlighted}` : undefined"
        class="mt-1 max-h-56 w-full overflow-auto rounded-md bg-default ring ring-default shadow-lg z-50 focus:outline-none"
      >
        <li
          v-for="(item, index) in items"
          :key="`${String(item.value)}-${index}`"
          role="option"
          :id="`${id || 'ms'}-opt-${index}`"
          :data-index="index"
          :aria-selected="index === selectedIndex"
          :tabindex="index === highlighted ? 0 : -1"
          @click="selectAt(index)"
          @keydown="onOptionKeydown($event, index)"
          @mouseenter="!item.disabled && (highlighted = index)"
          class="px-3 py-2 text-sm flex items-center justify-between cursor-pointer focus:outline-none"
          :class="[
            index === highlighted ? 'bg-primary/10' : 'bg-transparent',
            item.disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary/10'
          ]"
        >
          <span class="truncate">{{ item.label }}</span>
          <span v-if="index === selectedIndex" class="i-lucide-check text-primary"></span>
        </li>
      </ul>
    </transition>

    <p v-if="help" class="mt-1 text-xs text-dimmed">{{ help }}</p>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 120ms ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
