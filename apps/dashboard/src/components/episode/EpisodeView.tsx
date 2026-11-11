"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Bot,
  User,
  Wrench,
  CheckCircle2,
  XCircle,
  Sparkles,
} from "lucide-react";
import { EpisodeDetail } from "@/types/evaluation";
import {
  SUPPORTED_LANGUAGES,
  VERDICT_CONFIG,
  ATTACK_FAMILY_LABELS,
} from "@/lib/constants";
import { formatDate } from "@/lib/format";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface EpisodeViewProps {
  episode: EpisodeDetail;
  evaluationId: string;
}

export function EpisodeView({ episode, evaluationId }: EpisodeViewProps) {
  const langInfo = SUPPORTED_LANGUAGES[episode.language] || {
    label: episode.language,
    nativeLabel: episode.language,
  };

  const verdictMeta = VERDICT_CONFIG[episode.judgment.verdict] || {
    label: episode.judgment.verdict,
    variant: "pending",
  };

  const attackLabel = episode.attack_family
    ? ATTACK_FAMILY_LABELS[episode.attack_family] || episode.attack_family
    : "Genuine Customer Request";

  return (
    <div className="space-y-6" data-testid="episode-view">
      {/* Back button and breadcrumb */}
      <div className="flex items-center justify-between">
        <Link href={`/evaluations/${evaluationId}`}>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Scorecard
          </Button>
        </Link>
        <span className="text-xs font-mono text-slate-500">
          Evaluation: {evaluationId}
        </span>
      </div>

      {/* Episode Header Card */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs font-semibold text-slate-500">
                  {episode.episode_id}
                </span>
                <span className="text-slate-300">•</span>
                <span className="font-mono text-xs font-semibold text-slate-700">
                  Scenario: {episode.scenario_id}
                </span>
                <span className="text-slate-300">•</span>
                <Badge variant="outline" className="text-xs">
                  {langInfo.label} ({langInfo.nativeLabel})
                </Badge>
                {episode.is_adversarial ? (
                  <Badge variant="unsafe" className="text-xs">
                    Adversarial Probe
                  </Badge>
                ) : (
                  <Badge variant="safe" className="text-xs">
                    Genuine Banking Request
                  </Badge>
                )}
              </div>
              <h1 className="mt-2 text-xl font-bold text-slate-900">
                {attackLabel}
              </h1>
            </div>

            <div className="flex flex-col sm:items-end gap-1.5">
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">
                Safety Verdict
              </span>
              <Badge variant={verdictMeta.variant} className="text-sm px-3 py-1">
                {verdictMeta.label}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="border-t border-slate-100 pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div>
              <span className="font-semibold text-slate-500">Deterministic Checks:</span>
              <p className="mt-0.5 text-slate-800">
                {episode.judgment.is_deterministic
                  ? "Evaluated via Nammakam deterministic safety regex & policy"
                  : "Assisted by semantic arbiter"}
              </p>
            </div>
            <div>
              <span className="font-semibold text-slate-500">Escalation Status:</span>
              <div className="mt-0.5 flex items-center gap-1.5">
                {episode.escalated ? (
                  <Badge variant="escalated" className="text-[11px]">
                    Escalated to Human Supervisor
                  </Badge>
                ) : (
                  <span className="text-slate-700">Not escalated</span>
                )}
              </div>
              {episode.escalation_reason && (
                <p className="mt-1 text-slate-500 italic">
                  Reason: {episode.escalation_reason}
                </p>
              )}
            </div>
            <div>
              <span className="font-semibold text-slate-500">Detected Violations:</span>
              {episode.violations.length > 0 ? (
                <ul className="mt-0.5 space-y-1">
                  {episode.violations.map((v, i) => (
                    <li key={i} className="text-rose-700 font-medium">
                      • {v}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-0.5 text-emerald-700 font-medium">
                  None (Zero violations recorded)
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Gemini Judge Arbiter Card (Conditional) */}
      {episode.judgment.gemini_response && (
        <Card className="border-indigo-200 bg-indigo-50/30">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-600" />
              <CardTitle className="text-sm font-semibold text-indigo-950">
                Gemini Semantic Arbiter Assessment
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-indigo-900/70">
              Evaluated under structured schema for ambiguous dialogue nuances.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            {episode.judgment.gemini_response.explanation && (
              <div>
                <span className="font-semibold text-slate-700">Explanation:</span>
                <p className="mt-0.5 text-slate-800">
                  {episode.judgment.gemini_response.explanation}
                </p>
              </div>
            )}
            {episode.judgment.gemini_response.recommended_fix && (
              <div>
                <span className="font-semibold text-slate-700">Recommended Fix:</span>
                <p className="mt-0.5 text-slate-800">
                  {episode.judgment.gemini_response.recommended_fix}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Turn-by-Turn Dialogue Transcript */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Dialogue Transcript</CardTitle>
          <CardDescription>
            Multi-turn conversation between the simulated caller and the bank agent.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {episode.turns.map((turn) => {
              const isCaller = turn.role === "caller";
              return (
                <div
                  key={turn.turn_index}
                  className={`flex gap-3 p-4 rounded-xl border ${
                    isCaller
                      ? "border-amber-200 bg-amber-50/40"
                      : "border-slate-200 bg-white shadow-sm"
                  }`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                      isCaller
                        ? "bg-amber-600 text-white"
                        : "bg-slate-900 text-white"
                    }`}
                  >
                    {isCaller ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-slate-900">
                        {isCaller ? "Caller (Simulated Customer / Attacker)" : "Nammakam Bank Agent"}
                      </span>
                      <span className="text-slate-400">
                        Turn #{turn.turn_index + 1}
                      </span>
                    </div>
                    <p className="text-sm text-slate-800 whitespace-pre-wrap leading-relaxed select-text">
                      {turn.content}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Tool Invocations Ledger */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Wrench className="h-4 w-4 text-slate-600" />
            <CardTitle className="text-base">Tool Invocations & Attempts</CardTitle>
          </div>
          <CardDescription>
            All banking tool interactions attempted by the agent during this session.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {episode.tool_calls.length === 0 ? (
            <p className="text-xs text-slate-500 italic">
              No banking tools were invoked during this session.
            </p>
          ) : (
            <div className="space-y-3">
              {episode.tool_calls.map((tc, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-slate-200 bg-slate-50/50 p-4 font-mono text-xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-indigo-700">
                        {tc.tool_name}()
                      </span>
                      {tc.authorized ? (
                        <Badge variant="safe" className="text-[10px]">
                          Authorized
                        </Badge>
                      ) : (
                        <Badge variant="unsafe" className="text-[10px]">
                          Unauthorized Attempt
                        </Badge>
                      )}
                    </div>
                    <span className="text-slate-400">{tc.call_id}</span>
                  </div>

                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="rounded bg-white p-2.5 border border-slate-200">
                      <span className="font-sans font-semibold text-slate-600">Parameters:</span>
                      <pre className="mt-1 text-slate-800 overflow-x-auto">
                        {JSON.stringify(tc.parameters, null, 2)}
                      </pre>
                    </div>
                    <div className="rounded bg-white p-2.5 border border-slate-200">
                      <span className="font-sans font-semibold text-slate-600">Result:</span>
                      <pre className="mt-1 text-slate-800 overflow-x-auto">
                        {JSON.stringify(tc.result, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

