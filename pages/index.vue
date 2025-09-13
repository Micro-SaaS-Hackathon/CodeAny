<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from '#imports'

const toast = useToast()
const isGenerating = ref(false)

async function onTryDemo() {
  isGenerating.value = true
  try {
    // Simulate optimistic background generation with skeletons
    await new Promise((r) => setTimeout(r, 900))
    toast.add({
      title: 'Demo launched',
      description: 'We prefilled a Notion outline and generated a holiday-aware schedule.',
      icon: 'i-lucide-rocket',
      color: 'success'
    })
    // In a real app, navigate to demo route or external live demo
    // navigateTo('/demo')
  } finally {
    isGenerating.value = false
  }
}

const subscribeEmail = ref('')
function onSubscribe() {
  const email = subscribeEmail.value?.trim()
  if (!email || !email.includes('@')) {
    toast.add({ title: 'Enter a valid email', color: 'warning', icon: 'i-lucide-alert-circle' })
    return
  }
  toast.add({
    title: 'Subscribed',
    description: "We'll send product updates and launch news.",
    color: 'primary',
    icon: 'i-lucide-mail-check'
  })
  subscribeEmail.value = ''
}
</script>

<template>
  <div class="min-h-screen bg-default text-default flex flex-col">
    <!-- Navigation -->
    <nav class="sticky top-0 z-50 bg-default/80 backdrop-blur border-b border-default">
      <UContainer class="py-3">
        <div class="flex items-center justify-between">
          <NuxtLink to="/" class="flex items-center gap-2">
            <img src="~/assets/images/cursly-logo-small.png" alt="Cursly logo" class="h-7 w-auto" />
            <span class="font-semibold text-highlighted">Cursly</span>
          </NuxtLink>
          <div class="hidden md:flex items-center gap-6">
            <NuxtLink to="#features" class="text-toned hover:text-highlighted transition-colors">Features</NuxtLink>
            <NuxtLink to="#why-cursly" class="text-toned hover:text-highlighted transition-colors">Why</NuxtLink>
            <NuxtLink to="#how-it-works" class="text-toned hover:text-highlighted transition-colors">How it works</NuxtLink>
          </div>
          <UButton to="/auth" color="primary" label="Get Started" />
        </div>
      </UContainer>
    </nav>

    <!-- Hero Section -->
    <section class="bg-hero border-b border-default">
      <UContainer class="py-16 lg:py-24">
        <div class="text-center max-w-4xl mx-auto">
          <h1 class="text-4xl md:text-6xl lg:text-7xl font-bold text-highlighted mb-6">
            Cursly
          </h1>
          <p class="text-xl md:text-2xl text-muted mb-8 max-w-3xl mx-auto">
            Build courses in minutes
          </p>
          <p class="text-lg text-muted mb-8 max-w-2xl mx-auto">
            Get a ready‑to‑edit generated Course with <strong>generated modules, videos, pictures</strong>, <strong>generated quiz questions</strong>, and <strong>generated assignments with rubrics</strong>. <br></br> Export a <strong>Course</strong> for <strong>Moodle/Canvas/Blackboard</strong>. 
          </p>
          <div class="flex flex-wrap justify-center gap-4 mb-12">
            <UButton
              label="Try Demo"
              color="primary"
              :loading="isGenerating"
              :loading-auto="true"
              icon="i-lucide-rocket"
              size="xl"
              @click="onTryDemo"
            />
            <UButton
              label="See Sample Course"
              color="neutral"
              variant="outline"
              icon="i-lucide-file-text"
              size="xl"
            />
          </div>
          
          <!-- Product visual -->
          <div class="relative max-w-4xl mx-auto">
            <div class="absolute inset-0 bg-gradient-to-r from-primary/20 via-transparent to-primary/20 rounded-2xl"></div>
            <UCard class="relative overflow-hidden border-0 shadow-2xl">
              <div class="bg-gradient-to-br from-primary/5 to-white dark:to-gray-900 p-6">
                <USkeleton class="h-56 w-full rounded-xl" />
              </div>
            </UCard>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- Unique Value (moved up for visibility) -->
    <section id="why-cursly" class="scroll-mt-24 bg-gray-50 dark:bg-gray-900/50 border-b border-default">
      <UContainer class="py-16">
        <p class="text-primary font-medium text-center">Why Cursly</p>
        <h2 class="text-3xl md:text-4xl font-bold text-highlighted text-center mt-2">Unique advantages you won’t get elsewhere</h2>
        <p class="text-muted text-center max-w-3xl mx-auto mt-3">Cursly is built for educators who need results fast without sacrificing quality.</p>
        <div class="mt-10 grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <UIcon name="i-lucide-calendar-range" class="w-5 h-5 text-primary" />
            </div>
            <div>
              <p class="font-semibold">Holiday-aware by default</p>
              <p class="text-muted text-sm">Schedules respect national/academic holidays automatically.</p>
            </div>
          </div>
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <UIcon name="i-lucide-file-text" class="w-5 h-5 text-primary" />
            </div>
            <div>
              <p class="font-semibold">Notion/Markdown ingestion</p>
              <p class="text-muted text-sm">Turn your existing notes into a structured Course Pack.</p>
            </div>
          </div>
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <UIcon name="i-lucide-archive" class="w-5 h-5 text-primary" />
            </div>
            <div>
              <p class="font-semibold">LMS‑ready export</p>
              <p class="text-muted text-sm">One‑click ZIP for Moodle, Canvas, Blackboard and more.</p>
            </div>
          </div>
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <UIcon name="i-lucide-shield-check" class="w-5 h-5 text-primary" />
            </div>
            <div>
              <p class="font-semibold">Privacy‑first</p>
              <p class="text-muted text-sm">Your content stays yours. We don’t train on your data.</p>
            </div>
          </div>
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <UIcon name="i-lucide-badge-check" class="w-5 h-5 text-primary" />
            </div>
            <div>
              <p class="font-semibold">Assessment quality</p>
              <p class="text-muted text-sm">Rubric‑backed assignments and 18+ quiz questions per course.</p>
            </div>
          </div>
          <div class="flex items-start gap-4">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <UIcon name="i-lucide-users" class="w-5 h-5 text-primary" />
            </div>
            <div>
              <p class="font-semibold">Teach or export</p>
              <p class="text-muted text-sm">Run classes in Cursly with enrollment and proctoring—or export.</p>
            </div>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- Features Section -->
    <section id="features" class="scroll-mt-24 bg-gray-50 dark:bg-gray-900/50 border-b border-default">
      <UContainer class="py-16">
        <p class="text-primary font-medium text-center">Core Features</p>
        <h2 class="text-3xl md:text-4xl font-bold text-highlighted text-center mt-2">Everything you need to create professional courses</h2>
        <p class="text-muted text-center max-w-3xl mx-auto mt-3">From AI‑generated content to LMS integration, Cursly handles the heavy lifting so you can focus on teaching.</p>

        <div class="mt-10 grid md:grid-cols-3 gap-6">
          <div class="p-5 rounded-xl border border-default bg-elevated">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-3">
              <UIcon name="i-lucide-brain-circuit" class="w-5 h-5 text-primary" />
            </div>
            <p class="font-semibold">AI Course Generation</p>
            <p class="text-sm text-muted mt-1">Generate course outlines, lessons, quizzes, and assignments with rubrics in minutes.</p>
          </div>
          <div class="p-5 rounded-xl border border-default bg-elevated">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-3">
              <UIcon name="i-lucide-calendar-clock" class="w-5 h-5 text-primary" />
            </div>
            <p class="font-semibold">Smart Scheduling</p>
            <p class="text-sm text-muted mt-1">Holiday‑aware scheduling using national and academic calendars.</p>
          </div>
          <div class="p-5 rounded-xl border border-default bg-elevated">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center mb-3">
              <UIcon name="i-lucide-download" class="w-5 h-5 text-primary" />
            </div>
            <p class="font-semibold">Universal Export</p>
            <p class="text-sm text-muted mt-1">Export ZIP files compatible with Moodle, Canvas, Blackboard, and more.</p>
          </div>
        </div>
      </UContainer>
    </section>

    <!-- How it Works -->
    <section id="how-it-works" class="scroll-mt-24">
      <UContainer class="py-16">
        <p class="text-primary font-medium text-center">Simple Process</p>
        <h2 class="text-3xl md:text-4xl font-bold text-highlighted text-center mt-2">From idea to published course in 3 steps</h2>
        <p class="text-muted text-center max-w-3xl mx-auto mt-3">Our streamlined workflow gets you from concept to classroom-ready content faster than ever.</p>
        <div class="mt-8">
          <UStepper
            class="w-full mx-auto max-w-5xl"
            size="lg"
            :items="[
              { icon: 'i-lucide-settings', title: 'Set Preferences', description: 'Tell us your course topic, target audience, duration, and learning objectives.' },
              { icon: 'i-lucide-sparkles', title: 'AI Generates', description: 'Cursly creates modules, quizzes, assignments, and a holiday-aware schedule.' },
              { icon: 'i-lucide-rocket', title: 'Launch', description: 'Edit anything, then export to your LMS.' }
            ]"
          />
        </div>
      </UContainer>
    </section>

    <!-- CTA Section -->
    <section class="scroll-mt-24 bg-gradient-to-r from-primary/5 to-primary/10">
      <UContainer class="py-12 text-center">
        <h2 class="text-2xl md:text-3xl font-bold text-highlighted">Ready to transform your teaching?</h2>
        <p class="text-muted mt-2 max-w-2xl mx-auto">Join educators who've already discovered the power of AI‑assisted course creation.</p>
        <div class="mt-6 flex flex-wrap justify-center gap-3">
          <UButton to="/auth" size="xl" color="primary" label="Start Creating" />
          <UButton size="xl" color="neutral" variant="outline" icon="i-lucide-play" label="Watch Demo" />
        </div>
      </UContainer>
    </section>

    <!-- Footer -->
    <footer class="mt-auto border-t border-default">
      <UContainer class="py-12 grid gap-10 md:grid-cols-3">
        <div class="flex items-start gap-3">
          <img src="~/assets/images/cursly-logo-small.png" alt="Cursly logo" class="h-6 w-auto mt-1" />
          <div>
            <p class="font-semibold">Cursly</p>
            <p class="text-sm text-muted max-w-xs">AI course builder for educators and teams. Generate complete, LMS‑ready courses in minutes.</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-8">
          <div>
            <p class="font-semibold mb-2">Product</p>
            <ul class="space-y-1 text-sm">
              <li><NuxtLink to="#features" class="text-toned hover:text-highlighted">Features</NuxtLink></li>
              <li><NuxtLink to="#how-it-works" class="text-toned hover:text-highlighted">How it works</NuxtLink></li>
            </ul>
          </div>
          <div>
            <p class="font-semibold mb-2">Resources</p>
            <ul class="space-y-1 text-sm">
              <li><NuxtLink to="#how-it-works" class="text-toned hover:text-highlighted">Import guide</NuxtLink></li>
              <li><a href="mailto:curslyapp@gmail.com" class="text-toned hover:text-highlighted">Contact</a></li>
              <li><a href="#" class="text-toned hover:text-highlighted">Changelog</a></li>
            </ul>
          </div>
          <div>
            <p class="font-semibold mb-2">Company</p>
            <ul class="space-y-1 text-sm">
              <li><a href="#" class="text-toned hover:text-highlighted">About</a></li>
              <li><a href="#" class="text-toned hover:text-highlighted">Careers</a></li>
              <li><a href="#" class="text-toned hover:text-highlighted">Press</a></li>
            </ul>
          </div>
          <div>
            <p class="font-semibold mb-2">Legal</p>
            <ul class="space-y-1 text-sm">
              <li><NuxtLink to="/privacy" class="text-toned hover:text-highlighted">Privacy</NuxtLink></li>
            </ul>
          </div>
        </div>

        <div class="space-y-3 w-full max-w-sm">
          <p class="text-sm text-muted">Get product updates</p>
          <form class="flex items-center gap-2" @submit.prevent="onSubscribe">
            <UInput v-model="subscribeEmail" placeholder="you@school.edu" type="email" class="flex-1" />
            <UButton type="submit" color="primary" label="Subscribe" />
          </form>
          <div class="flex items-center gap-3 text-dimmed">
            <a href="https://x.com/" target="_blank" aria-label="X / Twitter" class="hover:text-highlighted"><UIcon name="i-lucide-twitter" /></a>
            <a href="https://www.linkedin.com/" target="_blank" aria-label="LinkedIn" class="hover:text-highlighted"><UIcon name="i-lucide-linkedin" /></a>
            <a href="https://github.com/" target="_blank" aria-label="GitHub" class="hover:text-highlighted"><UIcon name="i-lucide-github" /></a>
          </div>
          <p class="text-xs text-dimmed">© {{ new Date().getFullYear() }} Cursly. All rights reserved.</p>
        </div>
      </UContainer>
    </footer>
  </div>
</template>
