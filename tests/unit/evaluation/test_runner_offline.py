"""Unit Tests for Offline Evaluation Runner and Report Output."""

import json
from pathlib import Path
import tempfile
import pytest

from nammakam_api.evaluation.fixtures import load_evaluation_cases
from nammakam_api.evaluation.report import generate_markdown_report, write_json_report, write_markdown_report
from nammakam_api.evaluation.runner import EvaluationRunner, _redact_secrets


def test_offline_runner_deterministic() -> None:
    cases = load_evaluation_cases()
    runner = EvaluationRunner()

    # Run on first 5 cases
    sample = cases[:5]
    report1 = runner.run_suite(sample, mode="offline")
    report2 = runner.run_suite(sample, mode="offline")

    assert report1.summary.total_cases == 5
    assert report2.summary.total_cases == 5
    assert report1.summary.passed_cases == report2.summary.passed_cases
    assert report1.summary.accuracy == report2.summary.accuracy
    assert report1.summary.pass_rate == report2.summary.pass_rate

    # Ensure every result source is recorded_fixture
    for r in report1.case_results:
        assert r.response_source == "recorded_fixture"
        assert r.passed


def test_write_reports_to_disk() -> None:
    cases = load_evaluation_cases()[:3]
    runner = EvaluationRunner()
    report = runner.run_suite(cases, mode="offline")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_ts, json_latest = write_json_report(report, tmpdir)
        md_ts, md_latest = write_markdown_report(report, tmpdir)

        assert json_ts.exists()
        assert json_latest.exists()
        assert md_ts.exists()
        assert md_latest.exists()

        # Validate JSON content
        with open(json_latest, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["report_id"] == report.report_id
        assert data["mode"] == "offline"
        assert data["summary"]["total_cases"] == 3

        # Validate Markdown content
        with open(md_latest, "r", encoding="utf-8") as f:
            md_text = f.read()
        assert "# Nammakam — Gemini Judge Evaluation Report" in md_text
        assert "Executive Summary" in md_text
        assert "Category Performance Slices" in md_text


def test_redact_secrets() -> None:
    # Test Google API key redaction
    sample_key = "AIzaSyD-fakeKey1234567890abcdefghijkl"
    text = f"An error occurred with key {sample_key} in request."
    redacted = _redact_secrets(text)
    assert sample_key not in redacted
    assert "[REDACTED_KEY]" in redacted

