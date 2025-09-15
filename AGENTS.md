# Repository Guidelines

## Project Structure & Module Organization
- Frontend (Nuxt 4 + TypeScript): `pages/`, `layouts/`, `composables/`, `assets/`, `server/`, `types/`, root `app.vue`, `nuxt.config.ts`.
  - Auth area lives under `pages/app/**` with shared layout `layouts/app.vue`.
  - Newsletter API: `server/api/newsletter/subscribe.post.ts` (Supabase).
- Backend (FastAPI): `backend/app/main.py`, `backend/app/models.py`, `backend/requirements.txt`. Falls back to in‑memory if Convex is unset.
- Supabase SQL: `supabase/migrations/`.

## Rendering Strategy
- Landing/marketing routes (e.g., `/`, `/privacy`) use SSR/SSG (pre‑rendered) for performance.
- Application routes under `/app/**` are client‑rendered only (no SSR). Nuxt `routeRules` and page `definePageMeta({ ssr: false })` enforce this.
- Server middleware must not redirect `/app/**` during SSR; auth gating occurs client-side after Supabase session initializes.

## Build, Test, and Development Commands
- Env: `cp sample.env .env` then fill values.
- Frontend dev: `npm install` · `npm run dev` (http://localhost:3010)
- Frontend build/preview: `npm run build` · `npm run preview`
- Backend dev: `python3 -m venv .venv && source .venv/bin/activate` · `pip install -r backend/requirements.txt` · `uvicorn backend.app.main:app --reload --port 8000`
- Tests: none configured yet.

### Docker Compose (preferred for unified dev)

Profiles are provided in a single `docker-compose.yml`:

- `backend` — FastAPI only (port 8000)
- `frontend` — Nuxt only (port 3010)
- `full` — backend + frontend

Commands:

- Backend only
  ```bash
docker compose --profile backend up --build
# http://localhost:8000
```

- Frontend only (expects `BACKEND_URL` reachable from the browser)
  ```bash
docker compose --profile frontend up --build
# http://localhost:3010
```

- Full stack
  ```bash
docker compose --profile full up --build
# Frontend: http://localhost:3010
# Backend:  http://localhost:8000
```

Notes:
- The repo is mounted into containers for hot reload.
- `frontend_node_modules` is a named volume to cache installs.
- Manim inside containers should use local mode (disable Docker-in-Docker):
  ```env
MANIM_ENABLE_DOCKER=0
MANIM_ENABLE_LOCAL=1
MANIM_LOCAL_FIRST=1
```

## Coding Style & Naming Conventions
- Vue/TS: 2‑space indent, `script setup`, strict TypeScript. Page files kebab‑case (e.g., `confirm.vue`), composables `useX.ts` (e.g., `useCourses.ts`), types in `types/*.ts` (PascalCase types/interfaces).
- Components (if added): PascalCase filenames and names.
- Styling: Tailwind CSS v4 + Nuxt UI tokens via `assets/css/main.css`.
- Python: PEP 8, 4‑space indent. Pydantic models in PascalCase.

## Testing Guidelines
- Not set up. If adding tests:
  - Frontend: Vitest, files `*.spec.ts`; focus on composables and server handlers.
  - Backend: pytest, files `tests/test_*.py`; cover endpoints and model validation.
  - Prefer deterministic tests; document commands in `package.json`/`Makefile`.

## Commit & Pull Request Guidelines
- Commits are short, imperative summaries (e.g., "Update landing page", "Fix sign‑in"). Group related changes.
- PRs should include:
  - Clear description and rationale; linked issue(s).
  - Screenshots/GIFs for UI changes.
  - Verification steps (commands, URLs), and any env/migration notes.
  - Small, focused scope; avoid unrelated refactors.

## Security & Configuration Tips
- Never commit secrets. `.env` is gitignored and excluded from Docker build context via `.dockerignore`.
- Required envs: `SUPABASE_PROJECT_URL`, `SUPABASE_API_KEY`, `BACKEND_URL`.
- Optional Convex envs: `CONVEX_URL`, `CONVEX_USER_BEARER`, `CONVEX_DEPLOY_KEY`.
- CORS: set `FRONTEND_ORIGIN` (or comma-separated `FRONTEND_ORIGINS`) for allowed origins. Default is `http://localhost:3010`.
- Convex HTTP endpoints are standardized to `/api/query`, `/api/mutation`, and `/api/run/{namespace/function}`; `.convex.site` is normalized to `.convex.cloud`.

## Teacher Hub: Course Detail & Edit

- UI Routes:
  - `/app/courses/list` — table of courses with navigation to detail
  - `/app/courses/[id]` — detail view with overview and modules, includes edit actions (course pencil and module pencils)
- Frontend conventions:
  - Uses Nuxt UI v4: `UCard`, `UButton`, `UBadge`, `UProgress`, `UModal`, `UForm`, `UInput`, `UTextarea`, `USelect`, `USkeleton`.
  - Client-only rendering for `/app/**` via `definePageMeta({ ssr: false })` and `routeRules`.
  - Composables in `composables/useCourses.ts` implement `getCourse`, `updateCourse`, `listModules`, `upsertModule`.
- Backend endpoints:
  - `GET /courses` · `POST /courses`
  - `GET /courses/{course_id}` — CourseDetail
  - `PATCH /courses/{course_id}` — update basics/metadata
  - `GET /courses/{course_id}/modules` — list modules
  - `PATCH /courses/{course_id}/modules/{module_id}` — upsert module
- Convex functions (expected):
  - `courses:list`, `courses:create`, `courses:get`, `courses:updateBasic`, `courses:createDetailed`, `courses:updateProgress`, `courses:finalize`
  - `modules:listByCourse`, `modules:upsert`
  - `stats:get`, `files:generateUploadUrl`

Notes:
- When Convex is not configured (`CONVEX_URL` unset), backend falls back to in-memory courses/modules; edits won’t persist across restarts.
- Field mapping: Convex detailed fields (e.g., `levelLabel`, `durationWeeks`) are normalized in the API to snake_case (`level_label`, `duration_weeks`).
