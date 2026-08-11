# Implementation Plan — HYROX Coach

Build vertically. Do not build every table before any workflow works.

## Phase 0 — Repository foundation

### Deliverables
- Next.js + TypeScript + Tailwind application
- FastAPI backend
- uv configuration
- npm scripts
- environment template
- Neon project linkage/config
- Neon Auth configuration
- lint/typecheck/test commands
- Vercel local integration

### Exit criteria
- Next.js renders.
- `/api/health` responds.
- frontend can call backend locally.
- preview deploy succeeds.

---

## Phase 1 — Authentication and team model

### Deliverables
- Neon Auth
- athlete profile
- team creation
- team invitation
- join team
- target event setup

### Screens
- sign in
- onboarding
- create/join team
- basic dashboard shell

### Exit criteria
Two separate accounts can join one team and see each other's display identity.

---

## Phase 2 — Workout logging

This is the first real product vertical.

### Deliverables
- workout CRUD
- HYROX category tagging
- exercise-performance rows
- arbitrary workout support
- team/private visibility
- recent activity feed

### Exit criteria
Both athletes can independently log:
- Parkrun;
- MMA;
- strength/rings;
- walking;
- HYROX-specific work;

and shared entries appear in the team feed.

---

## Phase 3 — Progress analytics

### Deliverables
- weekly workout totals
- category coverage
- running history
- 5 km performance trend
- exercise progression
- station metric history
- personal best detection
- team comparison DTO

### Exit criteria
The app answers:
- what have I trained?
- what is improving?
- what have we neglected?
- what is my partner doing?

without AI.

This phase is critical. Do not build the coach before deterministic analytics exist.

---

## Phase 4 — Meals and measurements

### Deliverables
- meal logging
- optional macros
- meal timeline
- measurement logging
- weight trend
- waist trend
- sharing controls

### Exit criteria
Users can log and review these records without forcing them to share measurements.

---

## Phase 5 — Media uploads

### Deliverables
- private S3-compatible object storage
- media metadata
- workout attachments
- meal attachments
- signed rendering
- mobile camera/photo upload

### Exit criteria
A user can attach a Parkrun screenshot to a run and a photo to a meal.

---

## Phase 6 — AI extraction

### Deliverables
- workout screenshot extraction
- meal photo understanding
- extraction confidence
- confirmation/edit screen
- extracted-record provenance

### Exit criteria
A Parkrun screenshot can produce a candidate workout result that the user confirms before saving.

Meal-photo output clearly communicates uncertainty.

---

## Phase 7 — AI Coach V1

### Deliverables
- deterministic CoachContext builder
- workout insight
- weekly athlete review
- weekly team review
- structured coach schema
- insight persistence
- coach UI
- AI eval suite

### Exit criteria
The coach can cite real trends and say "insufficient data" when warranted.

---

## Phase 8 — HYROX-specific intelligence

### Deliverables
- event countdown
- category coverage by race demand
- compromised-running tracking
- joint session tracking
- station split notes
- team strengths/gaps
- simulation history
- taper/race-week mode

### Exit criteria
The app feels unmistakably HYROX-specific rather than like a generic fitness tracker with an AI chat window.

---

## Phase 9 — Product hardening

### Deliverables
- PWA support
- responsive QA
- error monitoring
- rate limiting
- data export/deletion
- accessibility
- performance
- production RLS review
- seed/demo data isolated from production

---

# Immediate build order

Implement these first, in this exact order:

1. Scaffold repository.
2. Configure Neon Database and Neon Auth.
3. Implement auth.
4. Implement athlete profile.
5. Implement team + invite.
6. Implement target event.
7. Implement workout schema.
8. Implement workout form.
9. Implement team activity feed.
10. Implement running/exercise analytics.

**Do not start the AI coach before Step 10.**

The intelligence layer will be materially better when it has a trustworthy metrics layer to reason over.

## Phase 4A — Nutrition counter and steps
After base meal/measurement CRUD:

### Nutrition
- effective-dated calorie/macro targets
- daily deterministic totals
- consumed vs target UI
- estimated-vs-confirmed distinction

### Steps
- manual daily step entry
- weekly totals/average
- sharing controls
- future-source field

Do not build native health integrations in MVP.

---

## Phase 4B — Cindy
Add the one pre-built workout:
- 20-minute timer
- round/partial-rep logging
- completion summary
- calorie source/estimate
- progression analytics

Cindy must use the normal workout model plus a dedicated result extension.
