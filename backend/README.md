# Cursly Backend — FastAPI + Convex

This backend powers Teacher Hub pages (`/app/dashboard`, `/app/courses/list`).
It exposes a small FastAPI service that fetches/stores courses in **Convex** via its HTTP Functions API.
For local development without Convex configured, it gracefully falls back to an in‑memory store.

## Endpoints

- `GET /health` — health check
- `GET /courses` — returns an array of Course objects
- `POST /courses` — body `{ "title": string }`, creates and returns a Course
- `GET /stats` — returns dashboard stats:

```json
{
  "total_courses": 34,
  "active_teachers": 12,
  "recent_activity": [
    { "course_id": "C1", "event": "updated", "timestamp": "2024-06-15T10:45:00Z" }
  ]
}
```

## Course Schema

```ts
interface Course {
  id: string
  title: string
  progress: number // 0-100
  created_at: string // ISO 8601
  updated_at: string // ISO 8601
  status: 'draft' | 'published' | string
}
```

## Setup

Requirements: Python 3.10+

1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies

```bash
pip install -r backend/requirements.txt
```

3) Configure env vars (copy from sample and edit as needed)

```bash
cp sample.env .env
# Edit .env and set at least BACKEND_URL and (optionally) CONVEX_URL
```

4) Run the API

```bash
# Exclude Manim temp output to prevent reload loops during /ai/build
uvicorn backend.app.main:app --reload --port 8000 --reload-exclude tmp/manim_runs
```

Tip: set `MANIM_TMP_DIR` (in `.env`) to a path outside the repo, e.g. `~/.cache/cursly/manim_runs`, so Manim compiles don’t trigger the dev reload.

### Manim compilation (videos)

The AI pipeline compiles Manim animations for modules. By default it uses Docker (`manimcommunity/manim:stable`). If Docker is not available or times out, the backend now falls back automatically:

- Try local `manim` binary if installed (e.g., `brew install manim`)
- Else generate a short placeholder MP4 via `ffmpeg` (if available)

Environment switches:

```
# prefer/disable runners
MANIM_ENABLE_DOCKER=1           # set to 0 to skip docker
MANIM_ENABLE_LOCAL=1            # set to 0 to skip local manim
MANIM_ENABLE_PLACEHOLDER=1      # set to 0 to skip placeholder

# tuning
MANIM_DOCKER_IMAGE=manimcommunity/manim:stable
MANIM_DOCKER_INSPECT_TIMEOUT_S=8
MANIM_DOCKER_PULL_TIMEOUT_S=120
MANIM_DOCKER_RUN_TIMEOUT_S=180
MANIM_LOCAL_RUN_TIMEOUT_S=180
MANIM_PLACEHOLDER_SECONDS=5
MANIM_PLACEHOLDER_SIZE=1280x720
```

Common fixes for `Docker inspect timeout`:

- Start Docker Desktop and retry.
- Increase `MANIM_DOCKER_INSPECT_TIMEOUT_S`.
- Or force fallback: set `MANIM_ENABLE_DOCKER=0` to use local/placeholder.
- Ensure `ffmpeg` is installed for placeholder: `brew install ffmpeg`.

## CORS

The app allows CORS from `FRONTEND_ORIGIN` (defaults to `http://localhost:3010`).

## Connect to Convex

Convex HTTP API docs: https://docs.convex.dev/http-api/

Set the following env var(s):

- `CONVEX_URL` — deployment URL, e.g. `https://your-space-123.convex.cloud`
- Optional: `CONVEX_USER_BEARER` for user-authenticated calls, or `CONVEX_DEPLOY_KEY` for admin streaming APIs

Notes:
- Prefer the `.convex.cloud` domain. If you only have a `.convex.site` URL, the client will automatically try a `.convex.cloud` fallback and alternate HTTP endpoints.

The backend expects these Convex function names (you can rename them if you also update the backend):

- Query `courses:list` → returns `Course[]`
- Mutation `courses:create` → args `{ title: string }` → returns `Course`
- Query `stats:get` → returns `{ total_courses, active_teachers, recent_activity }`

Example Convex functions (JavaScript) outline:

```ts
// convex/courses.ts
import { mutation, query } from "convex/server";

export const list = query(async ({ db }) => {
  return await db.query("courses").collect();
});

export const create = mutation(async ({ db }, { title }) => {
  const now = new Date().toISOString();
  const doc = { id: crypto.randomUUID(), title, progress: 0, created_at: now, updated_at: now, status: 'draft' };
  await db.insert("courses", doc);
  return doc;
});
```

```ts
// convex/stats.ts
import { query } from "convex/server";

export const get = query(async ({ db }) => {
  const courses = await db.query("courses").collect();
  return {
    total_courses: courses.length,
    active_teachers: courses.length ? 1 : 0,
    recent_activity: courses.slice(-5).map(c => ({ course_id: c.id, event: 'updated', timestamp: c.updated_at }))
  };
});
```

## Test with curl

```bash
# courses
curl -s http://localhost:8000/courses | jq
curl -s -X POST http://localhost:8000/courses -H 'Content-Type: application/json' -d '{"title":"My first course"}' | jq

# stats
curl -s http://localhost:8000/stats | jq
```
