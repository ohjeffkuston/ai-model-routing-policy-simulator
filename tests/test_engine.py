import unittest

from ai_model_routing_policy_simulator.engine import evaluate_route


def fixture():
    policy = {
        "policy_version": "2026-07-28",
        "approved_providers": ["provider-a", "provider-b"],
        "require_fallback": True,
        "human_review_classifications": ["restricted"],
        "models": [
            {"model_id": "fast", "provider": "provider-a", "status": "active", "max_data_classification": "confidential", "allowed_risk_levels": ["low", "medium"], "cost_per_1k_tokens": 0.01, "p95_latency_ms": 600},
            {"model_id": "safe", "provider": "provider-b", "status": "active", "max_data_classification": "restricted", "allowed_risk_levels": ["low", "medium", "high"], "cost_per_1k_tokens": 0.02, "p95_latency_ms": 800},
            {"model_id": "legacy", "provider": "provider-a", "status": "retired", "max_data_classification": "restricted", "allowed_risk_levels": ["low"], "cost_per_1k_tokens": 0.005, "p95_latency_ms": 500},
        ],
    }
    request = {"request_id": "req-001", "data_classification": "internal", "risk_level": "low", "estimated_tokens": 1000, "cost_budget_usd": 0.05, "latency_slo_ms": 1000, "allowed_providers": ["provider-a", "provider-b"], "preferred_models": ["safe"]}
    return policy, request


class RoutingTests(unittest.TestCase):
    def test_allows_with_selected_and_fallback(self):
        p, r = fixture(); result = evaluate_route(p, r)
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["selected_route"]["model_id"], "safe")
        self.assertEqual(result["fallback_routes"][0]["model_id"], "fast")

    def test_deterministic_fingerprint(self):
        p, r = fixture()
        self.assertEqual(evaluate_route(p, r), evaluate_route(p, r))

    def test_blocks_when_no_route(self):
        p, r = fixture(); r["cost_budget_usd"] = 0
        self.assertEqual(evaluate_route(p, r)["decision"], "BLOCK")

    def test_restricted_requires_review(self):
        p, r = fixture(); r["data_classification"] = "restricted"
        self.assertEqual(evaluate_route(p, r)["decision"], "REVIEW")

    def test_missing_fallback_requires_review(self):
        p, r = fixture(); r["allowed_providers"] = ["provider-b"]
        self.assertIn("NO_COMPLIANT_FALLBACK", evaluate_route(p, r)["reason_codes"])

    def test_provider_policy_is_enforced(self):
        p, r = fixture(); p["approved_providers"] = ["provider-a"]
        rejected = evaluate_route(p, r)["rejected_routes"]
        self.assertIn("PROVIDER_NOT_APPROVED", next(x for x in rejected if x["model_id"] == "safe")["reason_codes"])

    def test_latency_is_enforced(self):
        p, r = fixture(); r["latency_slo_ms"] = 700
        self.assertIn("LATENCY_SLO_EXCEEDED", next(x for x in evaluate_route(p, r)["rejected_routes"] if x["model_id"] == "safe")["reason_codes"])

    def test_risk_is_enforced(self):
        p, r = fixture(); r["risk_level"] = "high"
        self.assertIn("RISK_LEVEL_NOT_ALLOWED", next(x for x in evaluate_route(p, r)["rejected_routes"] if x["model_id"] == "fast")["reason_codes"])

    def test_retired_model_is_rejected(self):
        p, r = fixture()
        self.assertIn("MODEL_NOT_ACTIVE", next(x for x in evaluate_route(p, r)["rejected_routes"] if x["model_id"] == "legacy")["reason_codes"])

    def test_invalid_classification_fails_closed(self):
        p, r = fixture(); r["data_classification"] = "secret"
        with self.assertRaises(ValueError): evaluate_route(p, r)


if __name__ == "__main__":
    unittest.main()
