# Security & Responsible AI Framework

## Threat Model & Security Boundaries

1. **Zero Real Customer Data**:
   All evaluation scenarios, caller personas, account numbers, and mock tool transactions are completely synthetic. Live customer data must never be processed or stored.

2. **Isolated Tool Execution**:
   Mock banking tools operate on in-memory state within the test runner. No outbound network requests to live banking systems are permitted.

3. **Tamper-Evident Evidence Packs**:
   - Transcripts, tool execution records, and evaluation verdicts are canonicalized to deterministic JSON.
   - SHA-256 digests are computed for each artifact.
   - An asymmetric key in Google Cloud KMS signs the hash manifest.

4. **Credential Isolation**:
   No credentials, service account keys, or API tokens may be stored in code or git. Runtime secrets are resolved through Google Cloud Secret Manager.

