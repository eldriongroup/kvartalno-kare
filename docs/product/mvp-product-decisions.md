# Квартално каре — MVP Product Decisions

**Status:** Proposed decisions for final product-owner review  
**Lesson:** 2 — AI as Product Planner  
**Date:** 6 October 2026  
**Related document:** `docs/architecture/tech-and-deployment-stack.md`

## 1. Purpose

This document combines:

- the product-owner decisions for how the real group will use the application;
- the useful recommendations from the Codex discovery report;
- architecture safeguards that are appropriate for a private MVP with approximately 10–20 known users;
- simplifications that avoid unnecessary enterprise complexity.

The product-owner decisions in this document take precedence over generic AI recommendations.

## 2. MVP summary

“Квартално каре” is a private, real-time No-Limit Texas Hold’em web application for a known group of players.

The initial MVP has:

- one administrator-managed table;
- 2–8 seated players;
- fixed blinds during a session;
- virtual chips granted only by an administrator;
- invited user accounts;
- real-time play through a server-authoritative FastAPI/WebSocket backend;
- desktop and mobile browser support;
- hand history with normal poker card-visibility rules;
- no real-money functionality.

## 3. Product decisions

### 3.1 Poker rules and game format

The MVP supports only standard **No-Limit Texas Hold’em cash-style play**.

Accepted rules:

- 2–8 seated players;
- fixed small and big blinds during a session;
- no increasing blind schedule;
- no ante;
- no rake;
- standard heads-up blind and action order;
- standard minimum-raise and raise-reopening rules;
- standard all-in and side-pot behavior;
- split pots are supported;
- odd chips use one deterministic documented rule;
- players may sit out and return between hands.

The exact blind values are chosen by the administrator before the session starts and cannot change during an active hand.

A custom poker variation conceived by the product owner may be added later for selected Hold’em rotations. It is explicitly excluded from the MVP and must not complicate the initial poker engine.

### 3.2 Table and hand lifecycle

The MVP has one active table.

- The administrator creates and opens the table/session.
- The administrator may close the table/session.
- The live session closes automatically after no players remain, using a short grace period so a temporary disconnect does not destroy the table immediately.
- Players select an available seat.
- The administrator starts the first hand after the expected group is ready.
- Subsequent hands start automatically when at least two eligible players remain ready.
- Joining, leaving, rebuying and changing seats take effect only between hands.
- Players may sit out between hands.
- A player with insufficient chips cannot be dealt into the next hand.

The table record and completed hand history remain durable even after the live session closes.

### 3.3 Accounts, invitations and recovery

Accounts are durable and invitation-only.

- The administrator creates or authorizes a one-time invitation link.
- The invitation link expires and becomes invalid after successful use.
- The invited person chooses a unique username, password and avatar.
- Each human has one account.
- The username is unique and is the stable identity used by the application.
- Avatar and display presentation may be changed without changing ownership of balances or history.
- There is no public self-registration.
- There is no social login in the MVP.
- There is no email-based self-service password recovery in the MVP.
- When a password is forgotten, the administrator invalidates existing sessions and creates a new one-time recovery invitation.

Password policy:

- allow long passwords and passphrases;
- do not impose arbitrary uppercase/symbol composition rules;
- use a minimum length stronger than the initially suggested eight characters; the recommended MVP minimum is 10 characters;
- store only a modern salted password hash;
- rate-limit login and invitation attempts.

### 3.4 Virtual-chip economy

Chips are virtual and have no monetary value inside the application.

- Every player has a persistent **wallet balance** that is separate from the player’s **active table stack**.
- Only an administrator can add chips to a player’s wallet.
- The administrator may add chips to a player’s wallet at any time, including while that player is seated or playing.
- An administrative wallet credit never changes the player’s active table stack automatically.
- Players cannot buy chips through the application.
- Players cannot transfer chips directly to one another.
- There is no automatic daily or session refill.
- If a player loses all wallet and table chips, only the administrator can grant more chips to the wallet.
- When joining the table, the player chooses how many wallet chips to transfer into the table stack, subject to the configured minimum and maximum buy-in.
- The remainder stays safely in the wallet and is not at risk in the current session.
- A seated player may rebuy or top up the table stack from the wallet only between hands and within the configured table limits.
- Winnings remain in the table stack while the player stays seated.
- When the player leaves the table between hands or the session closes, the complete remaining table stack returns to the wallet.
- Wallet and table-stack movements use an append-only transaction ledger instead of silently overwriting totals.
- Each administrative credit records actor, player, amount, reason and timestamp.
- Each wallet-to-table buy-in, table-to-wallet cash-out and between-hand top-up is recorded as a linked ledger movement.

Example:

- A player has 200 chips in the wallet from previous sessions.
- The player chooses a 20-chip buy-in.
- The active table stack becomes 20 and 180 chips remain in the wallet.
- If the player leaves with a 55-chip table stack, those 55 return to the wallet and the wallet becomes 235.
- If the administrator adds 100 chips while the player is playing, the 100 are added to the wallet only; the active table stack does not change.

The ledger is retained because it directly supports the product-owner requirement that the administrator controls chip distribution while players independently choose how much of their wallet to risk at the table. It is not a real-money accounting system.

### 3.5 Disconnects, action timeouts and abandoned seats

The table does not pause for a disconnected player.

- The server owns the action deadline.
- A disconnected player receives the normal action timer plus one limited reconnect time bank.
- When the deadline expires, the server auto-checks if checking is legal; otherwise it auto-folds.
- The current hand continues normally.
- If the player is still disconnected after the hand, the player is marked sitting out.
- The seat is reserved for a configurable grace period.
- If the player does not reconnect before that grace period ends, the player is removed from the live table and remaining table chips are returned safely to the persistent balance.
- A reconnect always requests a fresh authoritative snapshot.

The exact normal action timer, reconnect time bank and seat-reservation duration remain configuration decisions to be chosen before implementation of the timer feature.

### 3.6 Table visibility and administrator powers

There are no separately private tables in the MVP because there is initially only one table.

- Only invited and authenticated users can access the application.
- All authenticated users can see whether the single table is open and which seats are available.
- No separate per-table membership model is required.
- There is no table password in the MVP.
- Full spectator mode is deferred. A non-seated user may see lobby/table status but does not receive live private game state.

Administrator powers:

- invite and recover accounts;
- create, open and close the table/session;
- configure fixed blinds before play;
- grant or correct virtual chips with an audit reason;
- remove or sit out a disruptive or abandoned player;
- review redacted audit and hand-history information.

The administrator must not:

- see live hole cards through an administrative UI;
- change the deck or outcome;
- rewrite an active player action;
- silently edit balances without a ledger entry.

### 3.7 Hand history and card visibility

Normal poker visibility rules apply.

Player-visible history includes:

- public actions;
- board cards;
- pots and results;
- the viewing player’s own hole cards;
- opponent hole cards only when voluntarily shown or legitimately exposed at showdown.

The application must never reveal every player’s hole cards automatically after each hand.

A fuller protected audit record may exist for technical recovery and dispute investigation, but it must not expose live hole cards in logs or an administrator screen.

Because the first group is small, completed hand history may be retained indefinitely during the MVP. Storage growth will be measured and a retention/export policy can be introduced later.

### 3.8 Mobile experience

The Codex recommendation is accepted:

- full gameplay on current Android Chrome and iOS Safari;
- condensed portrait layout;
- enhanced landscape layout;
- readable hole cards, board cards, pot and legal actions take priority over decorative elements;
- touch targets must be suitable for mobile use;
- reconnect behavior must tolerate backgrounded mobile tabs;
- decorative animations may be reduced or skipped on constrained devices;
- the user can disable sound and request reduced motion.

## 4. Technical decisions derived from the product behavior

### 4.1 Timing, ordering and idempotency

This is an architecture responsibility rather than a product-owner choice. The simplified safe design is accepted:

- player commands are serialized per table;
- every command has a unique command ID;
- every command includes the table revision the client believes it is acting on;
- accepted commands are idempotent, so retrying the same command cannot apply an action twice;
- server events have a monotonic table revision;
- action deadlines use server time;
- the UI may animate only confirmed state;
- if an event gap or revision mismatch is detected, the client discards speculative view state and requests a fresh snapshot;
- animations may accelerate or be skipped when the client is behind the authoritative state.

This prevents double bets, actions based on stale state and visual animations becoming the game’s source of truth.

### 4.2 Backend restart during an active hand

The solution combines recovery safety with lower MVP complexity.

- Store a durable hand-start checkpoint containing player stacks and table configuration.
- Append every accepted game action and the minimum private state required to reconstruct the active hand.
- Protect deck continuation and private cards from normal logs and unauthorized access.
- On restart, attempt deterministic reconstruction and validate the result.
- If reconstruction succeeds, restore the table in a paused/reconnecting state and continue after players reconnect.
- If reconstruction fails validation, void the interrupted hand and restore stacks from the hand-start checkpoint.
- Record a `hand_voided` audit event with a technical reason.

This does not require a generic event-sourcing platform. The persistence exists only to recover or safely void an active poker hand.

### 4.3 Integrity and abuse model

The MVP uses a trust-based model for a known private group, with basic production safeguards.

Included:

- server-authoritative game state;
- cryptographically secure server-side shuffle;
- deterministic shuffle fixtures only in tests;
- authorization on lobby, table, WebSocket and history access;
- command replay protection and idempotency;
- rate limits on authentication and game commands;
- immutable chip-adjustment and game-action audits;
- redacted logs that do not contain passwords, tokens, full deck state or live hole cards;
- no administrator screen for viewing live hole cards;
- sufficient evidence to investigate a disputed hand.

Deferred:

- automated collusion detection;
- device fingerprinting;
- multi-account heuristics;
- provably fair cryptographic verification;
- advanced anomaly detection.

### 4.4 Authentication transport and initial deployment

The MVP must remain simple and must not require a custom domain.

- Frontend remains on a Vercel provider subdomain.
- Backend and WebSockets remain on a Render provider subdomain.
- PostgreSQL remains in the dedicated Supabase project.
- Do not introduce a custom domain only to solve authentication during the MVP.
- Use short-lived access credentials kept out of persistent browser storage.
- Use a single-use, short-lived WebSocket ticket for the WebSocket upgrade.
- Prefer a rotated refresh token in a Secure, HttpOnly cookie only after verifying that current browser behavior works reliably across the selected provider origins.
- If cross-site refresh cookies are not reliable without a custom domain, prefer an explicit re-login in the earliest MVP rather than storing a long-lived bearer token in `localStorage`.
- Exact CORS origins are allowlisted.
- CSRF protection is required for any cookie-authenticated mutation.
- Provider regions, quotas and free/paid plans are verified at deployment time.

Environment simplification:

- use one dedicated Supabase cloud project for the poker application initially;
- automated tests use an isolated local/test database and never production tables;
- preview deployments must not receive production database credentials by default;
- add a second cloud environment only when regular real-user usage or release risk justifies it.

## 5. Explicitly deferred features

- tournaments and increasing blinds;
- antes and rake;
- custom Hold’em rotations or the future custom game;
- multiple tables;
- private table memberships and table passwords;
- spectators and live observer mode;
- email-based self-service recovery;
- social login;
- peer-to-peer chip transfers;
- chip purchases or real-money settlement;
- customizable rule variants;
- automated collusion detection;
- device fingerprinting;
- provably fair deck verification;
- native mobile applications;
- Redis, multiple backend instances and horizontal scaling;
- custom domain;
- advanced administrative analytics.

## 6. Remaining configuration decisions

These do not block the overall product architecture but must be selected before their relevant features are implemented:

1. Default small blind and big blind values.
2. Minimum and maximum table buy-in.
3. Normal player action timer.
4. Additional reconnect time bank.
5. Disconnected-seat reservation period.
6. Empty-table auto-close grace period.
7. Exact odd-chip allocation rule.
8. Whether the administrator may pause between hands or only close the session.
9. Whether avatars are selected from built-in options or uploaded by users.

## 7. Implementation gate

Before implementation begins:

- the product owner reviews and accepts this document;
- remaining configuration values may stay marked as TBD if they are not required by the first implementation slice;
- Codex must not replace accepted decisions with its earlier generic recommendations;
- future changes must update this document explicitly;
- the first technical specification must reference both this document and the technology/deployment decision document.

## 8. Lesson 2 takeaway

The discovery report was useful because it found decisions that the original request did not contain. Its recommendations were inputs, not requirements.

The product owner kept the recommendations that protect real-time correctness and game integrity, simplified the parts that were too enterprise-heavy, and replaced assumptions with behavior that matches the actual group.

That is the core Planner skill: use AI to expose the decision space, then make and document the decisions deliberately.
