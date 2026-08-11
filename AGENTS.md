# AGENTS.md — HYROX Coach

This repository uses scoped agents. The root file defines shared rules; subsystem files define implementation responsibilities.

## Agent map

| Agent | File | Responsibility |
|---|---|---|
| Product | `agents/product-agent.md` | Requirements, scope and acceptance criteria |
| Frontend | `agents/frontend-agent.md` | Next.js, Tailwind, mobile UX and dashboards |
| Backend | `agents/backend-agent.md` | FastAPI services and API contracts |
| Data | `agents/data-agent.md` | Neon Postgres schema, RLS and migrations |
| Coach | `agents/ai-coach-agent.md` | AI coaching, multimodal extraction and evaluation |
| Analytics | `agents/analytics-agent.md` | Progress metrics and HYROX readiness calculations |
| QA | `agents/qa-agent.md` | Automated tests and regression control |

## Shared domain model

The key objects are:

- User
- AthleteProfile
- Team
- TeamMembership
- GoalEvent
- Workout
- WorkoutMetric
- ExercisePerformance
- Meal
- Measurement
- MediaAsset
- CoachInsight
- DailySummary
- WeeklySummary
- ReadinessSnapshot

## Required distinction

### Activity data
What happened:
- workouts;
- meals;
- measurements;
- uploaded evidence.

### Derived metrics
What can be calculated:
- running volume;
- training frequency;
- category coverage;
- progression;
- consistency;
- trend direction.

### Coaching interpretation
What the system thinks those metrics mean:
- strengths;
- gaps;
- risk signals;
- recommended next emphasis;
- team coordination observations.

Never merge these three layers into one uncontrolled AI output.

## Core HYROX categories

The app must support at minimum:

- Running
- SkiErg
- Sled Push
- Sled Pull
- Burpee Broad Jumps
- Row
- Farmers Carry
- Sandbag Lunges
- Wall Balls
- Strength
- MMA / Combat
- Mobility
- Recovery
- Walking / Low-intensity aerobic
- Other

A workout can carry more than one category.

## Definition of done

A feature is complete only when:
- permissions are enforced;
- loading, empty and error states exist;
- mobile use is practical;
- relevant tests exist;
- analytics implications are handled;
- AI context changes are intentional;
- documentation is updated if the domain contract changes.

### Special product modules
Read when relevant:
- `CINDY_WORKOUT.md`
- `NUTRITION_TRACKING.md`
- `STEPS_TRACKING.md`

Cindy is the only pre-built workout. Do not introduce additional predefined workouts without an explicit product decision.

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
