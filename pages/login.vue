<script setup lang="ts">
import { onMounted } from 'vue'
import { navigateTo } from '#imports'

onMounted(() => {
  navigateTo('/auth', { replace: true })
})
</script>

<template>
  <main class="bg-default text-default min-h-screen">
    <UContainer class="py-10">
      <div class="max-w-md mx-auto">
        <UCard>
          <template #header>
            <div class="flex items-center gap-2">
              <UIcon name="i-lucide-move-right" class="text-primary" aria-hidden="true" />
              <h1 class="text-h3 text-highlighted">Redirecting…</h1>
            </div>
          </template>
          <p class="text-muted">Taking you to the sign in page.</p>
        </UCard>
      </div>
    </UContainer>
  </main>
</template>
