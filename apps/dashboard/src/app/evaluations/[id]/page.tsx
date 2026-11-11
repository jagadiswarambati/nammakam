"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { getEvaluation } from "@/lib/api-client";
import { ScorecardView } from "@/components/scorecard/ScorecardView";
import { Button } from "@/components/ui/button";

export default function EvaluationPage() {
  const params = useParams();
  const evaluationId = params?.id as string;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["evaluation", evaluationId],
    queryFn: () => getEvaluation(evaluationId),
    enabled: Boolean(evaluationId),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4" data-testid="loading-state">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        <p className="text-sm font-medium text-slate-600">
          Loading evaluation scorecard...
        </p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-8 text-center space-y-4" data-testid="error-state">
        <AlertCircle className="mx-auto h-10 w-10 text-rose-600" />
        <div>
          <h3 className="text-base font-semibold text-rose-900">
            Failed to Load Evaluation
          </h3>
          <p className="mt-1 text-xs text-rose-700">
            {error instanceof Error ? error.message : "Unknown error occurred"}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          className="gap-1.5 text-xs bg-white"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <ScorecardView
      summary={data.summary}
      episodeIds={data.episode_ids}
      createdAt={data.created_at}
    />
  );
}
