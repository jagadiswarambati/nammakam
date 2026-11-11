"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  FileCheck2,
  Copy,
  Check,
  ShieldCheck,
  Lock,
} from "lucide-react";
import { EvidencePack } from "@/types/evaluation";
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

interface EvidencePackViewProps {
  evidencePack: EvidencePack;
}

export function EvidencePackView({ evidencePack }: EvidencePackViewProps) {
  const [copied, setCopied] = React.useState(false);

  const copyDigest = () => {
    navigator.clipboard.writeText(evidencePack.digest_sha256);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6" data-testid="evidence-pack-view">
      {/* Back button */}
      <div>
        <Link href={`/evaluations/${evidencePack.evaluation_id}`}>
          <Button variant="outline" size="sm" className="gap-1.5 text-xs">
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Scorecard
          </Button>
        </Link>
      </div>

      {/* Main Evidence Card */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-700">
                <FileCheck2 className="h-5 w-5" />
              </div>
              <div>
                <CardTitle className="text-xl">Cryptographic Evidence Pack</CardTitle>
                <CardDescription>
                  Tamper-evident verification digest for regulatory compliance and audit logs.
                </CardDescription>
              </div>
            </div>

            <Badge variant="safe" className="self-start sm:self-auto text-xs px-3 py-1">
              Status: {evidencePack.status.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 rounded-lg bg-slate-50 p-4 text-xs border border-slate-200">
            <div>
              <span className="font-semibold text-slate-500">Pack ID:</span>
              <p className="font-mono mt-0.5 text-slate-900 font-medium">
                {evidencePack.evidence_pack_id}
              </p>
            </div>
            <div>
              <span className="font-semibold text-slate-500">Evaluation Reference:</span>
              <p className="font-mono mt-0.5 text-slate-900 font-medium">
                {evidencePack.evaluation_id}
              </p>
            </div>
            <div>
              <span className="font-semibold text-slate-500">Total Encapsulated Episodes:</span>
              <p className="mt-0.5 text-slate-900 font-bold">
                {evidencePack.total_episodes} Episodes
              </p>
            </div>
          </div>

          {/* SHA-256 Digest Card */}
          <div className="rounded-xl border border-indigo-200 bg-indigo-50/40 p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-indigo-700" />
                <span className="text-xs font-semibold uppercase tracking-wider text-indigo-900">
                  Canonical SHA-256 Evidence Digest
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={copyDigest}
                className="h-7 gap-1 text-xs bg-white"
              >
                {copied ? (
                  <>
                    <Check className="h-3 w-3 text-emerald-600" />
                    <span>Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3 w-3" />
                    <span>Copy Hash</span>
                  </>
                )}
              </Button>
            </div>

            <div className="mt-3 rounded-lg bg-white p-3 border border-indigo-100 font-mono text-xs text-slate-800 break-all select-all">
              {evidencePack.digest_sha256}
            </div>

            <p className="mt-2 text-[11px] text-indigo-950/70">
              Computed deterministically across all episode turns, tool parameters, and judgments.
            </p>
          </div>

          {/* Verification Notes */}
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-slate-700" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-700">
                Integrity & Signing Protocol
              </h4>
            </div>
            <p className="mt-2 text-xs text-slate-600 leading-relaxed select-text">
              {evidencePack.verification_notes}
            </p>
            <div className="mt-3 flex items-center gap-2">
              <Badge variant="outline" className="text-[11px] text-slate-600">
                Cloud KMS Asymmetric Signing: Ready for Production Phase
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
