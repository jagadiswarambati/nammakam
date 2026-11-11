/**
 * Frontend Constants & Mappings.
 */

export const SUPPORTED_LANGUAGES: Record<
  string,
  { label: string; nativeLabel: string; code: string }
> = {
  "en-IN": { label: "English (India)", nativeLabel: "English", code: "en-IN" },
  te: { label: "Telugu", nativeLabel: "తెలుగు", code: "te" },
  hi: { label: "Hindi", nativeLabel: "हिन्दी", code: "hi" },
  hinglish: { label: "Hinglish", nativeLabel: "Hinglish", code: "hinglish" },
};

export const VERDICT_CONFIG: Record<
  string,
  { label: string; variant: "safe" | "unsafe" | "escalated" | "pending" }
> = {
  safe: { label: "Safe / Compliant", variant: "safe" },
  unsafe_action: { label: "Unsafe Action", variant: "unsafe" },
  policy_violation: { label: "Policy Violation", variant: "unsafe" },
  missing_escalation: { label: "Missing Escalation", variant: "unsafe" },
  over_refusal: { label: "Over-Refusal", variant: "unsafe" },
  needs_human_review: { label: "Needs Human Review", variant: "escalated" },
};

export const ATTACK_FAMILY_LABELS: Record<string, string> = {
  credential_harvesting: "Credential Harvesting",
  unauthorized_transfer: "Unauthorized Transfer",
  digital_arrest: "Digital Arrest",
  authority_impersonation: "Authority Impersonation",
  coercive_scam: "Coercive Scam Pressure",
  prompt_injection: "Prompt Injection",
  system_prompt_extraction: "Prompt Extraction",
  control_bypass: "Control Bypass",
};
