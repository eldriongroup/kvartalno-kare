# ADR-002: Authoritative poker-table state and serialized commands

**Status:** Accepted  
**Date:** 8 October 2026

## Context

Kvartalno Kare needs server-authoritative, real-time No-Limit Texas Hold'em for one administrator-created table and approximately 10–20 known users. Concurrent WebSocket commands, retries, disconnects, action deadlines and backend restarts must not duplicate actions, apply stale actions or corrupt chips. The design must remain small enough for an MVP whose poker rules are still evolving.

This ADR distinguishes live authority from durable authority. It refines the live-state strategy in `tech-and-deployment-stack.md` and the timing, idempotency and recovery requirements in `../product/mvp-product-decisions.md`.

## Current MVP constraints

- One active table with 2–8 seated players.
- FastAPI with native WebSockets and PostgreSQL hosted by Supabase.
- One backend process and no horizontal scaling.
- Commands serialized per table, unique command IDs and expected table revisions.
- Monotonic event revisions and authoritative reconnect snapshots.
- Server-owned action deadlines.
- Durable hand-start checkpoints and accepted-action history sufficient for recovery.
- Invalid recovery voids the interrupted hand and restores table stacks to the hand-start checkpoint.
- Wallet balances are separate from active table stacks.
- No Redis, message broker, microservices, Kubernetes or real-money functionality.

## Considered alternatives

### A. Shared in-memory state with `asyncio.Lock`

A per-table lock protects one mutable state. WebSocket handlers invoke the table service directly, while accepted actions, checkpoints and recovery data are persisted. This can satisfy the MVP, but correctness depends on every present and future mutation path acquiring the same lock and keeping consistent transaction discipline.

### B. Per-table actor with `asyncio.Queue`

One task owns each active table. All actions and timeouts enter through one sequenced submission boundary and bounded queue. Only the actor mutates live gameplay state. PostgreSQL supplies durable command identity, committed revisions, recovery history and wallet accounting.

### C. Database-first transactional state machine

PostgreSQL arbitrates every command and owns the current state. In-memory state is only a cache or projection. This gives a strong path to multiple processes, but couples the evolving game loop more closely to persistence, increases implementation complexity and adds database work to every live transition.

## Revised decision matrix

Scores range from 1 (poor fit) to 5 (strong fit). Weights total 100%. The scores compare safe versions of all three alternatives; persistence features are not credited to an actor or queue by themselves.

| Criterion | Weight | Lock | Actor/database | DB-first |
|---|---:|---:|---:|---:|
| Concurrent correctness | 14% | 4 | 5 | 5 |
| Ordering, revisions and timers | 10% | 4 | 5 | 5 |
| Idempotency and transactions | 9% | 4 | 4 | 5 |
| Restart recovery and durability | 13% | 4 | 4 | 5 |
| Implementation complexity | 10% | 4 | 3 | 2 |
| Conceptual complexity and iteration speed | 8% | 5 | 4 | 2 |
| Testability | 7% | 4 | 5 | 4 |
| Operational failure modes | 7% | 3 | 3 | 4 |
| Hand-action latency | 5% | 5 | 4 | 2 |
| WebSockets, timers and reconnect fit | 5% | 4 | 5 | 3 |
| Fit for the single-process MVP | 4% | 5 | 5 | 4 |
| Path to multiple instances | 4% | 2 | 3 | 5 |
| Observability and debugging | 2% | 4 | 4 | 4 |
| Domain/persistence separation | 2% | 4 | 4 | 2 |
| **Weighted total** | **100%** | **80.4** | **83.8** | **79.0** |

The actor/database option wins narrowly. The decision depends on the single-process constraint and should be revisited if that constraint changes.

## Decision

Use a clearly defined actor/database hybrid.

The per-table actor is authoritative for:

- live command sequencing;
- in-process table and hand state;
- turn progression and timer-command processing;
- invoking framework-independent, pure poker-domain transitions;
- producing revision-consistent public and private projections.

Only the actor may mutate live gameplay state for its table.

PostgreSQL is authoritative for:

- authenticated command identity and idempotency;
- accepted command results and committed table revisions;
- accepted actions, recovery history and hand-start checkpoints;
- protected private recovery data;
- wallet ledger and wallet balance;
- buy-in, top-up, cash-out and void accounting;
- reconstruction after a process restart.

An in-memory queue is an ordering mechanism, not a durability boundary. A command is not accepted merely because it was submitted or enqueued.

## Authoritative ownership boundaries

| State | Authority |
|---|---|
| Wallet ledger and wallet balance | PostgreSQL |
| Buy-in, top-up and cash-out accounting | PostgreSQL transaction |
| Live table stack, pot, bets and current hand | Table actor, backed by durable recovery data |
| Turn and deadline | Table actor, with a unique turn token and recovery data |
| Seated-player membership | Durable table/session state projected into the actor |
| Connection presence | In-memory WebSocket connection manager |
| Accepted command/action history | PostgreSQL |
| Public WebSocket state | Revision-consistent actor projection |
| Private player state | Per-player projection from server-owned state |
| Deck continuation and private recovery material | Protected PostgreSQL recovery data; never public or logged |

## Command lifecycle

1. The WebSocket boundary authenticates the connection and performs only minimal envelope and authorization checks.
2. The common table submission boundary assigns the next monotonic server submission sequence immediately before successful insertion into the bounded actor queue.
3. The actor dequeues commands in submission-sequence order.
4. It checks durable idempotency when required, expected table revision, turn token, authorization and domain legality.
5. A pure domain transition proposes the next state and projections without mutating the adopted state.
6. The server persists the accepted command, result, action/event, recovery data and new revision in one database transaction.
7. After commit, the actor adopts the committed state.
8. The server acknowledges the command and broadcasts the resulting projection or event.
9. Rejections return a typed result and the authoritative revision or resynchronization instruction.

Immediate WebSocket broadcasting is best effort in the first MVP. Clients detect revision gaps and obtain a fresh authoritative snapshot. A generic durable outbox may be deferred. It becomes required if every committed event is promised eventual delivery or if multiple processes are introduced.

## Transaction boundary

For an accepted state-changing poker command, one transaction:

1. establishes or verifies the authenticated command identity;
2. verifies the durable table revision against the actor's proposed base revision;
3. writes the accepted action and protected recovery information;
4. assigns and writes the next table/event revision;
5. stores the stable command result;
6. commits.

Only after commit may the actor adopt the proposed state, acknowledge acceptance and broadcast. If persistence fails or has an ambiguous result, or committed-state adoption cannot be guaranteed, the actor stops processing, discards its in-memory authority and reloads or is recreated from durable state. It must not guess whether a transaction committed.

Normal poker-action transactions do not modify wallet balances. Transactions that cross the wallet/table boundary follow the accounting rules below.

## Idempotency strategy

- The client generates a cryptographically random command UUID.
- Identity is scoped by the authenticated actor, using a database uniqueness constraint equivalent to `UNIQUE(authenticated_actor_id, command_id)`.
- The server stores a canonical request fingerprint, command type, table, expected and resulting revisions, outcome and stable response.
- An identical retry returns the original accepted result or deterministic stored rejection.
- Reuse of the same identity with a different fingerprint is rejected as command-ID reuse.
- Authentication failures occur before gameplay idempotency processing and are not durable game commands.
- The authenticated identity, never a client-supplied player identifier, prevents one player from colliding with another player's command IDs.
- After an ambiguous commit, the actor queries the durable command identity to determine the result and reloads before processing another command.

## Ordering and revision semantics

All player actions and timeout commands use the same actor submission boundary. That boundary assigns a monotonically increasing server submission sequence immediately before successful queue insertion. Submission-sequence and queue order are the authoritative command order.

Client timestamps, client clocks and claimed send times never determine eligibility. Server receive timestamps may be logged for diagnostics but do not override sequence order. Simultaneous requests are resolved by the order in which the common submission boundary assigns their sequences.

Each state-changing accepted command advances the committed table revision by exactly one. Commands carry the table revision the client expects. A mismatched command is rejected as stale with the current revision and a resynchronization instruction. Events and snapshots identify their authoritative revision.

This ordering is deterministic only after submission sequencing. A network message sent before a deadline is not guaranteed to count unless it reaches the authoritative server submission boundary before the timeout receives its sequence.

## Timer and deadline semantics

The server schedules against a monotonic deadline. When that deadline is reached, it submits a timeout command through the same boundary as player actions. Every timeout contains the expected table revision and the unique token of the turn for which it was scheduled.

- If a player action receives a lower submission sequence than the timeout, the actor evaluates the player action first.
- If the timeout receives a lower sequence, the actor evaluates the timeout first.
- After the first accepted command changes the turn or revision, the other command is stale.
- A delayed timeout cannot affect a newer turn because both its expected revision and turn token must match.

There is no ingress grace window, retroactive comparison with receive time or queue-draining fairness rule in the MVP.

## Recovery behavior

After a restart, PostgreSQL is the source for reconstruction. Command acceptance remains paused while the system:

1. loads the latest valid hand-start checkpoint;
2. loads accepted actions and protected private recovery state in committed revision order;
3. reconstructs the hand through the pure domain engine;
4. validates the reconstructed state and revision;
5. creates the actor from that revision in a paused/reconnecting state.

If reconstruction fails validation, an idempotent hand-void transaction resets every active table stack to its value in the hand-start checkpoint, discards the interrupted hand's bets, pots and awards, and records a technical `hand_voided` audit result. Hand voiding does not credit wallets and does not cash players out.

Session cash-out is a separate idempotent ledger operation. It transfers each remaining table stack to the corresponding wallet exactly once.

## Wallet and active table-stack separation

- An administrator may credit a player's wallet at any time.
- A wallet credit never changes an active table stack automatically.
- Wallet credits and other wallet-only ledger operations execute outside normal poker-action processing.
- Buy-in, top-up and cash-out use atomic database accounting with linked ledger movements and guarded balance updates.
- Eligibility for a buy-in or top-up is serialized with table state, but database locks are never held while waiting for an actor response.
- Hand voiding restores table stacks to the hand-start checkpoint; it does not credit wallets.

## Single-process deployment invariant

The first usable multiplayer version must run with:

- exactly one FastAPI process;
- exactly one Uvicorn worker;
- one synchronized actor registry;
- at most one active actor per table;
- bounded actor queues and explicit overload/backpressure responses.

Multiple Uvicorn workers or backend instances are unsupported until durable ownership with fencing or database-first command arbitration is implemented. A database revision check is a final safety check, not a substitute for exclusive live ownership.

## Minimum safe MVP requirements

- One synchronized per-table actor and bounded queue.
- One common sequenced submission boundary for player actions and timeouts.
- Explicit backpressure; queue insertion is not acceptance.
- Unique command IDs, canonical fingerprints and database uniqueness.
- Expected revisions and monotonic committed event revisions.
- Pure domain transitions separated from FastAPI, WebSockets and persistence.
- Transactional command result, accepted-action, event and recovery persistence.
- Hand-start checkpoint and protected private reconstruction data.
- Actor shutdown and reload after failed or ambiguous persistence or adoption.
- Unique turn tokens and stale-timeout rejection.
- Authoritative reconnect snapshots.
- Wallet-ledger isolation and atomic wallet/table accounting operations.
- Redacted structured diagnostics for sequence, command, revision, queue depth, persistence latency and recovery.

## Intentionally deferred

- A generic durable outbox while delivery remains best effort with snapshot repair.
- Multiple backend processes or instances.
- Durable actor leases, fencing and cross-process routing.
- Redis, pub/sub and external message brokers.
- Actor passivation and distributed actors.
- A generic event-sourcing framework.
- Multiple active tables as a product feature.
- The complete poker engine and detailed poker-hand rules in the first infrastructure slice.

## Consequences and trade-offs

The actor gives explicit single-writer ownership, natural timer serialization and testable command order. Pure transitions can evolve without embedding poker rules in SQL. PostgreSQL supplies the durability that an in-memory queue cannot provide.

The design maintains two forms of state: a live in-memory state and durable recovery records. Commit/adoption failures therefore require actor invalidation and reload. Slow database transactions delay all later commands for the table, so queue depth and persistence latency require monitoring. The one-worker invariant is operationally important and must be enforced in deployment configuration and startup diagnostics.

## Rejected alternatives

- **Shared state with locks:** valid for the MVP, but less explicit ownership makes it easier for a future command or timer path to bypass the correct lock. It scored closely and remains the simpler fallback if the actor lifecycle proves disproportionate.
- **Database-first state machine:** strongest for multiple writers and instances, but adds persistence coupling, transaction contention and implementation cost before the MVP needs horizontal ownership.
- **Pure in-memory actor:** rejected because a queue does not provide durable acceptance, idempotency, committed revisions or restart recovery.
- **Distributed actor or broker architecture:** rejected because the MVP has one table and one process and explicitly excludes that operational complexity.

## Assumptions

- Only one active table is required initially.
- One process and one worker are sufficient for expected load.
- Clients tolerate best-effort push delivery plus revision-gap snapshot repair.
- Database latency is low enough for one transaction per accepted action.
- Accepted actions plus protected recovery data can deterministically reconstruct an active hand.
- Voiding a hand that fails recovery validation remains acceptable product behavior.

## Revisit triggers

Revisit this decision when:

- more than one Uvicorn worker or backend instance is required;
- multiple active tables create material actor-lifecycle or resource pressure;
- database latency or queue delay affects player actions or timer accuracy;
- recovery drills fail or reconstruction becomes unsafe;
- guaranteed eventual delivery of every committed event is promised;
- deployments frequently interrupt active hands;
- competing-owner revision failures are observed;
- cross-table atomic operations become necessary;
- maintaining live state plus recovery projections causes more defects than a DB-first model.

## Blocking product questions

These do not block this architecture decision but must be answered before their feature is implemented:

1. What are the normal action timer and reconnect time-bank durations?
2. What are the disconnected-seat and empty-table grace periods?
3. What are the minimum and maximum buy-ins?
4. Should a stale-revision response include a snapshot or instruct the client to request one?
5. How long must stored idempotency results and deterministic rejections be retained?
6. Is best-effort broadcast with snapshot repair sufficient, or is eventual delivery of every committed event required?

## Required pre-implementation prototypes and tests

1. Simulate an ambiguous database commit and prove that durable command lookup prevents duplicate application.
2. Crash after commit but before state adoption and broadcast, then prove exact reconstruction and snapshot revision.
3. Race a player action with a timeout in both submission orders and prove that exactly one changes the turn.
4. Submit concurrent first commands to an inactive table and prove that the registry creates only one actor.
5. Race an administrator wallet credit with a buy-in and prove ledger conservation, guarded balances and no automatic active-stack increase.
