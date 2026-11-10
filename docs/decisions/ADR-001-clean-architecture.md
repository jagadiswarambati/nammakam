# ADR-001: Clean Architecture & Layer Isolation

## Status
Accepted

## Context
Nammakam evaluates sensitive banking conversational agents. The evaluation engine must remain deterministic, reproducible, testable without network access, and independent of specific cloud or model providers.

## Decision
We enforce a strict Clean Architecture pattern:
`Presentation -> Application -> Domain <- Infrastructure`

1. The Domain layer contains pure business entities, value objects, and deterministic safety rules. It has zero external dependencies.
2. The Application layer coordinates use cases and defines port interfaces.
3. The Infrastructure layer implements adapters for Google Cloud services (Firestore, BigQuery, GCS, Pub/Sub, Tasks, KMS, Secret Manager) and AI providers (Gemini Flash/Pro).
4. Presentation handles FastAPI routing and HTTP schema serialization only.

## Consequences
- Fast unit testing of domain and safety policies with zero cloud dependencies or mocks.
- Clear separation between deterministic rule checks and LLM-assisted evaluation.
- Cloud providers and model implementations can be upgraded or swapped without altering evaluation logic.

