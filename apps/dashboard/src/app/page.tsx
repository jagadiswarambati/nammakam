"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  ShieldAlert,
  ShieldCheck,
  Play,
  Loader2,
  AlertCircle,
  FileCheck2,
  ArrowRight,
  Sparkles,
  Languages,
} from "lucide-react";
import { runBaselineEvaluation } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function HomePage() {
  const router = useRouter();

  // Baseline evaluation mutation
  const evaluationMutation = useMutation({
    mutationFn: () => runBaselineEvaluation({ customer_authenticated: true }),
    onSuccess: (data) => {
      // Navigate directly to the scorecard
      router.push(`/evaluations/${data.evaluation_id}`);
    },
  });

  return (
    <div className="space-y-10" data-testid="dashboard-home">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-8 sm:p-10 shadow-sm">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 border border-indigo-200 px-3 py-1 text-xs font-semibold text-indigo-700">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Indic Voice & Chat Safety Benchmark</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
            AI Safety Evaluation for Indian-Language Banking Agents
          </h1>

          <p className="text-base text-slate-600 leading-relaxed">
            Nammakam systematically evaluates conversational banking models across
            Telugu, Hindi, Hinglish, and English. We measure scam resilience,
            credential protection, and cross-lingual parity gaps to ensure safe and
            equitable automated banking.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row sm:items-center gap-3">
            <Button
              size="lg"
              onClick={() => evaluationMutation.mutate()}
              disabled={evaluationMutation.isPending}
              className="gap-2 text-sm bg-indigo-600 hover:bg-indigo-700 text-white font-semibold shadow-md"
              data-testid="run-evaluation-btn"
            >
              {evaluationMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Executing 16 Baseline Scenarios...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-current" />
                  <span>Run Baseline Evaluation</span>
                </>
              )}
            </Button>
            <span className="text-xs text-slate-500">
              Evaluates 16 multi-turn dialogue scenarios deterministically.
            </span>
          </div>

          {evaluationMutation.isError && (
            <div className="mt-4 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
              <span>
                Evaluation trigger failed. Ensure the FastAPI backend is running on{" "}
                <code>localhost:8000</code>.
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Scope Disclaimer Banner */}
      <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4 text-xs text-amber-900 flex items-start gap-3">
        <AlertCircle className="h-4 w-4 shrink-0 text-amber-700 mt-0.5" />
        <div>
          <span className="font-semibold">Notice:</span> Baseline evaluation of
          Nammakam’s synthetic mock bank agent. Operates strictly on synthetic
          in-memory accounts and dialogue sets. Zero connection to real financial
          systems or customer data.
        </div>
      </div>

      {/* Three Core Evaluation Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 text-emerald-800">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <CardTitle className="mt-3 text-base">Scam & Coercion Defense</CardTitle>
            <CardDescription className="text-xs">
              Detects compliance with digital-arrest intimidation, authority
              impersonation, and uncooled fund transfers.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs text-slate-600">
            Mandates supervisory escalation on coercive cues before any financial
            action can be triggered.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-800">
              <Languages className="h-5 w-5" />
            </div>
            <CardTitle className="mt-3 text-base">Cross-Lingual Parity</CardTitle>
            <CardDescription className="text-xs">
              Quantifies safety gap disparities across Telugu, Hindi, and
              Hinglish versus English baseline.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs text-slate-600">
            Ensures non-English banking customers receive the exact same defense
            rigor without disparate failure rates.
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-100 text-blue-800">
              <FileCheck2 className="h-5 w-5" />
            </div>
            <CardTitle className="mt-3 text-base">Cryptographic Evidence Packs</CardTitle>
            <CardDescription className="text-xs">
              Generates deterministic SHA-256 digests over transcripts and tool
              invocations.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-xs text-slate-600">
            Produces immutable proof of evaluation results for regulatory audit
            and compliance verification.
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
