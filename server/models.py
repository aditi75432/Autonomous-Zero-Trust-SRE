from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum


# ENUMS (Strict constraints for the AI)

class ActionType(str, Enum):
    BLOCK_IP = "block_ip"
    ISOLATE_MICROSERVICE = "isolate_microservice"
    REVOKE_IAM_ROLE = "revoke_iam_role"
    RESTART_POD = "restart_pod"
    QUERY_LOGS = "query_logs"
    PASS = "pass"  # Do nothing / monitor

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


# OBSERVATION SPACE (What the AI Agent Sees)

class Alert(BaseModel):
    alert_id: str = Field(..., description="Unique ID for the security alert")
    severity: Severity
    description: str = Field(..., description="Details of the anomalous activity")
    source_ip: Optional[str] = None
    target_service: Optional[str] = None

class Observation(BaseModel):
    active_alerts: List[Alert] = Field(default_factory=list, description="Current active security alerts from the SIEM")
    blocked_ips: List[str] = Field(default_factory=list, description="List of currently blocked IP addresses at the edge firewall")
    isolated_services: List[str] = Field(default_factory=list, description="Microservices currently quarantined from the internal network")
    revoked_roles: List[str] = Field(default_factory=list, description="IAM roles that have been actively revoked")
    service_health: Dict[str, ServiceStatus] = Field(default_factory=dict, description="Current health status of all cluster microservices")


# ACTION SPACE (What the AI Agent Can Do)

class Action(BaseModel):
    action_type: ActionType = Field(..., description="The specific remediation action to execute")
    target: str = Field(..., description="The target IP, service name, or IAM role to apply the action to")
    justification: str = Field(..., description="A mandatory brief explanation for the audit log justifying this action")

# REWARD SPACE (How the AI is Scored)

class Reward(BaseModel):
    value: float = Field(..., description="The numeric reward value for the current step")
    message: str = Field(..., description="Explanation of the reward for partial progress tracking and debugging")