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

async function onJoinWaitlist() {
  toast.add({
    title: 'Added to waitlist',
    description: 'We\'ll notify you as soon as the beta is ready.',
    icon: 'i-lucide-mail-check',
    color: 'primary'
  })
}

const faqs = [
  {
    label: 'How does the holiday-aware schedule work?',
    content: 'We ingest national/academic calendars and auto-shift due dates. You can override any date inline with one click.'
  },
  {
    label: 'Which LMS are supported?',
    content: 'Export a .zip file and import it into Blackboard, Moodle, Canvas (Instructure), Open edX, Absorb LMS, TalentLMS and other compatible platforms.'
  },
  {
    label: 'Privacy and data handling?',
    content: 'Your content stays in your workspace. We do not train on your data. See Privacy for details.'
  }
] as const
</script>

<template>
  <main id="main" class="bg-default text-default">
    <!-- Skip link for accessibility -->
    <a href="#content" class="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 bg-inverted text-inverted rounded-md px-3 py-2">Skip to content</a>

    <!-- Header -->
    <nav class="sticky top-0 z-40 bg-white/70 dark:bg-white/70 backdrop-blur border-b border-default">
      <UContainer class="py-3">
        <div class="flex items-center justify-between gap-3">
          <NuxtLink to="/" class="flex items-center gap-2 focus:outline-none" aria-label="Cursly home">
            <img src="~/assets/images/cursly-logo-small.png" alt="Cursly logo" class="h-7 w-auto" />
            <span class="font-semibold text-highlighted">Cursly</span>
          </NuxtLink>
          <div class="hidden md:flex items-center gap-4">
            <NuxtLink to="#content" class="text-toned hover:text-highlighted">Features</NuxtLink>
            <NuxtLink to="#how-it-works" class="text-toned hover:text-highlighted">How it works</NuxtLink>
            <NuxtLink to="#teach-with-cursly" class="text-toned hover:text-highlighted">Teach</NuxtLink>
            <NuxtLink to="#import-guide" class="text-toned hover:text-highlighted">Import</NuxtLink>
          </div>
          <div class="flex items-center gap-2">
            <UButton label="Try Demo" color="primary" icon="i-lucide-rocket" @click="onTryDemo" aria-label="Try demo" />
            <UButton to="#teach-with-cursly" variant="outline" label="Join Students" aria-label="Join students" />
            <UButton to="/auth" variant="link" color="neutral" label="Sign in" aria-label="Sign in" />
          </div>
        </div>
      </UContainer>
    </nav>

    <!-- Hero -->
    <section class="bg-hero border-b border-default">
      <UContainer class="py-14">
        <div class="max-w-3xl">
          <h1 class="text-h1 mb-3 text-highlighted">Cursly: Build a complete, AI-powered course, intelligently enriched with real-world data, in minutes.</h1>
          <p class="text-muted mb-6">
            Tell us what you want to teach—Cursly turns your ideas into ready‑to‑edit lessons, activities, and assessments. Start fast, keep full control.
          </p>
          <div class="flex flex-wrap items-center gap-3">
            <UButton
              label="Try Demo"
              color="primary"
              :loading="isGenerating"
              :loading-auto="true"
              icon="i-lucide-rocket"
              size="lg"
              aria-label="Try live demo"
              @click="onTryDemo"
            />
            <UButton
              label="Join Waitlist"
              color="neutral"
              variant="outline"
              icon="i-lucide-mail-plus"
              size="lg"
              aria-label="Join the waitlist"
              @click="onJoinWaitlist"
            />
            <UButton
              label="See how it works"
              color="neutral"
              variant="link"
              to="#how-it-works"
              aria-label="Scroll to how it works"
            />
          </div>
          <div class="mt-4 flex items-center gap-2 text-dimmed">
            <UBadge color="success" variant="soft" :label="'No-code builder'" aria-label="No-code builder" />
            <UBadge color="warning" variant="soft" :label="'Edit before publishing'" aria-label="Edit before publishing" />
          </div>
        </div>
      </UContainer>
    </section>

    <section id="content">
      <UContainer class="py-12">
        <!-- Key features -->
        <div class="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <UCard variant="subtle" class="h-full" aria-labelledby="feat-1">
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-layout-dashboard" class="text-primary" aria-hidden="true" />
                <h2 id="feat-1" class="text-h3 text-highlighted">Creator hub</h2>
              </div>
            </template>
            <p class="text-muted">One place to set preferences and manage all your courses.</p>
          </UCard>
          <UCard variant="subtle" class="h-full" aria-labelledby="feat-2">
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-brain-circuit" class="text-primary" aria-hidden="true" />
                <h2 id="feat-2" class="text-h3 text-highlighted">AI course builder</h2>
              </div>
            </template>
            <p class="text-muted">Auto‑generates syllabus, content, quizzes, assignments and grading.</p>
          </UCard>
          <UCard variant="subtle" class="h-full" aria-labelledby="feat-3">
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-video" class="text-primary" aria-hidden="true" />
                <h2 id="feat-3" class="text-h3 text-highlighted">Full learning flow</h2>
              </div>
            </template>
            <p class="text-muted">Videos (generated/uploaded), assignments and proctored assessments.</p>
          </UCard>
          <UCard variant="subtle" class="h-full" aria-labelledby="feat-4">
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-pencil" class="text-primary" aria-hidden="true" />
                <h2 id="feat-4" class="text-h3 text-highlighted">Editing control</h2>
              </div>
            </template>
            <p class="text-muted">Review and tweak everything before you publish.</p>
          </UCard>
          <UCard variant="subtle" class="h-full" aria-labelledby="feat-5">
            <template #header>
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-plug" class="text-primary" aria-hidden="true" />
                <h2 id="feat-5" class="text-h3 text-highlighted">Integrations</h2>
              </div>
            </template>
            <p class="text-muted">Export as a .zip file. Import into Blackboard, Moodle, Canvas (Instructure), Open edX, Absorb LMS, TalentLMS and more.</p>
          </UCard>
        </div>

        <!-- How it works -->
        <div id="how-it-works" class="mt-12 grid md:grid-cols-3 gap-4" aria-label="How it works">
          <UCard variant="outline" class="h-full">
            <template #header>
              <div class="flex items-center gap-2">
                <UBadge label="Step 1" color="primary" variant="soft" />
                <h3 class="text-h3 text-highlighted">Set your preferences</h3>
              </div>
            </template>
            <div class="space-y-3">
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-sliders" class="text-muted" aria-hidden="true" />
                <span class="text-toned">Course type, topics, grading, video needs</span>
                <UButton color="neutral" size="xs" variant="outline" class="ml-auto" aria-label="Use suggested settings">Use suggested</UButton>
              </div>
              <USkeleton class="h-20 w-full rounded-md" />
            </div>
          </UCard>

          <UCard variant="outline" class="h-full">
            <template #header>
              <div class="flex items-center gap-2">
                <UBadge label="Step 2" color="primary" variant="soft" />
                <h3 class="text-h3 text-highlighted">Cursly generates</h3>
              </div>
            </template>
            <div class="space-y-3">
              <USkeleton v-if="isGenerating" class="h-24 w-full rounded-md" />
              <div v-else class="space-y-2">
                <div class="flex items-center gap-2">
                  <UIcon name="i-lucide-list-tree" class="text-muted" aria-hidden="true" />
                  <span class="text-toned">Syllabus + content</span>
                  <UBadge label="quizzes/exams" color="info" variant="soft" class="ml-auto" />
                </div>
                <div class="flex items-center gap-2">
                  <UIcon name="i-lucide-clipboard-list" class="text-success" aria-hidden="true" />
                  <span class="text-toned">Assignments + rubrics</span>
                  <UBadge label="videos" color="success" variant="soft" class="ml-auto" />
                </div>
              </div>
            </div>
          </UCard>

          <UCard variant="outline" class="h-full">
            <template #header>
              <div class="flex items-center gap-2">
                <UBadge label="Step 3" color="primary" variant="soft" />
                <h3 class="text-h3 text-highlighted">Edit & publish</h3>
              </div>
            </template>
            <div class="space-y-3">
              <div class="flex items-center gap-2">
                <UIcon name="i-lucide-pencil" class="text-muted" aria-hidden="true" />
                <span class="text-toned">Tweak anything, invite students</span>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <UButton label="Download .zip" color="primary" variant="subtle" size="sm" aria-label="Download course as zip file" title="Downloads a .zip file you can import into your LMS" />
                <UButton to="#import-guide" variant="link" color="neutral" size="sm" label="How to import" aria-label="Scroll to import guide" />
              </div>
            </div>
          </UCard>
        </div>

        <!-- Integrations -->
        <div class="mt-12">
          <UCard variant="subtle">
            <template #header>
              <h3 class="text-h3 text-highlighted">Integrations</h3>
            </template>
            <div class="flex flex-wrap items-center gap-2">
              <UBadge color="neutral" variant="soft" label="Blackboard" />
              <UBadge color="neutral" variant="soft" label="Moodle" />
              <UBadge color="neutral" variant="soft" label="Canvas (Instructure)" />
              <UBadge color="neutral" variant="soft" label="Open edX" />
              <UBadge color="neutral" variant="soft" label="Absorb LMS" />
              <UBadge color="neutral" variant="soft" label="TalentLMS" />
              <span class="text-muted ml-2">Export as a .zip file and import into these platforms and more.</span>
            </div>
          </UCard>
        </div>

        <!-- How to import -->
        <div id="import-guide" class="mt-12">
          <UCard variant="subtle">
            <template #header>
              <h3 class="text-h3 text-highlighted">How to import your course</h3>
            </template>
            <div class="grid md:grid-cols-3 gap-4">
              <UCard variant="outline" aria-labelledby="how-bb">
                <template #header>
                  <h4 id="how-bb" class="text-h3 text-highlighted">Blackboard</h4>
                </template>
                <ol class="list-decimal pl-6 text-toned space-y-1">
                  <li>Open your course and go to Content.</li>
                  <li>Choose “Build Content” &gt; “Content Package”.</li>
                  <li>Upload the .zip you downloaded from Cursly.</li>
                  <li>Submit and adjust options if needed.</li>
                </ol>
              </UCard>
              <UCard variant="outline" aria-labelledby="how-moodle">
                <template #header>
                  <h4 id="how-moodle" class="text-h3 text-highlighted">Moodle</h4>
                </template>
                <ol class="list-decimal pl-6 text-toned space-y-1">
                  <li>Open your course and turn editing on.</li>
                  <li>Click “Add an activity or resource”.</li>
                  <li>Upload the .zip from Cursly and save.</li>
                  <li>Adjust attempts and display options as needed.</li>
                </ol>
              </UCard>
              <UCard variant="outline" aria-labelledby="how-canvas">
                <template #header>
                  <h4 id="how-canvas" class="text-h3 text-highlighted">Canvas (Instructure)</h4>
                </template>
                <ol class="list-decimal pl-6 text-toned space-y-1">
                  <li>Go to Course &gt; Settings &gt; “Import Course Content”.</li>
                  <li>Select your .zip from Cursly and start the import.</li>
                  <li>Place the imported module in the course and publish.</li>
                </ol>
              </UCard>
            </div>
            <p class="text-muted mt-4">Note: menu labels vary by LMS version; look for “Import”, “Content Package” or similar. You’ll use the .zip you downloaded from Cursly.</p>
          </UCard>
        </div>

        <!-- Teach with Cursly -->
        <div id="teach-with-cursly" class="mt-12">
          <UCard variant="subtle">
            <template #header>
              <h3 class="text-h3 text-highlighted">Run your classes in Cursly</h3>
            </template>
            <div class="grid md:grid-cols-4 gap-4">
              <UCard variant="outline" aria-labelledby="teach-enroll">
                <template #header>
                  <h4 id="teach-enroll" class="text-h3 text-highlighted">Easy enrollment</h4>
                </template>
                <p class="text-muted">Invite learners by shareable URL or email invitation. Self‑serve registration is frictionless.</p>
              </UCard>
              <UCard variant="outline" aria-labelledby="teach-proctor">
                <template #header>
                  <h4 id="teach-proctor" class="text-h3 text-highlighted">Proctored quizzes</h4>
                </template>
                <p class="text-muted">Organize quizzes and exams with built‑in proctoring controls to protect assessment integrity.</p>
              </UCard>
              <UCard variant="outline" aria-labelledby="teach-lti">
                <template #header>
                  <h4 id="teach-lti" class="text-h3 text-highlighted">Use with your LMS</h4>
                </template>
                <p class="text-muted">Prefer your existing LMS? Download a .zip and import it to your LMS.</p>
              </UCard>
              <UCard variant="outline" aria-labelledby="teach-motivate">
                <template #header>
                  <h4 id="teach-motivate" class="text-h3 text-highlighted">Motivate learners</h4>
                </template>
                <p class="text-muted">Leaderboards and achievement badges keep students engaged and rewarded throughout the course.</p>
              </UCard>
            </div>
          </UCard>
        </div>

        <!-- FAQs -->
        <div class="mt-12">
          <h3 class="text-h2 text-highlighted mb-2">FAQs</h3>
          <UAccordion :items="[
            { label: 'What does Cursly generate?', content: 'A complete course: syllabus & content, quizzes/exams, assignments with rubrics, grading scheme, and videos (generated or uploaded).' },
            { label: 'Can I edit before publishing?', content: 'Yes. You have full control to review and tweak everything before publishing or inviting learners.' },
            { label: 'How do I export or use it with my LMS?', content: 'Download a .zip file and import it into Blackboard, Moodle, Canvas (Instructure), Open edX, Absorb LMS, TalentLMS and more.' }
          ]" />
        </div>
      </UContainer>
    </section>

    <!-- Footer -->
    <footer class="border-t border-default">
      <UContainer class="py-8">
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <p class="text-muted">Questions? <a href="mailto:curslyapp@gmail.com" class="text-primary underline focus:outline-none">curslyapp@gmail.com</a></p>
          <div class="flex items-center gap-3 text-dimmed">
            <NuxtLink to="/privacy" class="underline" aria-label="Privacy policy">Privacy</NuxtLink>
            <span aria-hidden="true">•</span>
            <span>© {{ new Date().getFullYear() }} Cursly</span>
          </div>
        </div>
      </UContainer>
    </footer>
  </main>
</template>
