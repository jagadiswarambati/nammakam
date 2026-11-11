/**
 * Evaluation TypeScript contracts mirroring FastAPI schemas.
 */

export interface LanguageMetrics {
  language: string;
  total_scenarios: number;
  passed: number;
  failed: number;
  escalated: number;
  over_refusal: number;
  resilience_score: number;
  protection_score: number;
}

export interface ParityGap {
  target_language: string;
  baseline_language: string;
  refusal_gap: number;
  attack_gap: number;
  parity_score: number;
}

export interface ScenarioTypeMetrics {
  total: number;
  passed: number;
  failed: number;
  escalated: number;
}

export interface ScenarioFailure {
  scenario_id: string;
  language: string;
  attack_family: string | null;
  verdict: string;
  reason: string;
  requires_human_review: boolean;
}

export interface EvaluationSummary {
  evaluation_id: string;
  total_scenarios: number;
  scenarios_passed: number;
  scenarios_failed: number;
  scenarios_escalated: number;
  scenarios_with_over_refusal: number;
  overall_resilience: number;
  overall_protection: number;
  overall_parity: number;
  results_by_language: Record<string, LanguageMetrics>;
  parity_gap_by_language: Record<string, ParityGap>;
  results_by_scenario_type: Record<string, ScenarioTypeMetrics>;
  failing_scenarios: ScenarioFailure[];
}

export interface BaselineEvaluationRun {
  evaluation_id: string;
  status: string;
  created_at: string;
  total_scenarios: number;
  scenarios_passed: number;
  scenarios_failed: number;
  scenarios_escalated: number;
  scenarios_with_over_refusal: number;
  overall_resilience: number;
  overall_protection: number;
  overall_parity: number;
  episode_ids: string[];
  summary_url: string;
  evidence_pack_url: string;
}

export interface Turn {
  turn_index: number;
  role: "caller" | "agent";
  content: string;
  timestamp_iso: string;
}

export interface ToolInvocation {
  call_id: string;
  tool_name: string;
  parameters: Record<string, unknown>;
  result: Record<string, unknown>;
  authorized: boolean;
  timestamp_iso: string;
}

export interface GeminiJudgeResponse {
  verdict?: string;
  confidence?: number;
  explanation?: string;
  recommended_fix?: string;
  scam_indicators?: string[];
  unsafe_actions?: string[];
  missing_protections?: string[];
  requires_human_review?: boolean;
}

export interface Judgment {
  judgment_id: string;
  verdict: string;
  confidence: number;
  rationale: string;
  is_deterministic: boolean;
  gemini_response?: GeminiJudgeResponse | null;
}

export interface EpisodeDetail {
  episode_id: string;
  scenario_id: string;
  language: string;
  is_adversarial: boolean;
  attack_family: string | null;
  is_safe: boolean;
  requires_escalation: boolean;
  escalated: boolean;
  escalation_reason: string | null;
  turns: Turn[];
  tool_calls: ToolInvocation[];
  violations: string[];
  judgment: Judgment;
}

export interface EvidencePack {
  evaluation_id: string;
  evidence_pack_id: string;
  status: string;
  digest_sha256: string;
  total_episodes: number;
  signed: boolean;
  verification_notes: string;
  created_at: string;
}
