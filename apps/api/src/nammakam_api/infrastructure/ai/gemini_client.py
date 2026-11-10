"""Gemini Model Client Adapter.

Intended Responsibility:
Integrates with Google AI Studio / Vertex AI Gemini Flash (caller simulation)
and Gemini Pro (multi-turn judging and structured evaluation).

TODO:
1. Implement GeminiClient implementing caller and judge ports.
2. Enforce Pydantic structured output decoding on model responses.
"""

