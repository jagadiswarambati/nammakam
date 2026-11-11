import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { EvidencePackView } from "../components/evidence/EvidencePackView";
import { EvidencePack } from "../types/evaluation";

const mockPack: EvidencePack = {
  evaluation_id: "EVAL-01",
  evidence_pack_id: "PACK-EVAL-01",
  status: "ready",
  digest_sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  total_episodes: 16,
  signed: false,
  verification_notes: "Computed SHA-256 digest across 16 canonical episode traces. Ready for Cloud KMS signature.",
  created_at: "2026-11-11T12:00:00Z",
};

describe("EvidencePackView Component", () => {
  it("renders SHA-256 digest and status", () => {
    render(<EvidencePackView evidencePack={mockPack} />);
    expect(screen.getByText("Cryptographic Evidence Pack")).toBeInTheDocument();
    expect(screen.getByText(/STATUS: READY/i)).toBeInTheDocument();
    expect(
      screen.getByText("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
    ).toBeInTheDocument();
  });

  it("renders total episode count and verification notes", () => {
    render(<EvidencePackView evidencePack={mockPack} />);
    expect(screen.getByText("16 Episodes")).toBeInTheDocument();
    expect(screen.getByText(/Cloud KMS signature/i)).toBeInTheDocument();
  });
});

