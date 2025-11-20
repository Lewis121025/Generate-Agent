# Lewis AI System Architecture

_Updated: 2025-11-19_

## 1. System Intent & Scope
Lewis AI System provides a single FastAPI backend (`src/lewis_ai_system/main.py`) that powers two flagship experiences from the refreshed product blueprint:

- **Insight Lab (General Mode)** – an enterprise research assistant that chains Web search, sandboxed Python, knowledge-base recall, structured APIs, and visualization tools to ship discussion-ready insight decks in minutes.
- **Creative Sprint (Creative Mode)** – a staged production pipeline that transforms briefs or full scripts into storyboards, renders, and delivery assets with approvals, QC, and distribution wired in.

Both experiences reuse the same deployment spine (`docker-compose.yml` spins up the `lewis-api` container plus Postgres, Redis, and Weaviate). Business state persists in Postgres, hot data and rate limits sit in Redis, embeddings live in Weaviate, and heavy artifacts stream to S3-compatible storage. This keeps the API stateless, portable, and easy to scale horizontally.

## 2. Experience-Led Entry Points
The architecture mirrors the blueprint’s three value scenes:

1. **Insight Lab** – `/general/sessions` endpoints create and iterate ReAct sessions with budget fences, surfacing tool traces so strategists can audit every step.
2. **Creative Sprint** – `/creative/projects` endpoints manage multi-stage creative lifecycles (Brief → Script → Storyboard → Render → Distribution) with version graphs and shareable outputs.
3. **Unified Governance Console** – analytics, cost, and audit data exposed through REST + internal dashboards allow operations teams to inspect run history, enforce quotas, and export evidence.

Templates, quick-start flows, and guided planners are implemented at the client layer, but every interaction ultimately resolves to the routers above, keeping product flows and architecture tightly coupled.

## 3. Runtime Topology & Deployment
```
Clients (Portal / REST / SDK)
        |
 FastAPI app (lewis-api container)
        |
  ┌───────────────┬────────────────┬────────────────┐
  │               │                │                │
Creative Router  General Router  Governance APIs  Service Endpoints
  │               │                │
Creative workflow  ReAct orchestrator  Usage/cost telemetry
        │               │                │
        │         ┌─────┴─────┐          │
        │         │ Agent Pool│          │
        │         └─────┬─────┘          │
        │               │                │
        └───── Shared services: tooling runtime, sandbox, providers, cost monitor,
              instrumentation, storage adapters, vector DB, Redis cache
```

Supporting containers and scripts:

- **Postgres** (`database.py`) – relational source of truth for projects, conversations, tool executions, budgets, and approvals.
- **Redis** (`redis_cache.py`) – async cache, session memoization, and rate limiting.
- **Weaviate** (`vector_db.py`) – semantic memory with in-memory fallback for tests.
- **Docker entrypoint** (`docker/entrypoint.sh`) – dependency wait, optional `python -m lewis_ai_system.cli init-db`, then `uvicorn` launch.
- **Launcher scripts** (`start.sh`, `start.ps1`) – env bootstrapping, secret generation, compose orchestration, health polling.

## 4. Capability Stack Mapping
| Layer | Modules | Blueprint Alignment |
|-------|---------|---------------------|
| **Foundation** | `config.py`, `auth.py`, `database.py`, `redis_cache.py`, `vector_db.py`, `s3_storage.py` | Multi-tenant config, auth, storage, and data guarantees for both modes |
| **Service Mesh** | `agents.py`, `tooling.py`, `sandbox.py`, `providers.py`, `costs.py`, `cost_monitor.py`, `instrumentation.py` | Agentic primitives, tool orchestration, secure execution, provider abstraction, proactive cost telemetry |
| **Business Logic** | `routers/general.py`, `routers/creative.py`, `general/session.py`, `creative/workflow.py`, repositories | Implements Insight Lab iterations and Creative Sprint stages with budget + approval logic |
| **Experience Layer** | Template/catalog APIs, share endpoints, analytics feeds (surfacing data to portal/UI) | Powers Quick Start, guided planners, share links, run history, and governance dashboards |

## 5. Workflow Lifecycles
### Insight Lab (General Mode)
1. **Create session** – `POST /general/sessions` persists goal, budget, tool whitelist, and governance tags.
2. **Cost pre-check** – budget envelopes (from `costs.py`) validate that the run fits user/team caps.
3. **Iterate** – `POST /general/sessions/{id}/iterate` invokes `_decide_tool`, executes via `ToolRuntime` + `sandbox.py`, records outputs, traces, token counts, and spend.
4. **Completion** – session halts when objectives met, iterations exhausted, or `cost_monitor.py` trips a hard stop; summaries stream back with attached telemetry for dashboards.

### Creative Sprint (Creative Mode)
1. **Blueprint intake** – `POST /creative/projects` stores brief, brand kit, milestone plan, and baseline budget.
2. **Stage orchestration** – `creative/workflow.py` advances tasks (Brief → Script → Storyboard → Render → Distribution), persisting artifacts (`storage.py`/`s3_storage.py`) and linking approvals.
3. **Version graph + share** – every generation writes to Postgres + S3 and updates version trees so users can diff, roll back, or promote to templates/share links.
4. **Distribution** – final assets push to external channels (S3, YouTube, TikTok, Meta, ad platforms) with metadata payloads and governance events for auditing.

## 6. Data & Storage Fabric
1. **Postgres schemas** (`database.py`):
   - Creative: `CreativeProject`, `Script`, `Storyboard`, `GeneratedShot`, `ProjectAsset`, approvals, render queue entries.
   - General: `Conversation`, `ConversationTurn`, tool traces.
   - Shared: `ToolExecution`, `CostBreakdown`, `User`, `VectorEmbedding`, `UserTopic`, `ToolSchemaRegistry`, `CostAnomalyAlert`, `VectorIndexMaintenance`.
2. **Redis** – TTL cache for tool responses, budget memoization, and rate limiting; swaps to in-memory backend during tests.
3. **Vector DB** – Weaviate collections orchestrated by `vector_db.py`; `InMemoryVectorDB` keeps unit tests hermetic.
4. **Artifact storage** – `storage.py` handles local disk, `s3_storage.py` abstracts AWS S3/MinIO; creative renders and downloadable research packs live here.

## 7. Cost Governance & Observability
- **Budget modeling** – `costs.py` assigns project/team/API envelopes; `governance/service.py` resolves hierarchy (Project vs Session).
- **Real-time monitoring** – `cost_monitor.py` streams spend deltas into `instrumentation.py`, which feeds Usage Analytics and triggers soft/hard thresholds.
- **Governance Service** – `governance/service.py` aggregates cost snapshots, audit events, and usage overviews for the console.
- **Telemetry** – structured events tag every tool call, stage transition, render job, and distribution push for the governance console.
- **Health endpoints** – `/healthz` for liveness, `/readyz` for dependency readiness (Postgres/S3/Redis/Weaviate checks).

## 8. Security & Configuration
- **Auth** – `auth.py` centralizes API key hashing, bearer tokens, and optional JWT validation; scopes map to template/run permissions.
- **Secrets & config** – `.env` (and `.env.docker.example`) define `SECRET_KEY`, `API_KEY_SALT`, provider credentials, and trusted hosts; launcher scripts backfill missing secrets during local spins.
- **Network posture** – `TrustedHostMiddleware` + CORS configurables enforce perimeter rules; future reverse proxies can layer on mTLS or WAF policies without code changes.
- **Provider governance** – `config.py` injects credentials for OpenRouter, Runway, Pika, Runware, ElevenLabs, Tavily, Firecrawl, Zapier, S3, etc., ensuring least-privilege tokens per environment.

## 9. Testing & Extensibility
- **Test harness** – `pytest` suites cover auth, providers, creative workflow, general sessions, new features, and cost monitoring; in-memory doubles keep CI isolated from cloud services.
- **Extending tools/providers** – implement new `Tool` subclasses in `tooling.py` or helpers, register with `default_tool_runtime`; provider adapters plug into `providers.py` with shared credential loading.
- **Vector/storage swaps** – `VectorDBManager` toggles between Weaviate and new drivers, while `s3_storage.py` can wrap any S3-compatible endpoint.
- **Surface evolution** – because routers expose clean contracts, product teams can continue iterating on templates, planners, embed SDKs, or governance dashboards without touching core orchestrators.

This refreshed architecture narrative keeps the full technical fidelity of the codebase while aligning terminology, flows, and governance controls with the latest product blueprint.
