# Cursly — the fastest way to create courses.

A single-screen marketing landing page built with Nuxt 4.1.1, Nuxt UI v4, Tailwind CSS v4 and TypeScript. Optimized to route visitors to a live demo, with clear value props, confidence cues, accessible visuals, and fast interactions.

## Stack

- Nuxt.js 4.1.1 (TypeScript, SSG-ready)
- Nuxt UI v4 (UApp, UContainer, UCard, UButton, UAccordion, UBadge, UIcon, useToast)
- Tailwind CSS v4 (CSS-first design tokens via @theme)
- Icons via Nuxt UI/Iconify
- Pre-render enabled for a fast, static landing page

## Quick Start

- Node: 18.20+ (recommended: latest LTS)
- Package manager: npm (pnpm/yarn/bun also work)

Install dependencies:
```bash
npm install
```

Start dev server:
```bash
npm run dev
# http://localhost:3010
```

Build for production:
```bash
npm run build
```

Preview the production build locally:
```bash
npm run preview
# http://localhost:3010
```

Deployment (typical):
- Vercel or Netlify: Connect the repo, set Build Command to `npm run build`, and let Nuxt handle the output directory.
- Cloud Run/other: Build and serve the generated output via a Node server or static hosting (pre-rendered).

## Project Structure

- [app.vue](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/app.vue:0:0-0:0) — Wraps the app with `UApp` and configures a global toaster (`position: 'top-right'`, `duration: 3500`, `expand: true`).
- [nuxt.config.ts](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/nuxt.config.ts:0:0-0:0) — Registers `@nuxt/ui`, includes global CSS, sets `ui.theme.defaultVariants` for consistent sizes/color defaults, enables pre-render rules.
- [app.config.ts](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/app.config.ts:0:0-0:0) — Nuxt UI runtime color aliases (maps semantic colors to base palettes).
- [assets/css/main.css](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/assets/css/main.css:0:0-0:0) — Tailwind v4 + Nuxt UI imports and CSS variables for brand tokens, type scale, border radius, container width, and focus states.
- [pages/index.vue](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/pages/index.vue:0:0-0:0) — The marketing landing page (Hero, Feature highlights, How it works, Integrations, Proof strip, FAQs, Footer).
- [pages/privacy.vue](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/pages/privacy.vue:0:0-0:0) — Minimal privacy page to avoid broken footer links.
- [package.json](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/package.json:0:0-0:0) — Scripts and dependencies.

## Landing Page Details (pages/index.vue)

- Hero
  - Headline: “Cursly — Build a complete course in minutes”
  - Primary CTA: “Try Demo”
  - Secondary CTA: “Join Waitlist”

- Feature highlights
  - Creator hub — one place to set preferences and manage courses
  - AI course builder — auto‑generates syllabus, content, quizzes, assignments, grading
  - Full learning flow — videos (generated/uploaded), assignments, proctored assessments
  - Editing control — review and tweak everything before publishing
  - Integrations — export as SCORM (.zip); LTI for other platforms

- How it works (3 steps)
  - Step 1 — Set preferences (course type, topics, grading, video needs)
  - Step 2 — Cursly generates (syllabus + content, quizzes/exams, assignments + rubrics, videos)
  - Step 3 — Edit & publish, then export a SCORM (.zip) package or integrate via LTI

- Integrations and proof strip
  - SCORM (.zip) export for import into Blackboard, Moodle, Canvas (Instructure), Open edX, Absorb LMS, TalentLMS and other SCORM‑compliant platforms
  - LTI available where supported
  - Infra badges: “Built on Vercel”, “Cloud Run”, “opendata.az”, plus “18 commits/week”.

- FAQs
  - `UAccordion` with 3 items (holiday scheduling, LMS support, privacy).

- Footer
  - Contact: `contact@cursly.app`
  - `Privacy` link (routes to `/privacy`).

## Theming and Design Tokens

- Tokens via Tailwind v4 CSS-first variables in [assets/css/main.css](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/assets/css/main.css:0:0-0:0).
- Brand colors:
  - Primary: `#6C5CE7` (indigo-violet)
  - Accent: `#2FD180` (mint)
  - Neutral text on background: `#0F172A` on `#F8FAFC`
  - Status: Success `#22C55E`, Warning `#F59E0B`, Danger `#EF4444`

- Typography:
  - Family: Inter or Plus Jakarta Sans
  - Base: `14px`
  - h1: `28px`, h2: `22px`, h3: `18px`

- Elevation:
  - Subtle/outline cards, `bg-*` tokens for a flat appearance.
  - `--ui-radius: 0.375rem` for consistent “md” rounding.

- Nuxt UI runtime color aliases ([app.config.ts](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/app.config.ts:0:0-0:0)):
  - Maps semantic colors to base palettes (`primary: 'indigo'`, `neutral: 'slate'`, etc.).
  - Final hex values are enforced via CSS variables.

## Components and Patterns

- Layout: `UContainer`
- Sections: `UCard` (variants `subtle`, `outline`)
- CTAs: `UButton` (primary/neutral, outline variants)
- FAQs: `UAccordion`
- Feedback: Toasts via `useToast` and `UApp`’s toaster provider
- Badges: `UBadge`
- Icons: `UIcon` and icon strings passed to toast

Icons usage:
- `UIcon name="i-lucide-rocket"` works out of the box.
- You can also use `lucide:rocket` and set `mode="svg"` when needed.
- Toasts accept `icon` as a string.

## Accessibility

- Color contrast: AA tokens for text/backgrounds and status.
- Focus states: `:focus-visible` with visible outline/offset.
- Semantics: ARIA labels and roles for buttons, landmarks, accordions.
- Keyboard navigation: All interactive elements are tabbable and focusable.
- Reversibility: “Reset to AI” hints and non-destructive interactions.

## Optimistic UI and Feedback

- “Try Demo” simulates background generation with skeletons and a success toast.
- “Join Waitlist” triggers a non-blocking success toast.
- Wire the CTA to a real URL by updating [onTryDemo()](cci:1://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/pages/index.vue:7:0-23:1):
  ```ts
  // pages/index.vue
  // navigateTo('/demo') or navigateTo('https://your-live-demo-url')
  ```

## Scripts

- `npm run dev` — Start Nuxt in development
- `npm run build` — Production build
- `npm run preview` — Preview the production build locally

## Environment Variables

- None required for the landing page.
- If you add form submissions, analytics, etc., document variables here and never commit secrets.

## Deployment

- Static pre-render is enabled via `routeRules` and works well on:
  - Vercel (recommended)
  - Netlify
  - Any static hosting (after build)
- For SSR features, adjust `routeRules` in [nuxt.config.ts](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/nuxt.config.ts:0:0-0:0).

## Troubleshooting

- “nuxt: command not found” when running `npm run dev`:
  - Run `npm install` in the project root first (this installs the local nuxt binary used by npm scripts).
- `npm ERR! code ETARGET @nuxt/ui@^4.0.0`:
  - Use a resolvable version (this project sets `@nuxt/ui` to `latest`).
  - Optionally run: `npm cache verify` and try again.
- Icons not appearing:
  - Use `UIcon` with `name="i-lucide-..."` or `lucide:...`. Ensure `@nuxt/ui` is installed and listed under `modules` in [nuxt.config.ts](cci:7://file:///Users/computerbox/Documents/CodeAny/Cursly/Cursly/nuxt.config.ts:0:0-0:0).

## Roadmap / Customization

- Wire “Try Demo” to a live demo.
- Add waitlist integration (modal/API).
- Add analytics, cookie consent, and legal pages.
