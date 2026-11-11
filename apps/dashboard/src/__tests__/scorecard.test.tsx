import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ScorecardView } from "../components/scorecard/ScorecardView";
import { EvaluationSummary } from "../types/evaluation";

const mockSummary: EvaluationSummary = {
  evaluation_id: "EVAL-TEST-SCORECARD",
  total_scenarios: 16,
  scenarios_passed: 16,
  scenarios_failed: 0,
  scenarios_escalated: 4,
  scenarios_with_over_refusal: 0,
  overall_resilience: 1.0,
  overall_protection: 0.875,
  overall_parity: 1.0,
  results_by_language: {
    "en-IN": {
      language: "en-IN",
      total_scenarios: 4,
      passed: 4,
      failed: 0,
      escalated: 1,
      over_refusal: 0,
      resilience_score: 1.0,
      protection_score: 0.875,
    },
    te: {
      language: "te",
      total_scenarios: 4,
      passed: 4,
      failed: 0,
      escalated: 1,
      over_refusal: 0,
      resilience_score: 1.0,
      protection_score: 0.875,
    },
    hi: {
      language: "hi",
      total_scenarios: 4,
      passed: 4,
      failed: 0,
      escalated: 1,
      over_refusal: 0,
      resilience_score: 1.0,
      protection_score: 0.875,
    },
    hinglish: {
      language: "hinglish",
      total_scenarios: 4,
      passed: 4,
      failed: 0,
      escalated: 1,
      over_refusal: 0,
      resilience_score: 1.0,
      protection_score: 0.875,
    },
  },
  parity_gap_by_language: {
    te: {
      target_language: "te",
      baseline_language: "en-IN",
      refusal_gap: 0.0,
      attack_gap: 0.0,
      parity_score: 1.0,
    },
    hi: {
      target_language: "hi",
      baseline_language: "en-IN",
      refusal_gap: 0.0,
      attack_gap: 0.0,
      parity_score: 1.0,
    },
    hinglish: {
      target_language: "hinglish",
      baseline_language: "en-IN",
      refusal_gap: 0.0,
      attack_gap: 0.0,
      parity_score: 1.0,
    },
  },
  results_by_scenario_type: {
    genuine_customer: { total: 8, passed: 8, failed: 0, escalated: 0 },
    adversarial: { total: 8, passed: 8, failed: 0, escalated: 4 },
  },
  failing_scenarios: [],
};

const mockEpisodeIds = [
  "EP-SCEN-EN-01-abc",
  "EP-SCEN-TE-01-def",
  "EP-SCEN-HI-01-ghi",
  "EP-SCEN-HN-01-jkl",
];

describe("ScorecardView Component", () => {
  it("renders the mandatory synthetic bank agent label", () => {
    render(<ScorecardView summary={mockSummary} episodeIds={mockEpisodeIds} />);
    expect(
      screen.getByText("Baseline evaluation of Nammakam’s synthetic mock bank agent.")
    ).toBeInTheDocument();
  });

  it("renders key metric scores accurately", () => {
    render(<ScorecardView summary={mockSummary} episodeIds={mockEpisodeIds} />);
    // Resilience: 100.0%
    expect(screen.getAllByText("100.0%").length).toBeGreaterThanOrEqual(1);
    // Protection: 0.88 (or 0.875)
    expect(screen.getAllByText("0.88").length).toBeGreaterThanOrEqual(1);
    // Total: 16
    expect(screen.getByText("16")).toBeInTheDocument();
  });

  it("renders all 4 languages in the matrix table", () => {
    render(<ScorecardView summary={mockSummary} episodeIds={mockEpisodeIds} />);
    expect(screen.getByText("English (India)")).toBeInTheDocument();
    expect(screen.getByText("Telugu")).toBeInTheDocument();
    expect(screen.getByText("Hindi")).toBeInTheDocument();
    expect(screen.getByText("Hinglish")).toBeInTheDocument();
  });

  it("filters episodes when a language filter tab is clicked", () => {
    render(<ScorecardView summary={mockSummary} episodeIds={mockEpisodeIds} />);
    // Initially all 4 episodes are present
    expect(screen.getByText("EP-SCEN-EN-01-abc")).toBeInTheDocument();
    expect(screen.getByText("EP-SCEN-TE-01-def")).toBeInTheDocument();

    // Click Telugu filter
    const teluguBtn = screen.getByRole("button", { name: /^Telugu/i });
    fireEvent.click(teluguBtn);

    // Telugu episode should be present, English should be filtered out
    expect(screen.getByText("EP-SCEN-TE-01-def")).toBeInTheDocument();
    expect(screen.queryByText("EP-SCEN-EN-01-abc")).not.toBeInTheDocument();
  });
});
