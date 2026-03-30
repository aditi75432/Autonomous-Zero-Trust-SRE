from typing import Tuple, Dict, Any
from .models import Observation, Action, Reward, Alert, Severity, ServiceStatus, ActionType

class CloudSecEnv:
    def __init__(self):
        self.current_task_id = None
        self.state_data = None
        self.step_count = 0
        self.max_steps = 10
        self.logs_investigated = False
        self.final_score = 0.0

    def set_task(self, task_id: str):
        self.current_task_id = task_id
        self.reset()

    def reset(self) -> Observation:
        self.step_count = 0
        self.logs_investigated = False
        self.final_score = 0.0
        
        self.state_data = Observation(
            active_alerts=[
                Alert(alert_id="ALT-000", severity=Severity.LOW, description="Routine CPU spike detected on image-processor pod", target_service="image-processor")
            ],
            blocked_ips=[],
            isolated_services=[],
            revoked_roles=[],
            service_health={
                "frontend-web": ServiceStatus.HEALTHY, 
                "hr-database": ServiceStatus.HEALTHY, 
                "payment-gateway": ServiceStatus.HEALTHY,
                "auth-service": ServiceStatus.HEALTHY,
                "cache-redis": ServiceStatus.HEALTHY,
                "image-processor": ServiceStatus.DEGRADED,
                "email-worker": ServiceStatus.HEALTHY,
                "analytics-engine": ServiceStatus.HEALTHY
            }
        )

        if self.current_task_id == "easy_brute_force":
            self.state_data.active_alerts.append(
                Alert(alert_id="ALT-001", severity=Severity.HIGH, description="High volume failed SSH logins detected", source_ip="198.51.100.44", target_service="frontend-web")
            )
        elif self.current_task_id == "medium_lateral_movement":
             self.state_data.active_alerts.append(
                Alert(alert_id="ALT-002", severity=Severity.CRITICAL, description="Unauthorized lateral DB query detected", source_ip="frontend-web-pod-2", target_service="hr-database")
            )
        elif self.current_task_id == "hard_insider_threat":
             self.state_data.active_alerts.append(
                Alert(alert_id="ALT-003", severity=Severity.CRITICAL, description="Massive data exfiltration detected. API Key leaked.", source_ip="iam-role-billing-service", target_service="payment-gateway")
            )

        return self.state_data

    def state(self) -> Observation:
        return self.state_data

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        self.step_count += 1
        done = False
        reward_val = 0.0
        msg = f"Step {self.step_count}: Action processed."
        
        # --- DYNAMIC UPGRADE 1: Temporal Escalation ---
        if self.step_count == 3:
            for alert in self.state_data.active_alerts:
                if alert.severity == Severity.HIGH:
                    alert.severity = Severity.CRITICAL
                    msg += " [SYSTEM ALERT: Threat escalated to CRITICAL due to delayed response!]"

        # --- DYNAMIC UPGRADE 2: Infrastructure Cascading Failures ---
        if action.action_type == ActionType.ISOLATE_MICROSERVICE:
            self.state_data.isolated_services.append(action.target)
            if action.target == "auth-service":
                self.state_data.service_health["frontend-web"] = ServiceStatus.DEGRADED
                self.state_data.service_health["payment-gateway"] = ServiceStatus.DEGRADED
                msg += " [CASCADE ALARM: Isolating auth-service has degraded frontend and payment systems.]"

        # --- DYNAMIC UPGRADE 3: Multi-Factor Scoring Grader ---
        efficiency_bonus = max(0.0, (self.max_steps - self.step_count) / self.max_steps * 0.2)
        
        # EASY TASK
        if self.current_task_id == "easy_brute_force":
            if action.action_type == ActionType.BLOCK_IP and action.target == "198.51.100.44":
                self.state_data.blocked_ips.append(action.target)
                self.state_data.active_alerts = [a for a in self.state_data.active_alerts if a.alert_id != "ALT-001"]
                reward_val = 0.8 + efficiency_bonus
                msg += f" Threat neutralized. Efficiency Bonus: +{efficiency_bonus:.2f}"
                self.final_score = round(reward_val, 2)
                done = True
            elif action.action_type == ActionType.BLOCK_IP:
                reward_val = -0.2 
                msg += " Wrong IP blocked. Collateral damage incurred."

        # MEDIUM TASK
        elif self.current_task_id == "medium_lateral_movement":
            if action.action_type == ActionType.ISOLATE_MICROSERVICE and action.target == "frontend-web-pod-2":
                self.state_data.active_alerts = [a for a in self.state_data.active_alerts if a.alert_id != "ALT-002"]
                reward_val = 0.8 + efficiency_bonus
                msg += " Compromised pod isolated. DB secure."
                self.final_score = round(reward_val, 2)
                done = True
            elif action.target == "hr-database":
                self.state_data.service_health["hr-database"] = ServiceStatus.OFFLINE
                reward_val = -1.0 
                self.final_score = 0.0
                msg += " CRITICAL FAILURE: HR Database isolated! Global outage."
                done = True
                
        # HARD TASK
        elif self.current_task_id == "hard_insider_threat":
            if action.action_type == ActionType.QUERY_LOGS:
                self.logs_investigated = True
                reward_val = 0.2
                msg += " Logs queried. Audit trail established."
                
            elif action.action_type == ActionType.REVOKE_IAM_ROLE and action.target == "iam-role-billing-service":
                if self.logs_investigated:
                    self.state_data.revoked_roles.append(action.target)
                    self.state_data.active_alerts = [a for a in self.state_data.active_alerts if a.alert_id != "ALT-003"]
                    reward_val = 0.8 + efficiency_bonus
                    msg += " IAM Role safely revoked based on audit logs."
                    self.final_score = round(reward_val, 2)
                    done = True
                else:
                    reward_val = -1.0
                    self.final_score = 0.0
                    msg += " CRITICAL COMPLIANCE FAILURE: Blind role revocation without log analysis."
                    done = True

        if self.step_count >= self.max_steps and not done:
            done = True
            self.final_score = 0.0
            msg += " Episode terminated: Max steps reached."

        reward = Reward(value=reward_val, message=msg)
        return self.state_data, reward, done, {"step_count": self.step_count}