# System Architecture Specification

## Clean Architecture Principles

Nammakam is organized as a modular monolith adhering to Clean Architecture.

$$\text{Presentation} \longrightarrow \text{Application} \longrightarrow \text{Domain} \longleftarrow \text{Infrastructure}$$

### 1. Domain Layer (`src/nammakam_api/domain`)
- **Entities**: Stateful business concepts with identity (`Scenario`, `Episode`, `Transcript`, `ToolCall`, `Judgment`, `EvidencePack`).
- **Value Objects**: Immutable primitives with validation rules (`Language`, `AttackFamily`, `Verdict`, `Score`).
- **Domain Services**: Pure business algorithms operating across entities (`SafetyPolicy`, `ParityCalculator`, `ProtectionScorer`).
- **Invariants**: Must not import FastAPI, Pydantic (except pure validation), Google Cloud SDKs, database drivers, or presentation modules.

### 2. Application Layer (`src/nammakam_api/application`)
- **Use Cases**: Encapsulate business workflows (`RunEpisode`, `EvaluateEpisode`, `GenerateScorecard`, `GenerateEvidencePack`).
- **Ports**: Abstract interfaces for persistence, AI calling, messaging, and security.
- **DTOs**: Data transfer objects for boundary inputs and outputs.
- **Invariants**: Independent of frameworks, presentation routing, and concrete database drivers.

### 3. Infrastructure Layer (`src/nammakam_api/infrastructure`)
- **Adapters**: Concrete implementations of application ports.
- **AI**: Gemini Flash and Pro clients with Pydantic output validation.
- **Persistence**: Firestore (episodes), BigQuery (metrics), GCS (artifacts).
- **Messaging**: Cloud Pub/Sub, Cloud Tasks.
- **Security**: Secret Manager, Cloud KMS.

### 4. Presentation Layer (`src/nammakam_api/presentation`)
- **FastAPI Routers**: Protocol adapters that parse HTTP requests and invoke use cases.
- **Schemas**: Pydantic request/response models.
- **Invariants**: Route handlers must contain zero business logic.

