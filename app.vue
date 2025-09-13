<script setup lang="ts">
const toaster = { position: 'top-right', duration: 3500, expand: true } as const
</script>

<template>
  <UApp :toaster="toaster">
    <NuxtPage />
  </UApp>
</template>
