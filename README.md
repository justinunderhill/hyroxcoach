# HYROX Coach

HYROX Coach is a shared training, nutrition and performance intelligence application for two HYROX Doubles athletes.

Each athlete has an individual account and private profile, can log workouts, meals, body measurements and supporting evidence, while the shared team dashboard shows how both athletes are progressing toward the same HYROX competition.

The product is not intended to be a generic fitness tracker. Its differentiator is the **team intelligence layer**: the application understands the target event, observes both athletes over time, and provides useful coaching feedback based on training consistency, HYROX-specific preparedness, recovery signals, nutrition patterns and performance trends.

## Core product principles

1. **Individual ownership, shared mission**
   - Each athlete logs into a personal account.
   - Personal records belong to that athlete.
   - Data marked as team-visible appears in the shared dashboard.
   - The team shares one target event and preparation plan.

2. **Flexible logging**
   - Do not force users into predefined workouts.
   - A workout can be running, MMA, strength, rings, walking, mobility, HYROX simulation, cycling, recovery work or another activity.
   - HYROX relevance is represented through tags/categories rather than rigid workout templates.

3. **Evidence-friendly**
   - Users can upload screenshots/photos such as Parkrun results, running watches, gym summaries and meal photos.
   - Uploaded media may be attached to workouts, meals or progress entries.

4. **Progress over activity volume**
   - Track whether performance is improving, not merely whether sessions are being logged.
   - Examples: 5 km time, 1 km repeat pace, wall-ball capacity, loaded carry performance, sled performance, strength progression and training consistency.

5. **AI should coach, not decorate**
   - The coach needs context.
   - It should reason over recent history and the target event.
   - It should distinguish insufficient evidence from genuine trends.
   - It should not invent measurements, calories, diagnoses or performance conclusions.

## Recommended stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- npm
- Responsive PWA-friendly web application

### Backend
- FastAPI
- Python
- uv for Python dependency and environment management
- Pydantic
- SQLAlchemy with psycopg

### Data and infrastructure
- Neon Auth
- Neon Lakebase Postgres
- private S3-compatible object storage (provider selected before the media phase)
- Postgres Row Level Security
- Vercel deployment
- GitHub repository

### Intelligence
- LLM access from FastAPI only
- Structured coach inputs
- Structured coach outputs
- Image analysis for supported workout/meal screenshots
- Daily and weekly coaching summaries
- Deterministic metrics calculated outside the model wherever possible

## Suggested repository layout

```text
hyrox-coach/
├── app/                         # Next.js app router
├── components/
├── lib/
├── public/
├── api/                         # FastAPI application
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   └── ai/
├── migrations/                  # Postgres/Alembic migrations
├── seed.sql
├── agents/
├── tests/
│   ├── frontend/
│   └── backend/
├── CLAUDE.md
├── AGENTS.md
├── PLAN.md
├── PRODUCT_REQUIREMENTS.md
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── API_CONTRACT.md
├── AI_COACH.md
├── UX_SPEC.md
├── SECURITY_PRIVACY.md
├── TESTING.md
├── DEPLOYMENT.md
├── pyproject.toml
├── package.json
└── README.md
```

## MVP success criterion

The MVP is successful when two real users can:

- sign into individual profiles;
- join the same HYROX team;
- log arbitrary workouts;
- classify them by HYROX-relevant training category;
- log meals;
- upload supporting images/screenshots;
- record personal weight and waist measurements;
- see their own performance history;
- see a shared team dashboard;
- see their partner's shared activity;
- receive grounded AI coaching based on actual logged data;
- see whether preparation is balanced across the primary HYROX demands.

See `PLAN.md` for implementation order.

## Local development

Prerequisites: Node.js 22+, Python 3.12 and `uv`.

```bash
npm install
uv sync
cp .env.example .env.local
npm run dev
```

When Neon is already linked, use `neon env pull` instead of copying blank database/auth values. In development, Next.js proxies same-origin `/api/*` requests to `API_PROXY_TARGET` (default `http://127.0.0.1:8000`). `NEXT_PUBLIC_API_BASE_URL` can remain blank unless the API is hosted separately.

Local services:

- Next.js: `http://localhost:3000`
- FastAPI health: `http://localhost:8000/api/health`
- FastAPI docs: `http://localhost:8000/api/docs`

Baseline checks:

```bash
npm run lint
npm run typecheck
npm test
uv run ruff check .
uv run pytest
npm run build
```

Database migrations use the direct Neon connection:

```bash
uv run alembic upgrade head
```

Local auth uses a development-only cookie secret. Set a stable, random `NEON_AUTH_COOKIE_SECRET` of at least 32 characters in every deployed environment.

## Added performance modules

### Cindy
Cindy is the only pre-built workout: 20-minute AMRAP of 5 pull-ups, 10 push-ups and 15 air squats, with a built-in timer, round/rep tracking, optional calories burned and progression history. See `CINDY_WORKOUT.md`.

### Nutrition counter
Meal logging includes a daily calorie and macro counter with personal targets for calories, protein, carbohydrates and fat. See `NUTRITION_TRACKING.md`.

### Steps
The MVP supports manual daily steps and future imported step sources. See `STEPS_TRACKING.md`.
