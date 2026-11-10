# Test Suite Organization

Nammakam enforces a tiered testing pyramid:

## Tiers

1. **Unit Tests (`unit/`)**:
   - Pure domain rules, entities, value objects, and deterministic safety policy checks.
   - Zero network, zero disk I/O, zero cloud dependencies.
   - Must execute in under 1 second.

2. **Integration Tests (`integration/`)**:
   - Tests infrastructure adapters against mock servers, local fakes, or in-memory repositories.
   - Verifies use cases wired with in-memory adapters.

3. **End-to-End Tests (`e2e/`)**:
   - Full pipeline execution from scenario input to evidence pack generation using mock agent endpoints.

## Execution

```bash
cd apps/api
uv run pytest
```

