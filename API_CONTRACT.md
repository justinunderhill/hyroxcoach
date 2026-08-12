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
  "source": "manual",
  "notes": "Strong finish."
}
```

`source` is `manual` (default), `image` (created from a confirmed AI extraction), or `integration`.

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
Create a `media_assets` row and return a short-lived presigned PUT URL for the private R2 bucket.

Body:
```json
{
  "purpose": "workout_evidence",
  "mime_type": "image/jpeg",
  "size_bytes": 842311,
  "visibility": "private",
  "entity_type": "workout",
  "entity_id": "..."
}
```

`entity_type`/`entity_id` are optional but must be provided together. When present, the caller must own the referenced workout/meal/measurement; a `media_links` row is created in the same request. The client uploads the file bytes directly to `upload_url` via `PUT` with `upload_headers`.

### GET `/api/media`
Return media for a batch of entities of one type, with freshly signed short-lived view URLs.

Query:
- `entity_type` (`workout`, `meal`, `measurement`)
- `entity_ids` (comma-separated UUIDs)

Only entities the caller can view (owner, or team-visible) are returned.

### DELETE `/api/media/{id}`
Owner only. Deletes the storage object and cascades linked `media_links` rows.

### POST `/api/media/{id}/link`
Attach an already-uploaded media asset to an entity the caller owns. Idempotent — linking the same asset to the same entity twice is a no-op.

Body:
```json
{
  "entity_type": "workout",
  "entity_id": "..."
}
```

Used after extraction: the media is uploaded and extracted before the workout/meal exists, so linking happens once the record is created.

### POST `/api/media/{id}/extract`
Request AI extraction. Runs synchronously and returns the persisted result, including confidence and any uncertainty notes.

Body:
```json
{
  "extraction_type": "workout"
}
```

Response:
```json
{
  "id": "...",
  "media_asset_id": "...",
  "extraction_type": "workout",
  "model_name": "gpt-4o-mini",
  "status": "succeeded",
  "confidence": 0.82,
  "extracted_data": { "distance_km": 5.0, "duration_seconds": 1691, "...": "..." },
  "user_confirmed": false,
  "confirmed_data": null,
  "error_message": null,
  "created_at": "...",
  "confirmed_at": null
}
```

A model/network failure is recorded with `status: "failed"` and a bounded `error_message` rather than a 5xx — the user can retry or fill the record manually.

### POST `/api/media/{id}/confirm`
Record the user's reviewed/corrected values against a specific extraction result.

Body:
```json
{
  "extraction_result_id": "...",
  "confirmed_data": { "distance_km": 5.1, "...": "..." }
}
```

Confirming never creates or updates a workout/meal itself — it only sets `confirmed_data`/`user_confirmed`/`confirmed_at` on the extraction row. The client takes `confirmed_data` and calls `POST /api/workouts` or `POST /api/meals` exactly once (with `source: "image"`), then `POST /api/media/{id}/link` to attach the evidence. This keeps confirmation from automatically creating duplicate entries.

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
