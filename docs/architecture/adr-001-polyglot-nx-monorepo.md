# ADR-001: Polyglot Nx monorepo

**Status:** Accepted  
**Date:** 7 October 2026

## Context

Kvartalno Kare needs an Angular frontend and a FastAPI backend in one repository. The approved architecture requires shared task discovery without allowing JavaScript tooling to own Python packaging or deployment.

## Decision

Use one polyglot Nx monorepo. Angular is generated and managed through Nx. FastAPI remains a native Python project under `apps/api`, owned by `pyproject.toml`, `venv`, `pip`, pytest, Ruff, and mypy. Its `project.json` contains only thin, cross-platform commands based on the active Python environment.

Local development uses `npx nx run web:serve`, `python -m uvicorn app.main:app --reload` from `apps/api`, or `npx nx run-many --targets=serve --projects=web,api --parallel` with the Python environment active.

The frontend and backend have independent deployment boundaries. A frontend host builds the Angular application. Render installs and starts the API with native Python commands; it must not require Node or Nx.

Generated OpenAPI TypeScript contracts are deferred until the API surface warrants a contracts library. Pydantic remains the backend source of truth; this slice uses small local TypeScript interfaces.

## Rejected alternatives

- Separate repositories: unnecessary coordination overhead at this stage.
- A Python-specific Nx plugin: adds ownership and coupling without value for the current targets.
- Nx-owned Python packaging or an Nx-dependent API deployment: weakens direct FastAPI operability.
- A contracts library for two messages: premature structure and generation overhead.

## Consequences and risks

Nx gives one task graph and combined developer commands while Python remains independently runnable. Developers must activate the Python virtual environment before Nx invokes API targets. Node and Python lock/version disciplines remain separate, and manually duplicated frontend interfaces can drift until generated contracts are introduced.

## Temporary dependency override

Nx 23.3.0 pins vulnerable `undici` 7.29.0. The workspace narrowly overrides only Nx's copy to patched 7.29.1. Remove this override when a stable Nx release consumes `undici` 7.29.1 or newer.
