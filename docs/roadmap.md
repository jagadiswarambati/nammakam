# Nammakam Implementation Roadmap

## Phase 1: Foundation (Current)
- Clean Architecture directory layout and repository standards.
- Documentation, evaluation methodology, and architectural invariants.
- Typed skeleton interfaces for domain, application, and infrastructure layers.

## Phase 2: Core Domain & Mock Banking (Planned)
- Domain entities, value objects, and deterministic safety rules.
- Demo banking agent with mock tools (`transfer_funds`, `block_card`, `add_beneficiary`).
- Initial scenario suite for Telugu, Hindi, Hinglish, and English.

## Phase 3: Runner & Judging Engine (Planned)
- Multi-turn execution orchestrator (`RunEpisodeUseCase`).
- Gemini Flash simulator adapter for multi-turn caller interaction.
- Gemini Pro safety judging adapter with structured Pydantic validation.

## Phase 4: Scorecards & Cryptographic Evidence (Planned)
- Cross-lingual parity calculator and composite protection scoring.
- Evidence pack generation with SHA-256 digests.
- Cloud KMS asymmetric digital signature adapter.

## Phase 5: Dashboard UI (Planned)
- Next.js console for inspecting episode runs, drilldowns, and scorecards.
- Interactive evidence verification view.

## Phase 6: Voice Support via Gemini Live (Deferred)
- Bidirectional audio streaming and real-time voice red-teaming.

## Phase 7: Gemma Guard Integration (Deferred)
- On-premises and private VPC safety classification via local Gemma models.

