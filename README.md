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

- [app.vue](CodeAny/app.vue:0:0-0:0) — Wraps the app with `UApp` and configures a global toaster (`position: 'top-right'`, `duration: 3500`, `expand: true`).
- [nuxt.config.ts](CodeAny/nuxt.config.ts:0:0-0:0) — Registers `@nuxt/ui`, includes global CSS, sets `ui.theme.defaultVariants` for consistent sizes/color defaults, enables pre-render rules.
- [app.config.ts](CodeAny/app.config.ts:0:0-0:0) — Nuxt UI runtime color aliases (maps semantic colors to base palettes).
- [assets/css/main.css](CodeAny/assets/css/main.css:0:0-0:0) — Tailwind v4 + Nuxt UI imports and CSS variables for brand tokens, type scale, border radius, container width, and focus states.
- [pages/index.vue](CodeAny/pages/index.vue:0:0-0:0) — The marketing landing page (Hero, Feature highlights, How it works, Integrations, Proof strip, FAQs, Footer).
- [pages/privacy.vue](CodeAny/pages/privacy.vue:0:0-0:0) — Minimal privacy page to avoid broken footer links.
- [package.json](CodeAny/package.json:0:0-0:0) — Scripts and dependencies.

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
- For SSR features, adjust `routeRules` in [nuxt.config.ts](CodeAny/nuxt.config.ts:0:0-0:0).

## Troubleshooting

- “nuxt: command not found” when running `npm run dev`:
  - Run `npm install` in the project root first (this installs the local nuxt binary used by npm scripts).
- `npm ERR! code ETARGET @nuxt/ui@^4.0.0`:
  - Use a resolvable version (this project sets `@nuxt/ui` to `latest`).
  - Optionally run: `npm cache verify` and try again.
- Icons not appearing:
  - Use `UIcon` with `name="i-lucide-..."` or `lucide:...`. Ensure `@nuxt/ui` is installed and listed under `modules` in [nuxt.config.ts](CodeAny/nuxt.config.ts:0:0-0:0).

## Roadmap / Customization

- Wire “Try Demo” to a live demo.
- Add waitlist integration (modal/API).
- Add analytics, cookie consent, and legal pages.
