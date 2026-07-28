# Governing AI Model Routing Before Any Model Is Called

![AI Model Routing Policy Simulator architecture](https://raw.githubusercontent.com/ohjeffkuston/ai-model-routing-policy-simulator/main/docs/architecture.png)

AI orchestration is often presented as a routing problem: select the model with the best quality, lowest cost, or fastest response. In an enterprise, the harder question comes first: **is this model route permitted for this request?**

A request may contain confidential data, represent a high-risk business decision, have a strict latency objective, or require an approved fallback. A route that is technically available can still violate policy. If those controls live only in prompts or informal workflow conventions, the evidence is difficult to test and audit.

## A deterministic policy boundary

I built **AI Model Routing Policy Simulator** to demonstrate a safer orchestration pattern. The project accepts a versioned policy and a request profile, evaluates every candidate model, and returns an explainable `ALLOW`, `REVIEW`, or `BLOCK` decision before any model is called.

The engine checks:

- model and provider approval status;
- the request's data classification;
- task risk permitted by the model policy;
- estimated cost against an explicit budget;
- p95 latency against the request SLO;
- availability of a policy-compliant fallback.

Eligible routes are ordered deterministically: stated preference, estimated cost, latency, then model identifier. This makes the result reproducible and testable. Rejected routes include reason codes, while the complete decision receives a stable evidence fingerprint.

## Why `REVIEW` matters

Binary allow/deny logic is not enough for every enterprise workflow. Restricted data may require a human approval even when a compliant model exists. A request may also have one eligible route but no fallback, creating a resilience risk. The simulator returns `REVIEW` for those conditions instead of silently accepting them.

## The safety boundary

The project deliberately calls no LLM, cloud service, or external provider. It holds no credentials and executes no routed task. That separation is the point: a probabilistic system can propose work, a deterministic policy layer can evaluate it, and an authenticated gateway plus human approval can retain authority over execution.

The repository includes ten unit tests, sample policy data, GitHub Actions CI, Docker packaging, and an inactive n8n workflow template. The example is safe to run offline and designed to be extended without pretending that a simulator is a production enforcement point.

## The larger lesson

AI orchestration should optimize only inside an approved boundary. When data sensitivity, provider trust, cost, latency, and fallback requirements are encoded as policy, model routing becomes easier to explain, review, and improve.

The project is available on [GitHub](https://github.com/ohjeffkuston/ai-model-routing-policy-simulator).

What policy should always run before an enterprise AI request reaches a model?

Topics: Artificial Intelligence, AI Governance, DevOps, MLOps, Automation
