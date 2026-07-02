# Architecture

Web calls only `/api/v1`. CLI is HTTP-only for learner actions. API is the only SQLite writer. API calls runner-broker. Only runner-broker mounts `/var/run/docker.sock`. `python-runner` is a build-only image for short-lived execution containers.

Content is kind-aware end to end: `/api/v1/content` lists exercises, lessons, and quizzes (`?kind=` filter); `/api/v1/content/{id}` returns a kind-tagged detail. Quiz answers are graded server-side by `POST /api/v1/quizzes/answer` (quiz detail never includes correct choices). Lessons complete via `POST /api/v1/lessons/{id}/complete` and grant no mastery. The adaptive planner emits lesson, quiz, exercise, and review items; browser routes `/lesson/:id` and `/quiz/:id` join `/exercise/:id`.
