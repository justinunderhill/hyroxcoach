# API Contract — HYROX Coach

Prefix backend endpoints with `/api`.

Exact implementation may evolve, but domain semantics should remain stable.

## Authentication

All protected routes require a valid Neon Auth bearer token.

FastAPI validates the token against `NEON_AUTH_JWKS_URL` and derives user identity from the verified token subject.

Never accept authoritative `user_id` from the client body.

## Profiles

### GET `/api/me`
Return the verified Neon Auth identity, nullable athlete profile and active teams. A signed-in user who has not completed onboarding receives `profile: null` rather than a fabricated profile.

### PATCH `/api/me`
Create or update editable profile fields for the verified token subject. Initial creation requires display name and timezone. Optional onboarding bodyweight/waist values create a private measurement record.

## Teams

### POST `/api/teams`
Create a team.

### GET `/api/teams/{team_id}`
Return team metadata if requester is a member.

### POST `/api/teams/{team_id}/invites`
Create partner invite.

### POST `/api/team-invites/{token}/accept`
Accept invite.

### GET `/api/teams/{team_id}/dashboard`
Return deterministic team dashboard DTO.

## Workouts

### POST `/api/workouts`
Create workout.

Example:

```json
{
  "occurred_at": "2026-08-08T06:00:00+02:00",
  "title": "Parkrun",
  "activity_type": "running",
  "category_slugs": ["running"],
  "duration_minutes": 28,
  "distance_km": 5,
  "rpe": 8,
  "visibility": "team",
  "notes": "Strong finish."
}
```

### GET `/api/workouts`
Filters:
- from
- to
- team_id
- category
- athlete
- visibility as permitted

### GET `/api/workouts/{id}`
Authorized detail.

### PATCH `/api/workouts/{id}`
Owner only.

### DELETE `/api/workouts/{id}`
Owner only.

### POST `/api/workouts/{id}/performances`
Add exercise performance.

## Meals

### POST `/api/meals`
Create meal.

### GET `/api/meals`
Authorized personal/team history.

### PATCH `/api/meals/{id}`
Owner only.

### DELETE `/api/meals/{id}`
Owner only.

## Measurements

### POST `/api/measurements`
Create measurement.

### GET `/api/measurements`
Personal history unless explicit team visibility is requested and permitted.

### DELETE `/api/measurements/{id}`
Owner only.

## Media

### POST `/api/media/upload-intent`
Return signed/authorized storage target.

### POST `/api/media/{id}/extract`
Request AI extraction.

Body:
```json
{
  "extraction_type": "workout"
}
```

### POST `/api/media/{id}/confirm`
Confirm or correct extracted data.

Confirmation must not automatically create duplicate workout/meal entries.

## Analytics

### GET `/api/analytics/me`
Parameters:
- range
- category

Returns deterministic metrics and trends.

### GET `/api/analytics/team/{team_id}`
Returns:
- per-athlete metrics;
- combined coverage;
- progress signals;
- documented gaps.

## Coach

### GET `/api/coach/daily`
Return current user's latest daily coach summary.

### POST `/api/coach/workout/{workout_id}`
Generate/re-generate workout-specific insight.

### GET `/api/coach/weekly`
Return weekly athlete review.

### GET `/api/coach/team/{team_id}/weekly`
Return team coaching review.

### POST `/api/coach/ask`
Optional conversational coach endpoint.

Request should include a bounded question. Backend injects authorized context.

## Error format

Use a consistent shape:

```json
{
  "error": {
    "code": "WORKOUT_NOT_FOUND",
    "message": "Workout not found.",
    "request_id": "..."
  }
}
```

Do not leak existence of unauthorized records through distinguishable error messages where that creates a privacy issue.

## Cindy
### POST `/api/workouts/cindy/start`
Optional resilient start timestamp.

### POST `/api/workouts/cindy/complete`
Create workout + Cindy result atomically.

### GET `/api/analytics/cindy`
Return latest result, personal best, history and change from prior attempt.

## Nutrition targets
### GET `/api/nutrition/targets`
Return active target.

### POST `/api/nutrition/targets`
Create a new effective-dated target.

### GET `/api/nutrition/daily`
Return deterministic daily calories/macros vs active target.

## Steps
### PUT `/api/steps/{date}`
Create/update current user's daily steps.

### GET `/api/steps`
Return authorized step history.
