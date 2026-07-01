# Learn Code

Learn Code is a local, Dockerized programming learning platform. V1 teaches Python with a browser app, CLI, original exercises, adaptive interview-prep practice, and a contained local runner.

## Quick start

```bash
docker compose up --build
```

Then open `http://127.0.0.1:5173`.

## Scope

- Python only in V1.
- Original practice content only.
- Local single-user progress in SQLite.
- Browser and CLI use the same FastAPI backend.
- Learner code runs through runner-broker and short-lived Python containers.
