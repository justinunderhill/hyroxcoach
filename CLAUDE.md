# CLAUDE.md — HYROX Coach

You are working on HYROX Coach, a two-athlete HYROX Doubles preparation application.

Read these files before modifying production code:

1. `PRODUCT_REQUIREMENTS.md`
2. `ARCHITECTURE.md`
3. `DATA_MODEL.md`
4. `API_CONTRACT.md`
5. `AI_COACH.md`
6. `SECURITY_PRIVACY.md`
7. `TESTING.md`
8. `CINDY_WORKOUT.md`
9. `NUTRITION_TRACKING.md`
10. `STEPS_TRACKING.md`
11. `PLAN.md`

Also read the root `AGENTS.md` and the relevant file under `agents/` for the subsystem being changed.

## Product intent

HYROX Coach is not a generic fitness app.

Its primary job is to answer:

> Are these two athletes becoming more prepared to perform well together in their target HYROX Doubles race?

The application combines:
- individual workout logging;
- meal logging;
- personal measurements;
- uploaded evidence;
- progress analytics;
- shared team visibility;
- HYROX-specific readiness tracking;
- AI coaching.

## Non-negotiable engineering rules

### 1. Never invent user data
Do not fabricate workouts, meals, measurements, calories, scores or dates.

### 2. Source-of-truth calculations are deterministic
Metrics such as:
- weekly training count;
- running distance;
- average pace;
- exercise progression;
- adherence;
- body measurement trends;
- category coverage;

must be calculated in application code or SQL.

The LLM interprets these metrics. It does not calculate the canonical values from unstructured history.

### 3. Preserve raw data
When AI extracts information from a screenshot or meal photo:
- retain the original upload;
- retain the extracted structured result;
- retain extraction confidence;
- allow manual correction;
- do not silently overwrite a user's confirmed record.

### 4. AI is advisory
The AI coach may give training and nutrition feedback but must:
- avoid diagnosis;
- avoid presenting uncertain estimates as fact;
- flag insufficient data;
- recommend professional care when a user reports potentially serious symptoms or injury;
- never encourage extreme caloric restriction, dehydration or unsafe training through pain.

### 5. Protect user boundaries
Users belong to a team but retain individual identities.

A user may only:
- modify their own records;
- see another athlete's records where sharing rules allow it;
- see shared team analytics for teams they belong to.

Enforce permissions at the database/API level, not only in the UI.

### 6. Mobile-first UX
The dominant workflow is logging immediately after:
- a run;
- MMA;
- gym work;
- a walk;
- a meal.

Logging should therefore require minimal taps.

### 7. Do not over-engineer the MVP
Prefer:
- one repository;
- one Next.js app;
- one FastAPI backend;
- Neon Auth and Neon Lakebase Postgres;
- clear service boundaries.

Avoid premature microservices, queues, event buses or agent swarms.

## Coding expectations

### TypeScript
- strict mode;
- no unexplained `any`;
- shared domain types where practical;
- server-side validation for mutations.

### Python
- Python 3.12+;
- type annotations;
- Pydantic schemas;
- services separated from route handlers;
- pytest coverage for core calculations and AI orchestration.

### Database
- migrations committed to source control;
- foreign keys;
- useful indexes;
- timestamps in UTC;
- RLS policies reviewed with every new user-owned table.
- pooled `DATABASE_URL` for application traffic;
- direct `DATABASE_URL_UNPOOLED` for migrations and administrative tasks.

## AI implementation rule

AI calls must flow through a dedicated coach service.

Never scatter direct model calls across route handlers.

Preferred flow:

```text
route
  -> authorization
  -> deterministic data aggregation
  -> coach context builder
  -> model invocation
  -> schema validation
  -> persistence
  -> response
```

## Before declaring work complete

Run:
- frontend lint;
- frontend typecheck;
- frontend tests;
- backend tests;
- migration checks where relevant.

Then report:
1. files changed;
2. behaviour added/changed;
3. tests run;
4. unresolved risks;
5. next recommended task.
