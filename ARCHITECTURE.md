# Architecture — HYROX Coach

## 1. Architectural approach

Use a modular monolith.

Do not create microservices for the MVP.

```text
Browser / PWA
      |
      v
Next.js application
      |
      +-----------> Neon Auth
      |
      v
FastAPI API
      |
      +-----------> Neon Lakebase Postgres
      +-----------> Private object storage
      +-----------> LLM / vision provider
```

## 2. Frontend responsibilities

Next.js owns:
- authentication UX;
- onboarding;
- dashboards;
- forms;
- media upload flow;
- charts;
- client-side optimistic UX where safe.

Do not put authoritative analytics logic only in React components.

## 3. Backend responsibilities

FastAPI owns:
- authenticated mutations;
- authorization;
- validation;
- analytics aggregation;
- AI context construction;
- model calls;
- image extraction orchestration;
- coach insight persistence.

## 4. Neon responsibilities

### Auth
Neon Auth owns user identity and sessions. Next.js uses the Neon Auth SDK. FastAPI validates bearer tokens against `NEON_AUTH_JWKS_URL` and derives identity only from the verified token.

### Postgres
Neon Lakebase Postgres stores canonical application records. Use the pooled `DATABASE_URL` for normal API traffic and `DATABASE_URL_UNPOOLED` for migrations, dumps and operations that require session state.

### Branches
Use separate Neon branches or projects for development, preview/test and production. Test migrations away from production before promotion.

### RLS
Postgres RLS provides defence-in-depth around user/team access. If a policy relies on the authenticated subject, FastAPI must set that verified identity in request-scoped transaction context.

## 5. Object storage

Neon Database and Neon Auth do not by themselves provision the MVP's media bucket. The MVP uses Cloudflare R2 (S3-compatible) via `boto3`, accessed through `api/services/storage.py`. Neon Object Storage may be evaluated separately; it is not enabled by the current Database + Auth decision.

## 6. Deployment

Recommended single repository.

Vercel can deploy Next.js and FastAPI together. Configure FastAPI at a recognized Python entry point or via `tool.vercel.entrypoint`.

Suggested shape:

```text
app/              # Next.js
api/
  main.py          # FastAPI app = FastAPI()
```

Use `vercel dev` to validate production-style routing during integration.

## 7. Local development

Initialize/link Neon and pull local environment values:

```bash
npx neonctl@latest init
neon env pull
```

`.neon` contains non-secret project linkage. Keep `.env` and `.env.local` ignored.

Suggested commands:

### JavaScript
```bash
npm install
npm run dev
```

### Python
```bash
uv sync
uv run uvicorn api.main:app --reload --port 8000
```

For full Vercel parity:
```bash
vercel dev
```

A local rewrite/proxy can route `/api/*` appropriately during development if needed.

## 8. Authentication flow

1. User authenticates with Neon Auth through Next.js.
2. Frontend receives session.
3. API requests include access token.
4. FastAPI validates the token signature and claims using `NEON_AUTH_JWKS_URL`.
5. Backend resolves user and team memberships.
6. Authorization is checked before every protected read/write.

Never trust a submitted `user_id`.

## 9. Media flow

Preferred:
1. frontend requests signed upload authorization;
2. client uploads directly to private storage;
3. metadata row is created;
4. optional extraction job is requested;
5. AI extracts candidate fields;
6. user confirms/edit;
7. confirmed record becomes canonical.

For MVP, extraction may run synchronously if latency is acceptable. Keep the service boundary so it can become asynchronous later.

## 10. Analytics pipeline

Canonical tables
→ SQL/application aggregation
→ metric DTO
→ dashboard
→ coach context

The model should receive compact summaries rather than thousands of raw rows.

## 11. AI pipeline

```text
Recent records
    +
historical benchmarks
    +
event target
    +
training plan / category targets
    |
    v
deterministic aggregators
    |
    v
CoachContext
    |
    v
LLM
    |
    v
structured CoachInsight
    |
    v
schema validation
    |
    v
persist + display
```

## 12. Caching

MVP:
- rely on normal DB queries;
- cache expensive team/coach summaries where useful;
- invalidate when relevant data changes.

Avoid introducing Redis without measured need.

## 13. Observability

Log:
- request ID;
- authenticated user ID where safe;
- endpoint;
- latency;
- AI provider latency;
- token usage;
- structured extraction failures;
- validation errors.

Never log raw auth tokens or unnecessary sensitive body data.
