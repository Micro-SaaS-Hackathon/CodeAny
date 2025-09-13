<script setup lang="ts">
</script>

<template>
  <UContainer class="py-12">
    <UCard variant="subtle">
      <template #header>
        <h1 class="text-h2 text-highlighted">Privacy</h1>
      </template>
      <div class="prose prose-neutral max-w-none">
        <p class="text-default">We value your privacy. Your content stays in your workspace and is not used to train models.</p>
        <ul class="list-disc pl-6 text-toned">
          <li>No training on your data</li>
          <li>Exports remain local (CSV/JSON)</li>
          <li>Contact us for deletion requests at <a href="mailto:contact@cursly.app" class="text-primary underline">contact@cursly.app</a></li>
        </ul>
      </div>
    </UCard>
  </UContainer>
</template>
