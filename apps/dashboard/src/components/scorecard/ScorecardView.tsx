"use client";

import * as React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Filter,
  FileCheck2,
} from "lucide-react";
import { EvaluationSummary } from "@/types/evaluation";
import { SUPPORTED_LANGUAGES } from "@/lib/constants";
import { formatDate, formatPercent, formatScore } from "@/lib/format";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";

interface ScorecardViewProps {
  summary: EvaluationSummary;
  episodeIds?: string[];
  createdAt?: string;
}

export function ScorecardView({
  summary,
  episodeIds = [],
  createdAt,
}: ScorecardViewProps) {
  const [selectedLanguage, setSelectedLanguage] = React.useState<string>("all");

  const filteredEpisodes = React.useMemo(() => {
    if (selectedLanguage === "all") return episodeIds;
    // Map episode IDs: e.g. EP-SCEN-EN-01 -> en-IN, EP-SCEN-TE-01 -> te
    const langCodeMap: Record<string, string> = {
      EN: "en-IN",
      TE: "te",
      HI: "hi",
      HN: "hinglish",
    };
    return episodeIds.filter((id) => {
      const match = id.match(/EP-SCEN-([A-Z]{2})-/);
      if (!match) return false;
      const code = langCodeMap[match[1]];
      return code === selectedLanguage;
    });
  }, [episodeIds, selectedLanguage]);

  return (
    <div className="space-y-8" data-testid="scorecard-view">
      {/* Scope and Notice Banner */}
      <div className="rounded-xl border border-indigo-100 bg-gradient-to-r from-indigo-50/70 via-blue-50/50 to-slate-50 p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-md bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-800">
                Baseline Evaluation
              </span>
              <span className="text-xs text-slate-500">
                Run ID: <code className="font-mono text-slate-700">{summary.evaluation_id}</code>
              </span>
              {createdAt && (
                <span className="text-xs text-slate-400">
                  • {formatDate(createdAt)}
                </span>
              )}
            </div>
            <h2 className="mt-1 text-base font-semibold text-slate-900">
              Baseline evaluation of Nammakam’s synthetic mock bank agent.
            </h2>
            <p className="mt-0.5 text-xs text-slate-600">
              Systematic red-teaming across Indian languages measuring scam resilience, credential protection, and cross-lingual parity gaps.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link href={`/evaluations/${summary.evaluation_id}/evidence-pack`}>
              <Button variant="outline" size="sm" className="gap-1.5 text-xs">
                <FileCheck2 className="h-3.5 w-3.5 text-indigo-600" />
                View Evidence Pack
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Hero Metrics Tiles */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Resilience */}
        <Card className="border-l-4 border-l-emerald-500">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Resilience Score
            </CardDescription>
            <CardTitle className="text-3xl font-extrabold text-slate-900">
              {formatPercent(summary.overall_resilience)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-600">
              Adversarial defense success rate across all 8 injection and scam probes.
            </p>
          </CardContent>
        </Card>

        {/* Protection */}
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Protection Score
            </CardDescription>
            <CardTitle className="text-3xl font-extrabold text-slate-900">
              {formatScore(summary.overall_protection)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-600">
              Composite penalty score penalized by unsafe actions and wrongful refusals.
            </p>
          </CardContent>
        </Card>

        {/* Parity */}
        <Card className="border-l-4 border-l-indigo-500">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Cross-Lingual Parity
            </CardDescription>
            <CardTitle className="text-3xl font-extrabold text-slate-900">
              {formatPercent(summary.overall_parity)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-slate-600">
              Parity score relative to English baseline ($1.00$ represents zero disparity gap).
            </p>
          </CardContent>
        </Card>

        {/* Scenario Counts */}
        <Card className="border-l-4 border-l-slate-400">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs font-medium uppercase tracking-wider text-slate-500">
              Total Evaluated
            </CardDescription>
            <CardTitle className="text-3xl font-extrabold text-slate-900">
              {summary.total_scenarios}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2 text-xs">
            <Badge variant="safe" className="gap-1">
              <CheckCircle2 className="h-3 w-3" />
              {summary.scenarios_passed} Passed
            </Badge>
            {summary.scenarios_failed > 0 && (
              <Badge variant="unsafe" className="gap-1">
                <XCircle className="h-3 w-3" />
                {summary.scenarios_failed} Failed
              </Badge>
            )}
            {summary.scenarios_escalated > 0 && (
              <Badge variant="escalated" className="gap-1">
                <AlertTriangle className="h-3 w-3" />
                {summary.scenarios_escalated} Escalated
              </Badge>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Language Breakdown & Parity Gap Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <CardTitle className="text-lg">Language-Wise Safety & Parity Matrix</CardTitle>
              <CardDescription>
                Resilience, protection, and gap metrics comparing Indic languages to the English baseline.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Language</TableHead>
                <TableHead>Total Probes</TableHead>
                <TableHead>Passed</TableHead>
                <TableHead>Escalated</TableHead>
                <TableHead>Resilience</TableHead>
                <TableHead>Protection</TableHead>
                <TableHead>Refusal Gap vs EN</TableHead>
                <TableHead>Attack Gap vs EN</TableHead>
                <TableHead>Parity Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(summary.results_by_language).map(([langKey, metrics]) => {
                const langInfo = SUPPORTED_LANGUAGES[langKey] || {
                  label: langKey,
                  nativeLabel: langKey,
                };
                const parityGap = summary.parity_gap_by_language[langKey];
                const isBaseline = langKey === "en-IN";

                return (
                  <TableRow key={langKey}>
                    <TableCell className="font-medium text-slate-900">
                      <div>
                        <span>{langInfo.label}</span>
                        <span className="ml-1.5 text-xs text-slate-400">
                          ({langInfo.nativeLabel})
                        </span>
                        {isBaseline && (
                          <span className="ml-2 inline-flex items-center rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-600">
                            Baseline
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{metrics.total_scenarios}</TableCell>
                    <TableCell>
                      <Badge variant="safe">{metrics.passed}</Badge>
                    </TableCell>
                    <TableCell>
                      {metrics.escalated > 0 ? (
                        <Badge variant="escalated">{metrics.escalated}</Badge>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </TableCell>
                    <TableCell className="font-semibold text-slate-900">
                      {formatPercent(metrics.resilience_score)}
                    </TableCell>
                    <TableCell className="font-semibold text-slate-900">
                      {formatScore(metrics.protection_score)}
                    </TableCell>
                    <TableCell>
                      {isBaseline ? (
                        <span className="text-xs text-slate-400">— (Ref)</span>
                      ) : (
                        <span className="text-slate-700">
                          {formatPercent(parityGap?.refusal_gap ?? 0)}
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {isBaseline ? (
                        <span className="text-xs text-slate-400">— (Ref)</span>
                      ) : (
                        <span className="text-slate-700">
                          {formatPercent(parityGap?.attack_gap ?? 0)}
                        </span>
                      )}
                    </TableCell>
                    <TableCell>
                      {isBaseline ? (
                        <span className="font-bold text-slate-900">100.0%</span>
                      ) : (
                        <span className="font-semibold text-indigo-700">
                          {formatPercent(parityGap?.parity_score ?? 1.0)}
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Episode Drill-down Section */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <CardTitle className="text-lg">Evaluated Episodes</CardTitle>
              <CardDescription>
                Click any episode to inspect the full transcript, tool calls, and safety arbitration judgment.
              </CardDescription>
            </div>

            {/* Language Filter */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <span className="text-xs font-medium text-slate-600">Filter:</span>
              <div className="flex flex-wrap gap-1">
                <button
                  type="button"
                  onClick={() => setSelectedLanguage("all")}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    selectedLanguage === "all"
                      ? "bg-slate-900 text-white"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  All ({episodeIds.length})
                </button>
                {Object.entries(SUPPORTED_LANGUAGES).map(([key, lang]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setSelectedLanguage(key)}
                    className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                      selectedLanguage === key
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {lang.label.split(" ")[0]}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {filteredEpisodes.map((epId) => {
              // Parse language code from episode ID
              const langCode = epId.includes("EN")
                ? "en-IN"
                : epId.includes("TE")
                ? "te"
                : epId.includes("HI")
                ? "hi"
                : "hinglish";
              const langLabel = SUPPORTED_LANGUAGES[langCode]?.label || langCode;

              return (
                <Link
                  key={epId}
                  href={`/evaluations/${summary.evaluation_id}/episodes/${epId}`}
                  className="group block rounded-lg border border-slate-200 bg-white p-4 shadow-sm hover:border-indigo-400 hover:shadow-md transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-slate-800 group-hover:text-indigo-600">
                      {epId}
                    </span>
                    <Badge variant="safe">Safe</Badge>
                  </div>
                  <div className="mt-2 text-xs text-slate-500">
                    Language: <span className="font-medium text-slate-700">{langLabel}</span>
                  </div>
                  <div className="mt-3 flex items-center justify-end text-xs font-medium text-indigo-600 group-hover:translate-x-1 transition-transform">
                    <span>Inspect trace</span>
                    <ArrowRight className="ml-1 h-3.5 w-3.5" />
                  </div>
                </Link>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
