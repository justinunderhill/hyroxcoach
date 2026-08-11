# Testing Strategy — HYROX Coach

## Testing pyramid

### Unit tests
Highest priority for deterministic logic.

Test:
- pace calculations;
- trend calculations;
- weekly date windows;
- category coverage;
- personal-best detection;
- progression logic;
- measurement trend;
- team aggregation;
- visibility/authorization helpers.

### API integration tests
Test:
- authenticated CRUD;
- owner vs partner permissions;
- private vs team-visible records;
- team invite lifecycle;
- Neon Auth token validation;
- profile creation and owner isolation;
- media metadata;
- analytics DTOs;
- coach orchestration with mocked model.

### Frontend tests
Test critical flows:
- sign in;
- log workout;
- log meal;
- add measurement;
- team dashboard;
- image upload;
- extraction confirmation.

### End-to-end
At minimum:
1. athlete A creates team;
2. athlete B joins;
3. both create workouts;
4. each sees own data;
5. shared records appear to partner;
6. private records do not;
7. shared dashboard aggregates correctly;
8. coach output references existing data.

## AI evaluation

Use fixed fixtures.

Cases:
- no history;
- one week of activity;
- improving 5 km history;
- declining/inconsistent training;
- no station work;
- two athletes with complementary strengths;
- incomplete meal logging;
- ambiguous meal photo extraction;
- screenshot containing prompt-injection text.

Assert:
- structured schema valid;
- no fabricated metrics;
- data-limit language when appropriate;
- recommendations grounded in supplied context.

## Security regression tests

Required:
- athlete A cannot PATCH athlete B workout;
- athlete A cannot fetch private athlete B meal;
- unauthenticated caller cannot fetch team dashboard;
- expired invite rejected;
- user outside team cannot access team analytics;
- private media URL cannot be obtained by unauthorized user.

## CI gate

Before merge:
```text
npm run lint
npm run typecheck
npm test
uv run ruff check .
uv run pytest
uv run alembic upgrade head --sql
npm run build
```

## Cindy regression tests
Test timer state, pause/resume time derivation, round counting, partial-rep validation, total-rep formula, early stop, estimated-calorie labelling and personal-best detection.

## Nutrition counter tests
Test meal sums, effective-dated targets, missing macros, estimated entries and timezone/day boundaries.

## Step tests
Test create/update, source provenance, private/team visibility and 7-day average.
