# Cursly — the fastest way to create courses.

A single-screen marketing landing page built with Nuxt 4.1.1, Nuxt UI v4, Tailwind CSS v4 and TypeScript. Optimized to route visitors to a live demo, with clear value props, confidence cues, accessible visuals, and fast interactions.

Presentation in presentation folder - Cursly.pdf

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

### Rendering Strategy

- Landing/marketing routes are SSR/SSG (pre-rendered) for speed and SEO.
- Application (Teacher Hub) routes under `/app/**` are client-rendered only (no SSR).
  - Enforced via `definePageMeta({ ssr: false })` on app pages and `routeRules['/app/**'] = { ssr: false, prerender: false }` in `nuxt.config.ts`.
  - Server middleware avoids SSR redirects on `/app/**`; auth checks happen client-side after Supabase session initializes.

### Teacher Hub (Dashboard + Courses)

New authenticated area for teachers:

- `GET /app/dashboard` — Dashboard with stats, welcome CTA, and global "Create Course" action.
- `GET /app/courses/list` — Courses table (title, progress, status, created/updated) with "Create Course".
- `GET /app/courses/[id]` — Course detail view with overview and modules; includes edit actions.

Both pages use a shared layout `layouts/app.vue` (topbar with logo/search/Create Course/avatar + slim left sidebar navigation) powered by Nuxt UI v4 Dashboard components.

Backend is a FastAPI service located in `backend/` (see below).

## Scripts

- `npm run dev` — Start Nuxt in development
- `npm run build` — Production build
- `npm run preview` — Preview the production build locally

## Environment Variables

- None required for the static landing page.
- For auth and user accounts, fill these in `.env` (copy from `sample.env`):

```env
SUPABASE_PROJECT_URL="https://<your-project-ref>.supabase.co"
SUPABASE_API_KEY="<your-supabase-anon-key>"

# Teacher Hub backend
BACKEND_URL="http://localhost:8000"

# Optional Convex configuration for backend
CONVEX_URL="https://<your-space>.convex.cloud"
CONVEX_DEPLOY_KEY=""
CONVEX_USER_BEARER=""

# Optional if you implement your own Google OAuth (not required when using Supabase's Google provider)
GOOGLE_OAUTH_ID=""
GOOGLE_OAUTH_SECRET=""
```

Do not commit real secrets. `.env` is already gitignored.

### Supabase Auth (Email + Google)

This project integrates Supabase Auth using `@nuxtjs/supabase`:

- Email sign up with confirmation link
- Email sign in with password
- Google sign-in via Supabase OAuth provider

Routes:
- `GET /auth` — UI for sign up/sign in (email + Google)
- `GET /confirm` — Callback to exchange the auth `code` for a session

Supabase module reads runtime config from `runtimeConfig.public.supabase` (wired to `SUPABASE_PROJECT_URL` and `SUPABASE_API_KEY`).

#### Configure in Supabase Dashboard

1. Auth > URL Configuration:
   - Add Redirect URLs: `http://localhost:3010/confirm` (dev) and your production `https://your-domain/confirm`.
2. Auth > Providers > Google:
   - Click Enable and follow instructions to set the Google client ID/secret in the Supabase dashboard.
   - You do NOT need `GOOGLE_OAUTH_ID`/`GOOGLE_OAUTH_SECRET` in this app when using Supabase-managed Google OAuth.

#### Local Setup
1. Copy vars: `cp sample.env .env` and fill values.
2. Install deps and start:

   ```bash
   npm install
   npm run dev
   # http://localhost:3010
   ```

3. Visit `/auth` to sign up/sign in. After confirming email or Google OAuth, you will be redirected to `/confirm` and then to `/`.

## Database: Newsletter subscribers

We store newsletter signups in `public.newsletter_subscribers` via the API route `POST /api/newsletter/subscribe`.

Migration file added:

- `supabase/migrations/20250913_154251_newsletter_subscribers.sql`

This migration:

- Creates the `newsletter_subscribers` table with `id`, `email`, `created_at`.
- Adds a case-insensitive unique index on `email`.
- Enables RLS and allows `anon` inserts (so the API route can upsert with the anon key).
- Blocks `anon` selects by default.

### Apply via Supabase Dashboard (simplest)

1. Open your Supabase project > SQL Editor.
2. Paste the contents of `supabase/migrations/20250913_154251_newsletter_subscribers.sql` and run.
3. Verify the table exists under `Table Editor`.

### Apply via Supabase CLI

Prereqs: Supabase CLI installed and logged in.

```bash
# install (choose one)
npm i -g supabase
# or: brew install supabase/tap/supabase

# authenticate in your terminal
supabase login

# link your project (use the project ref from SUPABASE_PROJECT_URL)
supabase link --project-ref <your-project-ref>

# apply local migrations in ./supabase/migrations to your linked project
supabase db push
```

After this, the footer newsletter form will upsert emails into `public.newsletter_subscribers`.

## Docker & Docker Compose

This repo includes a `docker-compose.yml` configured with profiles to run three modes using the same file:

- Backend only
- Frontend only
- Full stack (backend + frontend)

Prerequisites:
- Docker Desktop 4.30+ or Docker Engine 24+
- Copy env: `cp sample.env .env` and fill at least:
  - `SUPABASE_PROJECT_URL`, `SUPABASE_API_KEY` (for auth-enabled pages)
  - `BACKEND_URL` (frontend uses this; default is `http://localhost:8000`)
  - Optional Convex: `CONVEX_URL` (+ `CONVEX_USER_BEARER` or `CONVEX_DEPLOY_KEY` if needed)

Notes:
- The frontend runs `npm run dev` on port 3010 with hot reload.
- The backend runs Uvicorn on port 8000 with `--reload` and excludes `tmp/manim_runs` from watcher.
- CORS is controlled by `FRONTEND_ORIGIN` (defaults to `http://localhost:3010`).

Profiles and commands:

- Backend only
  ```bash
  docker compose --profile backend up --build
  # API: http://localhost:8000
  ```

- Frontend only (expects a reachable backend at BACKEND_URL)
  ```bash
  # Ensure .env has BACKEND_URL set (defaults to http://localhost:8000)
  docker compose --profile frontend up --build
  # App: http://localhost:3010
  ```

- Full stack (backend + frontend)
  ```bash
  docker compose --profile full up --build
  # Frontend: http://localhost:3010
  # Backend:  http://localhost:8000
  ```

Environment variables used in Docker:

- Frontend container
  - `BACKEND_URL` is injected into Nuxt runtime config (see `nuxt.config.ts` `runtimeConfig.public.backendUrl`).
    - Default in compose is `http://localhost:8000` so the browser can reach the backend mapped on the host.
  - `SUPABASE_PROJECT_URL`, `SUPABASE_API_KEY` are forwarded to the Nuxt module.

- Backend container
  - `FRONTEND_ORIGIN` defaults to `http://localhost:3010` (CORS allowlist).
  - `FRONTEND_ORIGINS` can accept a comma-separated list for multi-origin dev.
  - Convex envs (`CONVEX_URL`, `CONVEX_USER_BEARER`, `CONVEX_DEPLOY_KEY`) are forwarded as-is.
  - Manim tuning envs are supported (see below) but Docker-in-Docker is off by default in compose.

Development volumes:

- The entire repo is mounted into both containers at `/app` for hot reload.
- A named volume `frontend_node_modules` prevents host/guest permission issues and speeds up installs.

Manim in Docker (video generation):

- The backend can attempt to run Manim via Docker or locally. Inside a container you typically cannot spawn nested Docker.
- For compose usage, set the following in `.env`:
  ```env
  MANIM_ENABLE_DOCKER=0
  MANIM_ENABLE_LOCAL=1
  MANIM_LOCAL_FIRST=1
  # Optionally set MANIM_LOCAL_PYTHON or MANIM_LOCAL_BIN if you bake Manim into the image
  ```
- If you do want Docker-based Manim, mount the host Docker socket (advanced, not recommended for general dev):
  ```yaml
  services:
    backend:
      volumes:
        - /var/run/docker.sock:/var/run/docker.sock
  ```
  You may also need to install docker CLI in the backend image.

Stop & clean up:
```bash
# Stop containers
docker compose --profile full down
# Remove volumes if needed (clears node_modules cache volume)
docker volume rm cursly_frontend_node_modules || true
```

## Backend (FastAPI + Convex)

All backend code lives in `backend/`.

Endpoints used by the Teacher Hub UI:

- `GET /courses` — Returns an array of Course objects (see schema below)
- `POST /courses` — Creates a new course with `{ title }`
- `GET /courses/{course_id}` — Returns CourseDetail including optional metadata and modules
- `PATCH /courses/{course_id}` — Updates course basics (title, status, description, etc.)
- `GET /courses/{course_id}/modules` — Lists modules for a course
- `PATCH /courses/{course_id}/modules/{module_id}` — Upserts a module (title, text, outline, etc.)
- `GET /stats` — Returns dashboard stats with recent activity

> **Auth note:** Every Teacher Hub request must include the current Supabase session token (`Authorization: Bearer <access_token>`). The backend derives the user ID from that token and only returns courses/modules owned by that teacher.

Course object schema:

```json
{
  "id": "string",
  "owner_id": "string",
  "title": "string",
  "progress": 0,
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601",
  "status": "draft|published"
}
```

### Run the backend locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
# Exclude Manim temp output to prevent reload loops during /ai/build
uvicorn backend.app.main:app --reload --port 8000 --env-file .env --reload-exclude tmp/manim_runs
```

Frontend expects `BACKEND_URL` (defaults to `http://localhost:8000`).

Tip: set `MANIM_TMP_DIR` in `.env` to a path outside the repo, e.g. `~/.cache/cursly/manim_runs`, so Manim compiles don’t trigger the dev reload.

### Connect FastAPI to Convex

Convex HTTP API docs: https://docs.convex.dev/http-api/

Set `CONVEX_URL` in `.env` to your deployment (e.g., `https://abc-123.convex.cloud`). The backend will call:

- `courses:list` (query)
- `courses:create` (mutation)
- `stats:get` (query)

If `CONVEX_URL` is not set, the backend falls back to an in‑memory list so you can try the UI immediately.

See `backend/README.md` for detailed examples and curl commands.

### Convex Functions (schema + deploy)

This repo includes a minimal Convex app in `convex/` implementing the functions the backend expects:

- `courses:list` (query)
- `courses:create` (mutation)
- `courses:get` (query) — fetch a course by public `id` with detailed fields
- `courses:updateBasic` (mutation) — update basic fields (title/status/metadata)
- `courses:createDetailed` (mutation)
- `courses:updateProgress` (mutation)
- `courses:finalize` (mutation)
- `modules:listByCourse` (query)
- `modules:upsert` (mutation)
- `stats:get` (query)
- `files:generateUploadUrl` (action)

Schema is defined in `convex/schema.ts` with `courses` and `modules` tables (and indexes used by functions).

Setup and deploy:

```bash
# 1) Install dependencies (adds Convex CLI)
npm install

# 2) Initialize Convex (login/select or create a project)
npm run convex:dev
# This starts a local dev server and creates project config; keep it running in another terminal

# 3) Deploy functions & schema to your Convex project
npm run convex:deploy

# 4) Copy envs and set your deployment URL so the backend can call Convex
cp sample.env .env
# Edit .env and set:
#   CONVEX_URL="https://<your-space>.convex.cloud"
```

Verify connectivity:

- Start the backend: `uvicorn backend.app.main:app --reload --port 8000 --env-file .env --reload-exclude tmp/manim_runs`
- Open `GET /convex/diagnostics` — it should show `query_ok: true` and `run_ok: true` once deployed.
- Try `GET /courses`, `POST /courses`, and the new detail routes `GET /courses/{id}`, `PATCH /courses/{id}` from the UI or curl.

### Course Detail & Edit (UI usage)

- Navigate to `Teacher Hub → Courses` and click a row to open `/app/courses/{id}`.
- Use the pencil icon in the top-right to edit title, status, and metadata.
- In the Modules section, use the per-row pencil to edit module title/text. Additional fields (outline/manim/media) can be added similarly.

## Deployment

- Static pre-render is enabled via `routeRules` and works well on:
  - Vercel (recommended)
  - Netlify
  - Any static hosting (after build)
- For SSR features, adjust `routeRules` in [nuxt.config.ts](CodeAny/nuxt.config.ts:0:0-0:0).

Auth routes (`/auth`, `/confirm`) are excluded from prerender to enable dynamic auth flows.

## Troubleshooting

- “nuxt: command not found” when running `npm run dev`:
  - Run `npm install` in the project root first (this installs the local nuxt binary used by npm scripts).
- `npm ERR! code ETARGET @nuxt/ui@^4.0.0`:
  - Use a resolvable version (this project sets `@nuxt/ui` to `latest`).
  - Optionally run: `npm cache verify` and try again.
- Icons not appearing:
  - Use `UIcon` with `name="i-lucide-..."` or `lucide:...`. Ensure `@nuxt/ui` is installed and listed under `modules` in [nuxt.config.ts](CodeAny/nuxt.config.ts:0:0-0:0).
- Nitro dev error `Error: spawn EBADF` on `npm run dev`:
  - This often occurs on Node 22. Use Node 20 LTS. We include `.nvmrc` (`20.18.0`) so you can run `nvm use`.
  - Alternatively, set `engines.node` to Node 20 in your environment or switch via your version manager.

## Roadmap / Customization

- Wire “Try Demo” to a live demo.
- Add waitlist integration (modal/API).
- Add analytics, cookie consent, and legal pages.
- Add user dashboard for course creators (requires authenticated area).

## Notes for the Hackathon

- Supabase documentation is indexed for fast lookup via NIA MCP: [https://supabase.com/docs](https://supabase.com/docs)
- Ask the AI assistant for examples (e.g., `exchangeCodeForSession`, `signInWithOAuth`, `emailRedirectTo`) and it can pull code-level references quickly.
