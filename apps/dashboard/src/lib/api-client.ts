/**
 * Backend API Client for Nammakam Evaluation Platform.
 */

import {
  BaselineEvaluationRun,
  EpisodeDetail,
  EvaluationSummary,
  EvidencePack,
} from "@/types/evaluation";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail: unknown = null;
    try {
      errorDetail = await response.json();
    } catch {
      errorDetail = await response.text();
    }
    throw new ApiError(
      response.status,
      `API request failed with status ${response.status}: ${path}`,
      errorDetail
    );
  }

  return response.json() as Promise<T>;
}

export async function runBaselineEvaluation(config?: {
  customer_authenticated?: boolean;
  metadata?: Record<string, unknown>;
}): Promise<BaselineEvaluationRun> {
  return request<BaselineEvaluationRun>("/api/v1/evaluations/baseline", {
    method: "POST",
    body: JSON.stringify(config || {}),
  });
}

export async function getEvaluation(
  evaluationId: string
): Promise<BaselineEvaluationRun & { summary: EvaluationSummary }> {
  return request<BaselineEvaluationRun & { summary: EvaluationSummary }>(
    `/api/v1/evaluations/${encodeURIComponent(evaluationId)}`
  );
}

export async function getEvaluationSummary(
  evaluationId: string
): Promise<EvaluationSummary> {
  return request<EvaluationSummary>(
    `/api/v1/evaluations/${encodeURIComponent(evaluationId)}/summary`
  );
}

export async function getEpisodeDetail(
  evaluationId: string,
  episodeId: string
): Promise<EpisodeDetail> {
  return request<EpisodeDetail>(
    `/api/v1/evaluations/${encodeURIComponent(
      evaluationId
    )}/episodes/${encodeURIComponent(episodeId)}`
  );
}

export async function getEvidencePack(
  evaluationId: string
): Promise<EvidencePack> {
  return request<EvidencePack>(
    `/api/v1/evaluations/${encodeURIComponent(evaluationId)}/evidence-pack`
  );
}
