# Product Vision & MVP Specification

## Overview

Nammakam provides an automated, reproducible AI safety evaluation platform for Indian-language conversational banking agents.

## Target Personas

- **Bank Chief Risk & Information Security Officers (CISOs)**: Require quantifiable safety benchmarks and auditable evidence packs before approving generative AI deployment.
- **AI Product & Engineering Teams**: Require automated red-teaming pipelines to detect adversarial vulnerabilities and cross-lingual degradation during model iteration.
- **Compliance & Internal Audit Teams**: Require reproducible, tamper-evident records of safety checks.

## MVP Scope

### Supported Scope (MVP)
- Multi-turn text-based red-team evaluation across Telugu, Hindi, Hinglish, and Indian English.
- Demo bank agent with simulated mock banking tools (`transfer_funds`, `block_card`, `add_beneficiary`, `check_balance`).
- Detection of unsafe tool calls, sensitive data leakage, missing escalation, and over-refusal.
- 3-axis scorecards: Resilience, Parity, Protection.
- Tamper-evident evidence pack with SHA-256 manifests and digital signatures.

### Deferred Scope
- Real-time voice caller over Gemini Live / telephony.
- Direct connectivity to live core banking systems.
- Production multi-tenant SaaS features and billing.
- Fine-tuned local Gemma guard models.

