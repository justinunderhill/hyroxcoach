# Security and Privacy — HYROX Coach

## Principle

The fact that users are family/team members does not remove the need for privacy boundaries.

## Authentication

- Neon Auth.
- Validate bearer token server-side.
- Rotate/revoke sessions using provider mechanisms.
- Do not build custom password storage.

## Authorization

Enforce in:
1. FastAPI;
2. Postgres RLS in Neon.

Frontend hiding is not authorization.

FastAPI must validate Neon Auth JWTs against `NEON_AUTH_JWKS_URL`. Database access that relies on RLS must propagate the verified subject into request-scoped transaction context; never trust an identity value submitted in a request body.

## Ownership

A user can modify only their own:
- workouts;
- meals;
- measurements;
- media;
- profile.

Team members may read shared records according to visibility.

## Measurement privacy

Measurements are private by default.

Sharing weight/waist must be an explicit user choice.

## Media

- private storage bucket;
- signed URLs with short expiry;
- validate MIME type;
- set upload size limits;
- strip/avoid relying on unsafe client filenames;
- never expose raw storage paths as public objects.

## AI

Do not send more personal data to model providers than needed.

AI requests should use:
- IDs only when necessary;
- no auth tokens;
- no storage secrets;
- no unrelated personal information.

## Secrets

Server only:
- model API keys;
- Neon database credentials;
- Neon Auth cookie secret;
- webhook secrets if introduced.

Public client:
- only Neon Auth values explicitly documented as browser-safe.

Never commit `.env*` secrets.

## Logs

Do not log:
- bearer tokens;
- service role keys;
- signed media URLs unnecessarily;
- raw meal/measurement bodies unless needed for debugging.

## Input validation

Validate:
- dates;
- numeric ranges;
- file type;
- file size;
- enum values;
- membership;
- ownership.

## Rate limiting

Apply sensible limits to:
- AI coach generation;
- image extraction;
- invite creation;
- authentication-sensitive endpoints.

## Data deletion

Provide a path to:
- delete individual records;
- leave team;
- delete account/data.

Deletion semantics should be documented before public release.
