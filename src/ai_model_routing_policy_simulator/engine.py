"""Policy evaluation engine. It makes no network calls and executes no model."""

from __future__ import annotations

import hashlib
import json
from typing import Any


CLASSIFICATION = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}
RISK = {"low", "medium", "high"}


def _fingerprint(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _validate(policy: dict[str, Any], request: dict[str, Any]) -> None:
    required_request = {
        "request_id", "data_classification", "risk_level", "estimated_tokens",
        "cost_budget_usd", "latency_slo_ms", "allowed_providers",
    }
    missing = sorted(required_request - request.keys())
    if missing:
        raise ValueError(f"missing request fields: {', '.join(missing)}")
    if request["data_classification"] not in CLASSIFICATION:
        raise ValueError("unknown data_classification")
    if request["risk_level"] not in RISK:
        raise ValueError("unknown risk_level")
    if request["estimated_tokens"] <= 0 or request["cost_budget_usd"] < 0:
        raise ValueError("token estimate must be positive and budget non-negative")
    if request["latency_slo_ms"] <= 0:
        raise ValueError("latency_slo_ms must be positive")
    if not isinstance(request["allowed_providers"], list) or not request["allowed_providers"]:
        raise ValueError("allowed_providers must be a non-empty list")
    if not policy.get("models"):
        raise ValueError("policy must contain models")


def evaluate_route(policy: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Return an explainable ALLOW, REVIEW, or BLOCK routing decision."""
    _validate(policy, request)
    eligible: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    preferred = request.get("preferred_models", [])
    preferred_rank = {model: index for index, model in enumerate(preferred)}

    for model in policy["models"]:
        reasons: list[str] = []
        if model.get("status") != "active":
            reasons.append("MODEL_NOT_ACTIVE")
        if model.get("provider") not in request["allowed_providers"]:
            reasons.append("PROVIDER_NOT_ALLOWED")
        if model.get("provider") not in policy.get("approved_providers", []):
            reasons.append("PROVIDER_NOT_APPROVED")
        model_class = model.get("max_data_classification")
        if model_class not in CLASSIFICATION or CLASSIFICATION[model_class] < CLASSIFICATION[request["data_classification"]]:
            reasons.append("DATA_CLASSIFICATION_EXCEEDED")
        if request["risk_level"] not in model.get("allowed_risk_levels", []):
            reasons.append("RISK_LEVEL_NOT_ALLOWED")
        cost = round(request["estimated_tokens"] / 1000 * model.get("cost_per_1k_tokens", 0), 6)
        if cost > request["cost_budget_usd"]:
            reasons.append("COST_BUDGET_EXCEEDED")
        if model.get("p95_latency_ms", 10**9) > request["latency_slo_ms"]:
            reasons.append("LATENCY_SLO_EXCEEDED")
        item = {
            "model_id": model.get("model_id"),
            "provider": model.get("provider"),
            "estimated_cost_usd": cost,
            "p95_latency_ms": model.get("p95_latency_ms"),
        }
        if reasons:
            rejected.append({**item, "reason_codes": sorted(set(reasons))})
        else:
            eligible.append(item)

    eligible.sort(key=lambda item: (
        preferred_rank.get(item["model_id"], len(preferred_rank)),
        item["estimated_cost_usd"], item["p95_latency_ms"], item["model_id"],
    ))
    rejected.sort(key=lambda item: item["model_id"] or "")

    decision = "ALLOW"
    reason_codes: list[str] = []
    if not eligible:
        decision = "BLOCK"
        reason_codes.append("NO_POLICY_COMPLIANT_ROUTE")
    else:
        review_classes = policy.get("human_review_classifications", ["restricted"])
        if request["data_classification"] in review_classes:
            decision = "REVIEW"
            reason_codes.append("SENSITIVE_DATA_REQUIRES_REVIEW")
        required_routes = 2 if policy.get("require_fallback", True) else 1
        if len(eligible) < required_routes:
            decision = "REVIEW"
            reason_codes.append("NO_COMPLIANT_FALLBACK")

    result = {
        "request_id": request["request_id"],
        "decision": decision,
        "reason_codes": sorted(set(reason_codes)),
        "selected_route": eligible[0] if eligible else None,
        "fallback_routes": eligible[1:],
        "rejected_routes": rejected,
        "policy_version": policy.get("policy_version", "unversioned"),
    }
    result["evidence_fingerprint"] = _fingerprint({"policy": policy, "request": request, "result": result})
    return result
