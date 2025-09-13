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
- Server middleware must not redirect `/app/**` during SSR; auth gating occurs client‑side after Supabase session initializes.

## Build, Test, and Development Commands
- Env: `cp sample.env .env` then fill values.
- Frontend dev: `npm install` · `npm run dev` (http://localhost:3010)
- Frontend build/preview: `npm run build` · `npm run preview`
- Backend dev: `python3 -m venv .venv && source .venv/bin/activate` · `pip install -r backend/requirements.txt` · `uvicorn backend.app.main:app --reload --port 8000`
- Tests: none configured yet.

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
- Never commit secrets. `.env` is gitignored. Required: `SUPABASE_PROJECT_URL`, `SUPABASE_API_KEY`, `BACKEND_URL`; optional Convex vars.
- CORS: frontend `http://localhost:3010`; backend default port `8000`.
