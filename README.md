---
title: Autonomous Zero Trust SRE
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
- openenv

---

# Autonomous Zero-Trust SRE Agent (OpenEnv)

[](https://www.google.com/search?q=https://github.com/openenv/spec)
[](https://www.google.com/search?q=https://huggingface.co/spaces/aditi75432/autonomous-zero-trust-sre)

## 1\. Executive Summary

**The Problem:** Modern enterprise cloud environments run on hundreds of interconnected microservices. When a cyberattack occurs, Level 1 Security Operations Center (SOC) analysts and Site Reliability Engineers (SREs) suffer from massive "alert fatigue." They must sift through thousands of false positives to find the real threat. If an analyst panics and shuts down the wrong database while trying to stop a hacker, they cause a self-inflicted global production outage.

**The Solution:** This project provides a real-world OpenEnv benchmark for Cloud Security. It simulates a Zero-Trust microservice cluster where agents must neutralize threats while maintaining 99.9% service uptime. Unlike toy environments, this agent implements **Negative Reward Constraints** for production-breaking actions, forcing frontier models to prioritize system uptime over aggressive remediation.

## 2\. Core Innovations: The Dynamic Environment

Most OpenEnv submissions rely on static states. This environment acts as a living simulation, implementing three advanced grading mechanics:

  * **Temporal Escalation:** Threats are not static. If the agent takes too many steps to resolve an issue, the threat severity automatically escalates from HIGH to CRITICAL, mimicking real-world breach dynamics.
  * **Cascading Infrastructure Failures:** Services do not exist in a vacuum. If the agent blindly isolates a core dependency (like an auth-service), downstream services (like the frontend and payment gateway) immediately degrade, penalizing the agent for collateral damage.
  * **Multi-Factor Scoring:** The deterministic grader does not just award a flat 1.0. It calculates a composite score based on threat neutralization (+), step efficiency (+), and collateral damage penalties (-).

## 3\. Mission Objectives & Difficulty Gradient

We evaluate agents across a difficulty gradient to measure their trajectory-planning and consequence-awareness capabilities.

| Task | Difficulty | Objective | The "Trap" (Negative Reward) |
| :--- | :--- | :--- | :--- |
| **Brute Force** | Easy | Block a malicious IP. | Blocking a legitimate internal service IP. |
| **Lateral Movement** | Medium | Isolate a compromised Pod. | Isolating the **Database** instead of the Pod (causing an outage). |
| **Insider Threat** | Hard | Revoke a leaked IAM Role. | Revoking the role **without** first using `query_logs` (Audit Failure). |

## 4\. Observation & Action Spaces

The environment communicates with the LLM using strict, strongly-typed JSON schemas (Pydantic models).

  * **Observation Space (What the AI sees):** A JSON payload containing `active_alerts`, `blocked_ips`, `isolated_services`, `revoked_roles`, and `service_health`.
  * **Action Space (What the AI does):** A strict JSON command requiring an `action_type` (Enum: block\_ip, isolate\_microservice, revoke\_iam\_role, etc.), a `target`, and a mandatory `justification` string for audit logging.

## 5\. System Architecture

The environment is built on a four-tier architecture designed for adversarial reasoning.

<img src="https://cdn-uploads.huggingface.co/production/uploads/69c60e74d6a5a36e8db49d9a/zeXTtzRI27I_JXgpV25y1.png" alt="Architecture Diagram" width="500">

  * **Layer 1: The Hosting Infrastructure:** A completely isolated `python:3.10-slim` Docker container hosted on Hugging Face Spaces.
  * **Layer 2: The OpenEnv Server (`src/api.py`):** A FastAPI-powered server implementing the full OpenEnv spec. It features a bulletproof POST/GET handler and a custom File I/O subsystem to bypass Linux console buffering, ensuring reliable score reporting.
  * **Layer 3: The Simulation Engine (`src/environment.py`):** A state-machine managing a cluster of 8 services. It manages step limits, injects "Enterprise Noise" (healthy distractor alerts), and calculates the multi-factor reward score.
  * **Layer 4: The AI Agent (`inference.py`):** Located at the repository root, the OpenAI SDK connects to the Groq API for Llama 3.1 inference. It implements anti-rate-limiting buffers to ensure reliable baseline execution.

## 6\. Setup & Usage Instructions

### Local Deployment (Docker)

```bash
# Build the container
docker build -t cloudsec-env .

# Run the environment
docker run -p 7860:7860 cloudsec-env
```

### Triggering the Baseline Evaluation

The environment includes a built-in baseline runner that handles the LLM reasoning loop.

```bash
export OPENAI_API_KEY="your_key_here"

# Trigger the evaluation via API
curl -X POST "https://your-space-url/baseline"
```

## 7\. Baseline Scores (Llama-3.1-8B-Instant)

| Task | Score | Result |
| :--- | :--- | :--- |
| **Easy** | 0.88 - 1.0 | Successful mitigation with efficiency bonus. |
| **Medium** | 0.0 | Agent panicked and isolated the Database (Global Outage). |
| **Hard** | 0.0 | Agent failed to perform sequential log investigation. |

**Conclusion:** This environment effectively challenges frontier models, proving that "Reasoning-over-Action" is the next hurdle for autonomous SRE agents.

