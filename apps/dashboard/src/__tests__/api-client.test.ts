import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  runBaselineEvaluation,
  getEvaluation,
  getEvaluationSummary,
  getEpisodeDetail,
  getEvidencePack,
  ApiError,
} from "../lib/api-client";

describe("Backend API Client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("runBaselineEvaluation issues POST /api/v1/evaluations/baseline", async () => {
    const mockData = {
      evaluation_id: "EVAL-TEST-123",
      status: "completed",
      total_scenarios: 16,
    };

    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response);

    const result = await runBaselineEvaluation({ customer_authenticated: true });
    expect(result.evaluation_id).toBe("EVAL-TEST-123");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/evaluations/baseline",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer_authenticated: true }),
      })
    );
  });

  it("getEvaluation issues GET /api/v1/evaluations/{id}", async () => {
    const mockData = {
      evaluation_id: "EVAL-01",
      status: "completed",
      summary: { total_scenarios: 16 },
    };

    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response);

    const result = await getEvaluation("EVAL-01");
    expect(result.evaluation_id).toBe("EVAL-01");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/evaluations/EVAL-01",
      expect.objectContaining({
        headers: { "Content-Type": "application/json" },
      })
    );
  });

  it("getEvaluationSummary issues GET /api/v1/evaluations/{id}/summary", async () => {
    const mockData = {
      evaluation_id: "EVAL-01",
      overall_resilience: 1.0,
      results_by_language: {},
    };

    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response);

    const result = await getEvaluationSummary("EVAL-01");
    expect(result.overall_resilience).toBe(1.0);
  });

  it("getEpisodeDetail issues GET /api/v1/evaluations/{id}/episodes/{episode_id}", async () => {
    const mockData = {
      episode_id: "EP-01",
      scenario_id: "SCEN-EN-01",
      turns: [],
      tool_calls: [],
    };

    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response);

    const result = await getEpisodeDetail("EVAL-01", "EP-01");
    expect(result.episode_id).toBe("EP-01");
    expect(result.scenario_id).toBe("SCEN-EN-01");
  });

  it("getEvidencePack issues GET /api/v1/evaluations/{id}/evidence-pack", async () => {
    const mockData = {
      evaluation_id: "EVAL-01",
      digest_sha256: "abcdef123456",
      status: "ready",
    };

    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: true,
      json: async () => mockData,
    } as Response);

    const result = await getEvidencePack("EVAL-01");
    expect(result.digest_sha256).toBe("abcdef123456");
  });

  it("throws ApiError when server returns non-200 status", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => ({ detail: "Evaluation not found" }),
    } as Response);

    await expect(getEvaluation("UNKNOWN-ID")).rejects.toThrow(ApiError);
  });
});

