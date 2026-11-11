"""Unit tests for FastAPI Presentation Endpoints (Task 4B).

Tests:
- GET /healthz and GET /readyz liveness/readiness probes
- POST /api/v1/evaluations/baseline batch execution
- GET /api/v1/evaluations/{evaluation_id} retrieval
- GET /api/v1/evaluations/{evaluation_id}/summary retrieval
- GET /api/v1/evaluations/{evaluation_id}/episodes/{episode_id} trace inspection
- GET /api/v1/evaluations/{evaluation_id}/evidence-pack digest computation
- 404 Not Found handling on unknown evaluation and episode IDs
- X-Request-ID header propagation
- Zero leakage of environment secrets, API keys, or raw configurations
- Gemini judge remains disabled by default
"""

from fastapi.testclient import TestClient
import pytest

from nammakam_api.container import get_evaluation_repository
from nammakam_api.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture providing an offline TestClient and clearing in-memory repository state."""
    repo = get_evaluation_repository()
    repo.clear()
    return TestClient(app)


class TestHealthAndReadinessEndpoints:
    def test_healthz_liveness_probe(self, client: TestClient) -> None:
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "nammakam-api"

    def test_readyz_readiness_probe_shows_gemini_disabled(self, client: TestClient) -> None:
        response = client.get("/readyz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "nammakam-api"
        assert data["version"] == "0.1.0"
        # Gemini judge must remain disabled by default
        assert data["gemini_judge_enabled"] is False

    def test_request_id_header_propagated(self, client: TestClient) -> None:
        custom_id = "req-custom-trace-12345"
        response = client.get("/healthz", headers={"x-request-id": custom_id})
        assert response.status_code == 200
        assert response.headers.get("x-request-id") == custom_id


class TestEvaluationEndpoints:
    def test_create_baseline_evaluation_runs_and_stores_suite(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/evaluations/baseline",
            json={"customer_authenticated": True, "metadata": {"tag": "ci_test"}},
        )
        assert response.status_code == 201
        data = response.json()

        assert data["status"] == "completed"
        assert data["evaluation_id"].startswith("EVAL-")
        assert data["total_scenarios"] == 16
        assert data["scenarios_passed"] == 16
        assert data["scenarios_failed"] == 0
        assert data["overall_resilience"] == 1.0
        assert data["overall_protection"] == 0.875
        assert data["overall_parity"] == 1.0
        assert len(data["episode_ids"]) == 16
        assert data["summary_url"] == f"/api/v1/evaluations/{data['evaluation_id']}/summary"
        assert data["evidence_pack_url"] == f"/api/v1/evaluations/{data['evaluation_id']}/evidence-pack"

    def test_get_evaluation_detail(self, client: TestClient) -> None:
        # 1. Trigger evaluation
        create_res = client.post("/api/v1/evaluations/baseline")
        eval_id = create_res.json()["evaluation_id"]

        # 2. Query evaluation detail
        response = client.get(f"/api/v1/evaluations/{eval_id}")
        assert response.status_code == 200
        data = response.json()

        assert data["evaluation_id"] == eval_id
        assert data["status"] == "completed"
        assert len(data["episode_ids"]) == 16
        assert data["summary"]["total_scenarios"] == 16

    def test_get_evaluation_summary_breakdowns(self, client: TestClient) -> None:
        create_res = client.post("/api/v1/evaluations/baseline")
        eval_id = create_res.json()["evaluation_id"]

        response = client.get(f"/api/v1/evaluations/{eval_id}/summary")
        assert response.status_code == 200
        summary = response.json()

        # Language metrics
        assert set(summary["results_by_language"].keys()) == {"en-IN", "te", "hi", "hinglish"}
        for lang_metrics in summary["results_by_language"].values():
            assert lang_metrics["total_scenarios"] == 4
            assert lang_metrics["passed"] == 4
            assert lang_metrics["resilience_score"] == 1.0

        # Parity gaps
        assert set(summary["parity_gap_by_language"].keys()) == {"te", "hi", "hinglish"}
        for gap in summary["parity_gap_by_language"].values():
            assert gap["refusal_gap"] == 0.0
            assert gap["attack_gap"] == 0.0
            assert gap["parity_score"] == 1.0

        # Scenario types
        assert summary["results_by_scenario_type"]["genuine_customer"]["total"] == 8
        assert summary["results_by_scenario_type"]["adversarial"]["total"] == 8

    def test_get_individual_episode_detail(self, client: TestClient) -> None:
        create_res = client.post("/api/v1/evaluations/baseline")
        eval_data = create_res.json()
        eval_id = eval_data["evaluation_id"]
        episode_id = eval_data["episode_ids"][0]

        response = client.get(f"/api/v1/evaluations/{eval_id}/episodes/{episode_id}")
        assert response.status_code == 200
        ep_data = response.json()

        assert ep_data["episode_id"] == episode_id
        assert "SCEN-" in ep_data["scenario_id"]
        assert ep_data["is_safe"] is True
        assert len(ep_data["turns"]) >= 1
        assert "judgment" in ep_data
        assert ep_data["judgment"]["verdict"] == "safe"
        assert ep_data["judgment"]["is_deterministic"] is True

    def test_get_evidence_pack_digest_and_status(self, client: TestClient) -> None:
        create_res = client.post("/api/v1/evaluations/baseline")
        eval_id = create_res.json()["evaluation_id"]

        response = client.get(f"/api/v1/evaluations/{eval_id}/evidence-pack")
        assert response.status_code == 200
        pack = response.json()

        assert pack["evaluation_id"] == eval_id
        assert pack["evidence_pack_id"] == f"PACK-{eval_id}"
        assert pack["status"] == "ready"
        assert pack["total_episodes"] == 16
        assert len(pack["digest_sha256"]) == 64  # Valid SHA-256 hex string
        assert pack["signed"] is False
        assert "Cloud KMS" in pack["verification_notes"]

    def test_unknown_evaluation_id_returns_404(self, client: TestClient) -> None:
        unknown_id = "EVAL-DOESNOTEXIST"
        assert client.get(f"/api/v1/evaluations/{unknown_id}").status_code == 404
        assert client.get(f"/api/v1/evaluations/{unknown_id}/summary").status_code == 404
        assert client.get(f"/api/v1/evaluations/{unknown_id}/evidence-pack").status_code == 404
        assert client.get(f"/api/v1/evaluations/{unknown_id}/episodes/EP-01").status_code == 404

    def test_unknown_episode_id_returns_404(self, client: TestClient) -> None:
        create_res = client.post("/api/v1/evaluations/baseline")
        eval_id = create_res.json()["evaluation_id"]

        res = client.get(f"/api/v1/evaluations/{eval_id}/episodes/EP-UNKNOWN-999")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_zero_secret_or_env_leakage(self, client: TestClient) -> None:
        response = client.get("/readyz")
        raw_text = response.text
        assert "GEMINI_API_KEY" not in raw_text
        assert "AIza" not in raw_text  # Common Google API key prefix

