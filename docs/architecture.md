# Architecture

Web calls only `/api/v1`. CLI is HTTP-only for learner actions. API is the only SQLite writer. API calls runner-broker. Only runner-broker mounts `/var/run/docker.sock`. `python-runner` is a build-only image for short-lived execution containers.

Content is kind-aware end to end: `/api/v1/content` lists exercises, lessons, and quizzes (`?kind=` filter); `/api/v1/content/{id}` returns a kind-tagged detail. Quiz answers are graded server-side by `POST /api/v1/quizzes/answer` (quiz detail never includes correct choices). Lessons complete via `POST /api/v1/lessons/{id}/complete` and grant no mastery. The adaptive planner emits lesson, quiz, exercise, and review items; browser routes `/lesson/:id` and `/quiz/:id` join `/exercise/:id`.

Learning paths are a `path` content kind under `content/python/paths/`: ordered units referencing existing item ids, validated against the catalog. Completion is derived from existing rollups, never stored. `/api/v1/paths` lists, `/api/v1/paths/{id}` returns the syllabus with per-item status and `next_item_id`, and `POST .../enroll` / `.../unenroll` manage the single active path via progress events. The planner adds a small bonus (0.05) to the enrolled path's current unit; due reviews always outrank it. Browser routes: `/paths` and `/path/:id`; CLI: `paths`, `path`, `enroll`, `unenroll`.

Timed practice: `POST /api/v1/sessions/timed` selects exercises whose concepts are all at practicing mastery (the planner's tier-6 gate) and mints a session id; submissions may carry `timed_session_id` into the event payload. Timing is advisory and client-owned — the browser (`/timed` plus a countdown banner on exercise pages) and CLI (`learn-code timed`) track budgets; nothing blocks a late submission.
