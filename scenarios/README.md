# Evaluation Scenarios

Scenario definitions for red-teaming Indian-language banking conversational agents.

## Structure

- `english/`: Indian English evaluation scenarios
- `telugu/`: Telugu (తెలుగు) evaluation scenarios
- `hindi/`: Hindi (हिन्दी) evaluation scenarios
- `hinglish/`: Code-mixed Hindi-English evaluation scenarios
- `shared/`:
  - `attack_families/`: Common adversarial taxonomy definitions
  - `genuine_customer/`: Non-adversarial baseline requests (for parity & refusal testing)
  - `scam_in_progress/`: Social engineering and urgency-based deception patterns

## Authoring Guidelines

Every scenario must include:
1. `id`: Unique scenario identifier
2. `language`: Target language code (`en-IN`, `te`, `hi`, `en-IN-hi`)
3. `attack_family`: Taxonomy category (e.g., `authority_impersonation`, `otp_extraction`)
4. `caller_persona`: Background persona for the simulated caller
5. `safety_assertion`: Expected safe handling outcome

