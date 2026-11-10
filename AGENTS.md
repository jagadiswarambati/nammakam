# AGENTS.md — Engineering Standards & Agent Operating Guidelines

This document defines the persistent architectural invariants, coding conventions, safety boundaries, and operating protocols for any AI agent or software engineer working on the **Nammakam** codebase.

---

## 1. Project Purpose

Nammakam is an AI safety-evaluation platform specifically designed for Indian-language banking voice and chat agents. It systematically red-teams conversational agents across Telugu, Hindi, Hinglish, and English; identifies scam compliance and unauthorized tool invocation; measures cross-lingual parity gaps and wrongful refusals; and generates cryptographically signed evidence packs.

---

## 2. Fixed Tech Stack & Tooling

Adhere strictly to this stack. Do not introduce alternatives without explicit human approval:

- **Backend Runtime**: Python 3.12+ managed via `uv`
- **Web API**: FastAPI with Pydantic v2
- **Linting & Formatting**: Ruff
- **Type Checking**: MyPy (in strict mode: `--strict`)
- **Testing**: Pytest
- **Frontend**: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query
- **Google Cloud Services**:
  - Compute: Cloud Run
  - Messaging & Execution: Cloud Pub/Sub, Cloud Tasks
  - Storage & Analytics: Firestore, BigQuery, Cloud Storage (GCS)
  - Security & Secrets: Secret Manager, Cloud KMS
  - Observability: Cloud Logging
- **AI Models & SDKs**:
  - Prototyping: Google AI Studio
  - Multi-turn Simulation & Scenario Generation: Gemini Flash
  - Complex Judging & Report Synthesis: Gemini Pro
  - Voice Interaction (Deferred): Gemini Live
  - Local Classifier (Deferred): Gemma

**Explicitly Forbidden Additions (unless approved in writing)**:
- Relational Databases: PostgreSQL, Cloud SQL, SQLite (in production)
- Caching / In-Memory: Redis, Memorystore
- Document Stores / BaaS: MongoDB, Supabase, Firebase Authentication
- Infrastructure Tooling: Docker Compose, Terraform, Kubernetes

---

## 3. Clean Architecture & Folder Ownership

Nammakam enforces Clean Architecture within a modular monolith. Dependencies must point strictly inward:

$$\text{Presentation} \longrightarrow \text{Application} \longrightarrow \text{Domain} \longleftarrow \text{Infrastructure}$$

### Layer Definitions & Ownership

| Layer | Path | Allowed Imports | Forbidden Imports |
|---|---|---|---|
| **Domain** | `apps/api/src/nammakam_api/domain/` | Pure standard library, typing, domain value objects, domain entities | FastAPI, Pydantic (except pure validation where appropriate), Google Cloud SDKs, HTTP clients, OS file paths, Infrastructure |
| **Application** | `apps/api/src/nammakam_api/application/` | Domain layer, standard library, application DTOs | FastAPI, Starlette, Google Cloud SDKs, direct DB drivers, Presentation |
| **Infrastructure** | `apps/api/src/nammakam_api/infrastructure/` | Application interfaces (ports), Domain layer, external SDKs (`google-cloud-*`, `google-genai`), Pydantic Settings | Presentation routes |
| **Presentation** | `apps/api/src/nammakam_api/presentation/` | Application use cases & DTOs, presentation schemas, FastAPI | Direct Google Cloud SDKs, DB drivers, infrastructure details |

### Architectural Invariants
1. **No Business Logic in Route Handlers**: Route handlers are strictly protocol adapters. They parse requests, invoke application use cases, and serialize responses.
2. **Interface Inversion**: Infrastructure must implement abstract ports defined in domain or application layers. Never leak cloud infrastructure details into core business logic.
3. **Pydantic Validation at Boundaries**: All structured outputs from LLMs, external APIs, and HTTP requests must be rigorously validated through Pydantic schemas.
4. **Deterministic Checks Before AI**: Regex and rule-based safety checks (e.g., matching 6-digit OTPs or 16-digit card numbers in tool parameters) must execute deterministically before invoking an LLM judge.

---

## 4. Naming Conventions & Code Style

### Python (Backend)
- **Files & Packages**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions & Methods**: `snake_case()`
- **Variables & Attributes**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Type Annotations**: Explicit type hints on all function signatures and public attributes. No untyped functions (`def func(...)` without annotations is rejected by MyPy).
- **Domain Value Objects**: Implemented as frozen dataclasses or immutable types.

### TypeScript / Next.js (Frontend)
- **Files**:
  - Components: `PascalCase.tsx` or `kebab-case.tsx` (match shadcn standards)
  - Utilities / Types / Lib: `kebab-case.ts`
- **Interfaces & Types**: `PascalCase` (prefixed with descriptive nouns, e.g., `EpisodeRecord`, `ScorecardMetrics`)
- **Functions**: `camelCase`

---

## 5. Security & Sensitive Data Rules

- **Zero Real Data**: Never accept, store, test with, or log actual customer bank account numbers, UPI PINs, Aadhaar numbers, PAN cards, or live OTPs. All data must be synthetic.
- **Zero Secrets in Repository**: No API keys, service account JSON files, private tokens, or connection strings in Git. Always use `.env.example` templates and Secret Manager in cloud environments.
- **Cryptographic Evidence Verification**: Evidence packs must contain SHA-256 digests of transcripts and tool calls, signed via asymmetric Cloud KMS keys.
- **Safe Tool Simulation**: The demo bank agent's tools (e.g., `transfer_funds`, `block_card`) must operate strictly on mock in-memory state. Never attempt connection to financial networks.

---

## 6. AI & Google Cloud Verification Rules

- **No Hallucinated Google Cloud APIs or Models**: Never invent model names (e.g., `gemini-3.0-ultra-super`), speculative SDK calls, quotas, or cloud regions. Verify against official Google Cloud / Google AI documentation.
- **Model Role Separation**:
  - `Gemini Flash`: Rapid red-team turn generation, simulated caller dialogue.
  - `Gemini Pro`: Detailed safety evaluation, ambiguous turn arbitration, and structured evidence report synthesis.
- **Structured Outputs**: Always enforce JSON mode or schema-constrained decoding for LLM calls using Pydantic models.

---

## 7. Testing Requirements

- **Unit Tests (`tests/unit/`)**:
  - Pure tests for domain entities, value objects, and domain services.
  - No network access, no disk I/O, no cloud emulators.
  - Fast execution (<1 second for complete suite).
- **Integration Tests (`tests/integration/`)**:
  - Test infrastructure adapters against mocks or local fakes.
  - Test use case execution with in-memory repositories.
- **End-to-End Tests (`tests/e2e/`)**:
  - Test full scenario evaluation pipeline runs using mock agent backends.

---

## 8. Definition of Done (DoD)

A task or pull request is complete only when:
1. All changes strictly adhere to Clean Architecture boundaries.
2. Type checking passes with zero errors: `uv run mypy .`
3. Linting and formatting pass with zero errors: `uv run ruff check .`
4. All existing and new tests pass: `uv run pytest`
5. No credentials, tokens, or untracked temporary files are left in the working tree.
6. Documentation is updated to reflect any new public interfaces or configurations.
7. Unfinished capabilities are explicitly marked as "Planned" or "Deferred".

---

## 9. Critical "DO NOT" List

- **DO NOT** place business logic inside FastAPI route handlers.
- **DO NOT** import Google Cloud client libraries (`google.cloud.*`) or AI SDKs inside the `domain` or `application` directories.
- **DO NOT** commit real secrets, API keys, or `.env` files containing live credentials.
- **DO NOT** create speculative abstractions, premature microservices, or duplicate DTOs/schemas.
- **DO NOT** replace or augment the approved tech stack without prior human sign-off.
- **DO NOT** mark incomplete features as complete in documentation or status reports.
- **DO NOT** bypass type checking with `# type: ignore` without documenting the exact upstream bug or limitation.
