# Poker App — Technology and Deployment Stack

**Status:** Accepted architecture decision  
**Last updated:** 5 October 2026  
**Purpose:** Single source of truth for the poker application's initial technology and deployment choices.

## 1. Product scope

The first release is a private, responsive Texas Hold'em web application for approximately 10–20 users, using virtual chips only.

Initial goals:

- polished desktop and mobile poker table;
- private tables for 2–8 players;
- real-time gameplay;
- reconnect after a temporary connection loss;
- lobby, accounts and hand history;
- smooth card, chip, turn and winner animations;
- low infrastructure cost during development.

The poker application is an independent project. It must not use Eldrion branding, Eldrion domains, Eldrion repositories, Eldrion databases or Eldrion environment variables.

## 2. Accepted technology stack

### 2.1 Frontend

| Area | Decision |
|---|---|
| Framework | Angular with standalone components |
| State | Angular signals for local and game-view state |
| Async streams | RxJS only where streams are a natural fit, especially WebSocket events |
| Change detection | Zoneless Angular |
| Workspace | Nx monorepo |
| Styling | Tailwind CSS, component SCSS and CSS custom properties |
| Major animations | GSAP timelines |
| Small transitions | CSS animations and Angular `animate.enter` / `animate.leave` |
| End-to-end testing | Playwright |
| Rendering model | Standard DOM; no full-canvas game engine in the MVP |

Frontend rules:

- The poker table uses semantic HTML and DOM elements, not a canvas-only scene.
- Animation state must not be the source of truth for game state.
- Prefer `transform` and `opacity` for smooth animations.
- Support responsive desktop and mobile layouts from the beginning.
- Provide reduced-motion and sound on/off settings.
- Do not use the deprecated legacy `@angular/animations` API for new code.
- Do not use a generic UI component library for the poker table itself. Reusable library components may be considered for ordinary forms or dialogs only when they fit the visual system.

### 2.2 Visual direction

The accepted initial direction is a premium dark poker room:

- dark graphite surfaces;
- muted green felt;
- restrained gold accents;
- custom card and chip assets;
- subtle depth, edge lighting and shadows;
- clear active-player, dealer and winner states;
- polished but not flashy casino styling.

GSAP is used for:

- dealing cards;
- 3D card flips;
- moving bets and chips to the pot;
- moving the pot to the winner;
- turn changes and timers;
- highlighting the winning combination;
- player seat enter/leave sequences.

PixiJS may be introduced later only as a decorative layer for advanced particles, lighting or background effects. Phaser and a full PixiJS table implementation are outside the MVP.

### 2.3 Backend

| Area | Decision |
|---|---|
| API framework | FastAPI |
| Realtime transport | Native WebSockets |
| Validation | Pydantic models |
| Game logic | Framework-independent Python package |
| Persistence | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Backend tests | pytest plus property-based tests for poker rules |
| Authentication | Short-lived access token and refresh-token flow using secure cookies |

Backend rules:

- The server is authoritative for all game state.
- The browser sends player intentions such as fold, check, call or raise.
- The server validates the action, advances the hand and broadcasts the resulting public state.
- Private cards are sent only to the player who owns them.
- Clients never decide card order, legal actions, winners, chip balances or side-pot distribution.
- The poker engine must not import FastAPI, SQLAlchemy or WebSocket code.
- Randomness must use a cryptographically secure server-side source and support deterministic test fixtures.
- Persist completed hands and important state transitions; do not use the database as the frame-by-frame live game loop.

### 2.4 Live-state strategy

For the first release:

- exactly one FastAPI process and one Uvicorn worker host a per-table actor that owns live command sequencing and in-process gameplay state;
- PostgreSQL owns durable command identity, committed revisions, recovery information and wallet accounting;
- the client automatically reconnects with bounded exponential backoff;
- a reconnect requests a fresh authoritative snapshot;
- WebSocket messages use typed, versioned event envelopes.

The complete ownership, transaction, ordering, deadline and recovery rules are recorded in [ADR-002: Authoritative poker-table state and serialized commands](adr-002-authoritative-poker-table-state.md).

Redis is intentionally excluded from the first release. It becomes necessary when we run multiple backend instances, need cross-instance pub/sub, or measurements show that a single process is insufficient.

## 3. Repository structure

Use one independent Nx monorepo with a structure similar to:

```text
apps/
  web/                  Angular application
  api/                  FastAPI application
libs/
  frontend/
    game-ui/
    lobby-ui/
    data-access/
    websocket-client/
    shared-ui/
  contracts/            Versioned API/WebSocket contracts
  poker-engine/         Pure Python poker rules and state machine
  backend/
    application/
    persistence/
    realtime/
```

The exact generated folders may change during project initialization, but the boundaries must remain: UI, transport, application logic, persistence and poker engine are separate concerns.

## 4. Accepted deployment stack

| Component | Provider | Initial plan |
|---|---|---|
| Angular frontend | Vercel | Hobby while the project is personal and non-commercial |
| FastAPI and WebSockets | Render | Free during development; smallest suitable always-on paid compute before regular multiplayer use |
| PostgreSQL | Dedicated Supabase project | Free plan initially |
| Static assets | Frontend build or the dedicated Supabase project's Storage | Free initially |
| Source control | New independent GitHub repository | Private initially |
| Domain | None initially | Use provider subdomains |

Expected initial addresses:

```text
https://<poker-project>.vercel.app
https://<poker-api>.onrender.com
wss://<poker-api>.onrender.com/ws
```

Deployment rules:

- Choose the closest matching EU regions offered by Render and Supabase, preferably the same region.
- Configure exact CORS and WebSocket origins; do not use wildcard origins in production.
- Vercel contains only public frontend configuration. Secrets remain in Render or Supabase.
- Render health checks must not mutate game state.
- Production deployment requires automatic database migrations or a documented migration step.
- The frontend and backend are deployed independently from the same repository.
- Preview environments must not connect to the production database by default.

## 5. Environment separation

Maintain separate development, test and production configuration.

Expected frontend variables:

```text
API_BASE_URL
WS_BASE_URL
APP_ENV
```

Expected backend variables:

```text
APP_ENV
DATABASE_URL
JWT_SECRET
ACCESS_TOKEN_TTL_SECONDS
REFRESH_TOKEN_TTL_SECONDS
ALLOWED_ORIGINS
FRONTEND_URL
```

Names may be refined when the configuration module is implemented, but secrets must never be committed.

## 6. Cost and rollout policy

### Development

- Vercel Hobby: free for the personal, non-commercial MVP.
- Render Free: acceptable while developing and testing.
- Supabase Free: acceptable for the first database and assets.
- Custom domain: not purchased yet.

Render Free can sleep after inactivity, so its cold start is acceptable only during development.

### Private playable MVP

Before scheduled games with real users:

- move FastAPI to the smallest suitable always-on Render compute plan;
- keep Vercel and Supabase free while their terms and quotas remain suitable;
- measure memory, CPU, WebSocket stability and database growth;
- add a custom domain only after the application has a final name.

### Scaling trigger

Revisit the architecture only when evidence shows one of the following:

- multiple backend instances are required;
- active WebSocket connections approach current service limits;
- one process cannot reliably own all active tables;
- database or storage quotas are approaching their limits;
- the project becomes commercial;
- availability requirements become stricter than a hobby MVP.

At that point consider Redis/pub-sub, multiple backend instances, paid database services and commercial hosting plans.

## 7. Explicit MVP exclusions

Do not introduce these without a separate architecture decision:

- Eldrion domains, branding or infrastructure;
- microservices;
- Kubernetes;
- Kafka or another event broker;
- Redis before horizontal scaling is needed;
- Phaser;
- a canvas-only poker table;
- multiple backend instances;
- real-money deposits, withdrawals or wagering;
- cryptocurrency payments;
- native mobile applications;
- AI features inside the game runtime.

AI is used as part of the development workflow and the 13-lesson training program, not as a required dependency for running the poker game.

## 8. Decision-change process

This document is the default for all lessons and implementation prompts.

A technology or hosting decision changes only when:

1. a concrete limitation is identified;
2. at least two alternatives are compared;
3. migration cost and operational impact are described;
4. the decision is recorded here before implementation begins.

Do not silently replace technologies during AI-generated implementations.

## 9. Official references

- Angular animations: https://angular.dev/guide/animations
- GSAP documentation: https://gsap.com/docs/v3/
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- Render WebSockets: https://render.com/docs/websocket
- Render free services: https://render.com/docs/free
- Vercel Hobby plan: https://vercel.com/docs/plans/hobby
- Supabase billing and quotas: https://supabase.com/docs/guides/platform/billing-on-supabase

## 10. Current decision summary

**Build:** Angular + Nx + Tailwind/SCSS + GSAP + FastAPI + native WebSockets + PostgreSQL/Supabase + SQLAlchemy/Alembic + pytest + Playwright.

**Deploy:** Vercel frontend + Render backend + dedicated Supabase project, using provider subdomains until the application has a final name.

**Isolation:** The project remains completely separate from Eldrion.
