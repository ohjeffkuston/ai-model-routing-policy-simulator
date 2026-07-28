# Day 12 Project Guide: AI Model Routing Policy Simulator

To: Jeffrey Ikuoyemwen <ohjeffkuston@yahoo.ca>

## What you built

AI Model Routing Policy Simulator is an offline Python policy engine that decides whether a proposed AI request has a compliant model route. It checks provider approval, data classification, task risk, cost budget, latency SLO, model status, and fallback availability. It then returns `ALLOW`, `REVIEW`, or `BLOCK` with a selected route, fallbacks, rejected options, reason codes, policy version, and audit fingerprint.

## Architecture walkthrough

1. A request profile describes the workload without including production credentials.
2. A versioned policy contains the approved providers and model catalog.
3. The deterministic engine evaluates every route against all gates.
4. Eligible routes are sorted predictably; rejected routes retain their reasons.
5. Sensitive data or a missing fallback produces human review.
6. The result is evidence only. Real model execution remains in a separate authenticated gateway.

## Code map

- `src/.../engine.py`: validation, filtering, ranking, decision logic, and fingerprints.
- `src/.../cli.py`: reads JSON and prints or saves the report.
- `examples/routing-request.json`: synthetic policy and request.
- `tests/test_engine.py`: ten tests across allow, review, block, risk, cost, latency, provider, state, determinism, and validation.
- `docs/architecture.png`: the public architecture visual used on GitHub and social posts.
- `n8n/...json`: inactive manual-trigger integration template.
- `.github/workflows/ci.yml`: repeatable CI validation.

## Run it yourself

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m ai_model_routing_policy_simulator --input examples/routing-request.json
```

Change one input at a time: lower the cost budget, shorten the latency SLO, switch the classification to `restricted`, remove a provider, or retire a model. Observe the reason codes and decision. That experiment is the fastest way to understand the engine.

## How to explain it in an interview

Start with the problem: model routing is also a governance boundary. Explain that prompts are not authorization controls, so you separated probabilistic execution from deterministic policy. Walk through fail-closed validation, multi-gate eligibility, stable sorting, fallback enforcement, human review, and audit evidence. Close with the production extension: verified gateway telemetry, signed policies, identity-aware access, decision storage, and approval integration.

## Safe deployment direction

Package the simulator as a read-only internal service. Do not give it provider credentials. Place it before the model gateway, bind requests to authenticated identities, sign policy versions, log decisions immutably, and re-evaluate immediately before execution. Production routing must remain gated by human and infrastructure approvals appropriate to the risk.

## Resume and portfolio value

This project demonstrates AI orchestration, policy-as-code, governance, Python, deterministic testing, CI/CD, Docker, n8n integration design, cost awareness, SLO thinking, and security boundaries. It supports AI generalist, AI automation, platform, cloud, DevOps, and AI-first problem-solver roles without claiming production model operations.
