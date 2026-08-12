# Deployment — HYROX Coach

## Target

Vercel.

Use one GitHub repository and, initially, one Vercel project.

Use Node.js 24 in CI and Python 3.12 for FastAPI.

## Environment variables

Typical server-side variables:

```text
DATABASE_URL=
DATABASE_URL_UNPOOLED=
NEON_AUTH_BASE_URL=
NEON_AUTH_JWKS_URL=
NEON_AUTH_COOKIE_SECRET=
OPENAI_API_KEY=
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=
```

`R2_*` variables configure the private Cloudflare R2 bucket used for media uploads (Phase 5). The bucket must be private; the API issues short-lived presigned PUT/GET URLs rather than exposing objects publicly.

`DATABASE_URL` is the pooled application connection. `DATABASE_URL_UNPOOLED` is reserved for migrations, dumps and administrative operations.

The Neon Auth cookie secret must be at least 32 characters and remain stable within an environment. Never expose database credentials, the cookie secret or model API keys through `NEXT_PUBLIC_*`.

Local setup:
```bash
npx neonctl@latest init
neon env pull
```

The committed `.neon` file identifies the linked organization/project and contains no database password. Pulled secrets belong in ignored `.env` or `.env.local` files.

## Python

Use `uv`.

`pyproject.toml` should define backend dependencies.

Pin a supported Python version through `.python-version` or `pyproject.toml`.

Suggested:
```text
3.12
```

## FastAPI

Expose a FastAPI instance named `app`.

Example:
```python
# api/main.py
from fastapi import FastAPI

app = FastAPI()
```

If repository structure requires it, configure Vercel's Python entrypoint in `pyproject.toml`.

## Development

Normal split dev:
```bash
npm run dev
uv run uvicorn api.main:app --reload --port 8000
```

Production-parity integration:
```bash
vercel dev
```

## Database deployment

- migrations committed;
- production and development use separate Neon branches or projects;
- application queries use the pooled connection;
- migrations use the direct connection;
- RLS enabled before real user data;
- the selected object-storage bucket is private.

## Release sequence

1. CI passes.
2. Database migrations reviewed.
3. Preview deployment tested.
4. Auth flows tested.
5. Both test athlete accounts tested.
6. AI calls verified with production-safe keys/limits.
7. Promote to production.
8. Smoke test core flows.

## Rollback

Every production change should be traceable to Git commit.

Schema migrations should be backward compatible where practical.

Avoid destructive migrations without backup/recovery plan.
