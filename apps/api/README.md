# Nammakam API Service

FastAPI backend service implementing Clean Architecture for evaluating Indian-language banking voice and chat agents.

## Layer Boundaries

1. **Domain (`src/nammakam_api/domain`)**: Pure business rules, entities, value objects, and domain services. Zero dependencies on external frameworks or databases.
2. **Application (`src/nammakam_api/application`)**: Orchestrates use cases and defines port interfaces for external systems.
3. **Infrastructure (`src/nammakam_api/infrastructure`)**: Implements application ports for Google Cloud, AI models, persistence, and security.
4. **Presentation (`src/nammakam_api/presentation`)**: FastAPI route handlers and request/response validation schemas.

## Guidelines

- Route handlers must remain thin adapters and delegate directly to use cases.
- Never import cloud SDKs or AI clients into domain or application layers.

