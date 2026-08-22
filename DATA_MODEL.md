# Data Model — HYROX Coach

Neon Lakebase Postgres is the source of truth.

Application-generated primary keys may use UUIDs. Fields that reference an authentication identity must preserve the canonical Neon Auth subject identifier without coercion.

## users

Neon Auth remains canonical for authentication.

Application profile data should not duplicate credentials.

## athlete_profiles

- id
- user_id unique
- display_name
- avatar_path nullable
- timezone
- baseline_5k_seconds nullable
- training_availability jsonb
- created_at
- updated_at

Baseline bodyweight and waist values are stored as private `measurements`, not duplicated on the profile.

## teams

- id
- name
- created_by
- created_at
- updated_at

## team_memberships

- id
- team_id
- user_id
- role (`owner`, `athlete`)
- status (`invited`, `active`, `left`)
- joined_at

Unique:
- team_id + user_id

## team_invites

- id
- team_id
- invited_email nullable
- token_hash
- expires_at
- accepted_at nullable
- created_by

Never store a reusable plain-text invite token.

## goal_events

- id
- team_id
- name
- event_type (`hyrox_singles`, `hyrox_doubles`)
- event_date
- division nullable
- location nullable
- preparation_start_date nullable
- metadata jsonb
- created_at

## workouts

- id
- user_id
- team_id
- occurred_at
- title
- activity_type
- duration_minutes nullable
- distance_km nullable
- rpe nullable
- notes nullable
- visibility (`team`, `private`)
- source (`manual`, `image`, `integration`)
- created_at
- updated_at

Indexes:
- user_id + occurred_at desc
- team_id + occurred_at desc

## workout_categories

Reference table:
- id
- slug
- name
- category_group
- active

Seed categories documented in `AGENTS.md`.

## workout_category_links

- workout_id
- category_id

Unique:
- workout_id + category_id

## exercise_performances

Flexible metric record attached to workout.

- id
- workout_id
- exercise_name
- normalized_exercise_key nullable
- sequence_no
- sets nullable
- reps nullable
- load_kg nullable
- distance_m nullable
- duration_seconds nullable
- pace_seconds_per_km nullable
- calories nullable
- rpe nullable
- metadata jsonb
- notes nullable

Do not force every exercise into the same metric shape.

## meals

- id
- user_id
- team_id
- occurred_at
- meal_type nullable
- description
- calories nullable
- protein_g nullable
- carbs_g nullable
- fat_g nullable
- nutrition_is_estimated boolean default false
- notes nullable
- visibility (`team`, `private`)
- source (`manual`, `image`)
- created_at
- updated_at

## measurements

- id
- user_id
- occurred_at
- weight_kg nullable
- waist_cm nullable
- resting_hr nullable
- notes nullable
- visibility (`private`, `team`)
- created_at

Constraint:
At least one measurement field must be populated.

## media_assets

- id
- user_id
- team_id nullable
- storage_path
- mime_type
- size_bytes
- purpose (`workout_evidence`, `meal_photo`, `measurement`, `other`)
- visibility
- created_at

## media_links

Allows one asset to attach to a domain record.

- id
- media_asset_id
- entity_type (`workout`, `meal`, `measurement`)
- entity_id
- created_at

## extraction_results

- id
- media_asset_id
- extraction_type (`workout`, `meal`)
- model_name
- status
- confidence nullable
- extracted_data jsonb
- user_confirmed boolean
- confirmed_data jsonb nullable
- error_message nullable
- created_at
- confirmed_at nullable

## coach_insights

- id
- scope (`workout`, `daily`, `weekly`, `team_weekly`)
- user_id nullable
- team_id
- period_start nullable
- period_end nullable
- source_record_id nullable
- coach_version
- model_name
- insight_json jsonb
- context_hash
- created_at

## daily_summaries

Prefer materialized/cached records only if needed.

Possible fields:
- user_id
- date
- session_count
- training_minutes
- running_distance_km
- category_counts jsonb
- nutrition_summary jsonb
- measurement_summary jsonb

## readiness_snapshots

Only create after readiness methodology is defined.

Suggested:
- id
- team_id
- snapshot_date
- methodology_version
- metrics jsonb
- explanation jsonb

Never expose an unexplained "AI readiness score".

## Data ownership rules

A row with `user_id` is owned by that user.

Team membership grants read access only according to:
- team match;
- active membership;
- record visibility.

Changing UI filters must never bypass these rules.

## nutrition_targets
- id
- user_id
- effective_from
- calories_target nullable
- protein_g_target nullable
- carbs_g_target nullable
- fat_g_target nullable
- created_at

## daily_steps
- id
- user_id
- date
- steps
- source (`manual`, `health_connect`, `apple_health`, `other_import`)
- visibility (`private`, `team`)
- metadata jsonb
- created_at
- updated_at

Index: user_id + date desc

## cindy_results
- id
- workout_id unique
- user_id
- full_rounds
- extra_pullups
- extra_pushups
- extra_squats
- total_reps
- total_seconds
- completed_as_prescribed
- calories_burned nullable
- calorie_source nullable
- calorie_estimation_version nullable
- created_at
