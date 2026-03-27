---
title: Autonomous Zero Trust SRE
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
- openenv
emoji: 💻
---

# Autonomous Zero-Trust SRE Agent (OpenEnv)

## Environment Description & Motivation
Modern cloud infrastructure relies heavily on microservices and Zero-Trust architecture. During a cyberattack or severe misconfiguration, Level 1 SOC and SRE analysts are frequently overwhelmed by alert fatigue, forced to sift through thousands of logs to find the true threat. 

This OpenEnv project simulates a highly realistic Enterprise Cloud Security environment. It provides a non-game scenario where an AI agent acts as an autonomous Site Reliability Engineer. The agent must investigate active SIEM alerts, filter out enterprise "noise" (distractor microservices and low-priority alerts), and execute precise remediation actions without causing downtime to legitimate production traffic. 

Agents that perform well in this environment demonstrate the advanced sequential reasoning and consequence-awareness required for real-world automated incident response.

## Action & Observation Spaces

### Observation Space (Agent's View)
The environment returns a strict Pydantic JSON state representing the live cloud cluster:
* `active_alerts`: List of SIEM alerts (includes Severity, Description, Source, and Target).
* `blocked_ips`: The edge firewall blocklist.
* `isolated_services`: Internal microservices currently quarantined from the network.
* `revoked_roles`: IAM policies that have been actively revoked.
* `service_health`: Uptime status of core services (includes distractors like image-processors and cache-redis alongside core databases).

### Action Space (Agent's Controls)
The agent must respond with a typed JSON payload containing:
* `action_type`: Strict Enum (`block_ip`, `isolate_microservice`, `revoke_iam_role`, `restart_pod`, `query_logs`, `pass`).
* `target`: The specific IP, service ID, or IAM role to target.
* `justification`: A required string explaining the reasoning behind the action, which is mandatory for enterprise audit logging.

## Task Descriptions & Difficulty

1. Easy: The Brute Force (`easy_brute_force`)
   * Scenario: A high volume of failed SSH logins from an external IP is targeting the frontend.
   * Expected Action: Identify the source IP and execute `block_ip` at the edge firewall.
   * Grader: Verifies the exact IP is in the firewall blocklist.

2. Medium: The Lateral Movement (`medium_lateral_movement`)
   * Scenario: A frontend pod is compromised and attempting unauthorized queries to the internal HR database.
   * Expected Action: Execute `isolate_microservice` on the specific compromised pod. 
   * The Trap: If the agent panics and isolates the target HR database instead of the pod, it triggers a critical failure penalty (-1.0).

3. Hard: The Insider Threat (`hard_insider_threat`)
   * Scenario: A developer's API key is leaked, causing massive data exfiltration via the billing service IAM role.
   * Expected Action: The agent must perform sequential reasoning. It must first execute `query_logs` to investigate the anomaly, and then execute `revoke_iam_role` on the specific billing service. 
   * The Trap: If the agent blindly revokes the role without querying logs, it fails. If the agent isolates the payment gateway entirely, it causes a global production outage and fails.

## Setup & Usage Instructions

### Local Docker Testing (Hackathon Verification)
1. Build the container:
   ```bash
   docker build -t cloudsec-env .
   ```
2. Run the environment:
   ```bash
   docker run -p 7860:7860 cloudsec-env
   ```
3. Test the endpoints: The OpenEnv API will be live at `http://localhost:7860`.

### Running the Baseline
Ensure you have an OpenAI-compatible API key set in your environment variables:

```bash
export OPENAI_API_KEY="your-api-key-here"
python -m src.baseline
```

### Baseline Scores
Tested using `llama-3.1-8b` via the official OpenAI Python Client.

* **Easy Task:** 1.0/1.0
* **Medium Task:** 0.0/1.0 (The agent frequently falls for the distractor and accidentally takes down the database, proving the environment challenges frontier models).
* **Hard Task:** 0.0/1.0 (The agent struggles with the multi-step trajectory requirement of investigating logs before executing destructive IAM actions).
```

