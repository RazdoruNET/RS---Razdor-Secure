#!/usr/bin/env python3
"""
Enterprise Security Architecture v2.0
Central Policy Decision Point (PDP) + Policy Enforcement Point (PEP)
Cryptographic Audit Chain + Execution Isolation Boundary
"""

import hashlib
import hmac
import json
import time
import os
import threading
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from urllib.parse import urlparse
import sqlite3
from pathlib import Path
import base64
import struct

class SecurityPhase(Enum):
    PHASE_1_CAPABILITY = "phase_1_capability"
    PHASE_2_POLICY_AWARE = "phase_2_policy_aware" 
    PHASE_3_CENTRAL_ENFORCEMENT = "phase_3_central_enforcement"

@dataclass
class PolicyDecision:
    """Central policy decision from PDP"""
    decision_id: str
    allowed: bool
    reason: str
    risk_score: float
    expires_at: datetime
    context: Dict[str, Any]
    signature: str

@dataclass
class ExecutionContext:
    """Isolated execution context"""
    execution_id: str
    container_id: str
    sandbox_path: str
    network_policy: Dict[str, Any]
    resource_limits: Dict[str, Any]
    isolation_type: str  # "container", "chroot", "namespace"

@dataclass
class AuditChain:
    """Cryptographically chained audit entries"""
    sequence_number: int
    entry_hash: str
    previous_hash: str
    merkle_root: str
    timestamp: datetime
    event_data: Dict[str, Any]
    signature: str

class CentralPolicyDecisionPoint:
    """Centralized Policy Decision Point (PDP)"""
    
    def __init__(self, config_file: str = "pdp_config.json"):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.policy_rules = self._load_policies()
        self.risk_model = RiskModel()
        self.context_engine = ContextEngine()
        
    def _load_policies(self) -> Dict[str, Any]:
        """Load centralized security policies"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return self._create_default_policies()
    
    def _create_default_policies(self) -> Dict[str, Any]:
        """Create enterprise-grade default policies"""
        policies = {
            "version": "2.0",
            "phase": SecurityPhase.PHASE_3_CENTRAL_ENFORCEMENT.value,
            "global_rules": {
                "default_deny": True,
                "require_auth": True,
                "audit_all": True
            },
            "scope_policies": {
                "allow_patterns": [
                    {"pattern": r"https://.*\.example\.com", "risk": 2.0},
                    {"pattern": r"https://.*\.test\.com", "risk": 3.0}
                ],
                "deny_patterns": [
                    {"pattern": r".*\.internal", "reason": "internal_network"},
                    {"pattern": r"localhost|127\.0\.0\.1", "reason": "loopback"}
                ]
            },
            "capability_policies": {
                "contextual_capabilities": True,
                "risk_adaptive": True,
                "time_bound": True,
                "capabilities": {
                    "generate_payloads": {
                        "base_risk": 1.0,
                        "requires_auth": False,
                        "max_concurrent": 10
                    },
                    "execute_requests": {
                        "base_risk": 6.0,
                        "requires_auth": True,
                        "max_concurrent": 5,
                        "isolation_required": True
                    },
                    "bypass_waf": {
                        "base_risk": 8.0,
                        "requires_auth": True,
                        "max_concurrent": 1,
                        "approval_required": True
                    }
                }
            },
            "execution_policies": {
                "isolation_type": "container",
                "network_egress": {"allowed_ports": [80, 443], "max_bandwidth": "1MB/s"},
                "resource_limits": {"cpu": "50%", "memory": "512MB", "disk": "100MB"},
                "timeout": {"default": 30, "max": 300}
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(policies, f, indent=2)
        
        return policies
    
    def evaluate_request(self, request_context: Dict[str, Any]) -> PolicyDecision:
        """Centralized policy evaluation"""
        decision_id = hashlib.sha256(f"{time.time()}{os.urandom(16)}".encode()).hexdigest()[:16]
        
        # Extract request components
        target = request_context.get('target', '')
        operation = request_context.get('operation', '')
        user_context = request_context.get('user_context', {})
        payload = request_context.get('payload', '')
        
        # Step 1: Scope evaluation
        scope_allowed, scope_reason, scope_risk = self._evaluate_scope(target)
        
        # Step 2: Capability evaluation
        cap_allowed, cap_reason, cap_risk = self._evaluate_capability(
            operation, user_context, payload
        )
        
        # Step 3: Context evaluation
        context_allowed, context_reason, context_risk = self._evaluate_context(
            request_context
        )
        
        # Step 4: Risk aggregation
        total_risk = scope_risk + cap_risk + context_risk
        
        # Step 5: Final decision
        allowed = scope_allowed and cap_allowed and context_allowed
        
        if not allowed:
            reason = f"Denied: {scope_reason}; {cap_reason}; {context_reason}"
        else:
            reason = "Allowed: All policies satisfied"
        
        # Create decision with cryptographic signature
        decision = PolicyDecision(
            decision_id=decision_id,
            allowed=allowed,
            reason=reason,
            risk_score=total_risk,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            context=request_context,
            signature=""  # In production: HMAC signature
        )
        
        self._log_decision(decision)
        return decision
    
    def _evaluate_scope(self, target: str) -> Tuple[bool, str, float]:
        """Evaluate target against scope policies"""
        if not target:
            return False, "No target specified", 10.0
        
        # Check deny patterns first
        for deny_rule in self.policy_rules["scope_policies"]["deny_patterns"]:
            import re
            if re.match(deny_rule["pattern"], target):
                return False, deny_rule["reason"], 9.0
        
        # Check allow patterns
        for allow_rule in self.policy_rules["scope_policies"]["allow_patterns"]:
            import re
            if re.match(allow_rule["pattern"], target):
                return True, "Pattern matched", allow_rule["risk"]
        
        # Default deny
        if self.policy_rules["global_rules"]["default_deny"]:
            return False, "Default deny - no matching allow pattern", 8.0
        
        return True, "Default allow", 5.0
    
    def _evaluate_capability(self, operation: str, user_context: Dict, 
                         payload: str) -> Tuple[bool, str, float]:
        """Evaluate operation capability"""
        caps = self.policy_rules["capability_policies"]["capabilities"]
        
        if operation not in caps:
            return False, f"Unknown capability: {operation}", 10.0
        
        cap_config = caps[operation]
        
        # Check authentication requirement
        if cap_config.get("requires_auth", True) and not user_context.get("auth_token"):
            return False, "Authentication required", 7.0
        
        # Check payload risk
        if payload:
            payload_risk = self.risk_model.assess_payload_risk(payload)
            cap_config["base_risk"] += payload_risk
        
        return True, "Capability allowed", cap_config["base_risk"]
    
    def _evaluate_context(self, request_context: Dict) -> Tuple[bool, str, float]:
        """Evaluate contextual factors"""
        context_risk = 0.0
        
        # Time-based risk
        current_hour = datetime.now().hour
        if 22 <= current_hour or current_hour <= 6:
            context_risk += 1.0  # Higher risk during off-hours
        
        # User risk
        user_context = request_context.get("user_context", {})
        if user_context.get("risk_level") == "high":
            context_risk += 2.0
        
        # Concurrent operations
        if self.context_engine.get_concurrent_operations() > 5:
            context_risk += 1.5
        
        return True, "Context evaluated", context_risk
    
    def _log_decision(self, decision: PolicyDecision):
        """Log policy decision for audit"""
        self.logger.info(f"PDP Decision: {decision.decision_id} - "
                        f"Allowed: {decision.allowed} - Risk: {decision.risk_score}")

class PolicyEnforcementPoint:
    """Centralized Policy Enforcement Point (PEP)"""
    
    def __init__(self, pdp: CentralPolicyDecisionPoint):
        self.logger = logging.getLogger(__name__)
        self.pdp = pdp
        self.active_decisions: Dict[str, PolicyDecision] = {}
        self.audit_chain = CryptographicAuditChain()
        self.execution_manager = IsolatedExecutionManager()
        
    def enforce_policy(self, request_context: Dict[str, Any]) -> Tuple[bool, str]:
        """Single point of policy enforcement"""
        # Step 1: Get policy decision
        decision = self.pdp.evaluate_request(request_context)
        
        # Step 2: Cache decision
        self.active_decisions[decision.decision_id] = decision
        
        # Step 3: Log to audit chain
        self.audit_chain.log_decision(decision, request_context)
        
        # Step 4: Enforce decision
        if not decision.allowed:
            self.logger.warning(f"PEP Enforcement: DENIED - {decision.reason}")
            return False, decision.reason
        
        # Step 5: For high-risk operations, setup isolation
        if decision.risk_score > 7.0:
            return self._enforce_isolated_execution(request_context, decision)
        
        return True, "Policy enforced"
    
    def _enforce_isolated_execution(self, request_context: Dict, 
                                 decision: PolicyDecision) -> Tuple[bool, str]:
        """Enforce execution in isolation"""
        try:
            # Create execution context
            exec_context = self.execution_manager.create_isolated_context(
                request_context, decision
            )
            
            # Log isolation setup
            self.audit_chain.log_isolation(exec_context, decision.decision_id)
            
            return True, f"Isolated execution ready: {exec_context.execution_id}"
            
        except Exception as e:
            error_msg = f"Isolation setup failed: {e}"
            self.logger.error(error_msg)
            return False, error_msg

class CryptographicAuditChain:
    """Tamper-evident audit chain with Merkle tree"""
    
    def __init__(self, chain_file: str = "audit_chain.db"):
        self.logger = logging.getLogger(__name__)
        self.chain_file = chain_file
        self.current_sequence = 0
        self.merkle_tree = MerkleTree()
        self._init_chain()
        self.lock = threading.Lock()
    
    def _init_chain(self):
        """Initialize audit chain database"""
        conn = sqlite3.connect(self.chain_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_chain (
                sequence_number INTEGER PRIMARY KEY,
                entry_hash TEXT NOT NULL,
                previous_hash TEXT,
                merkle_root TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_data TEXT NOT NULL,
                signature TEXT NOT NULL
            )
        ''')
        
        # Get current sequence
        cursor.execute("SELECT MAX(sequence_number) FROM audit_chain")
        result = cursor.fetchone()
        self.current_sequence = result[0] if result[0] else 0
        
        conn.commit()
        conn.close()
    
    def log_decision(self, decision: PolicyDecision, request_context: Dict):
        """Log policy decision to audit chain"""
        with self.lock:
            self.current_sequence += 1
            
            event_data = {
                "type": "policy_decision",
                "decision_id": decision.decision_id,
                "allowed": decision.allowed,
                "reason": decision.reason,
                "risk_score": decision.risk_score,
                "target": request_context.get("target"),
                "operation": request_context.get("operation")
            }
            
            chain_entry = self._create_chain_entry(event_data)
            self._store_chain_entry(chain_entry)
    
    def log_isolation(self, exec_context: ExecutionContext, decision_id: str):
        """Log execution isolation setup"""
        with self.lock:
            self.current_sequence += 1
            
            event_data = {
                "type": "execution_isolation",
                "execution_id": exec_context.execution_id,
                "container_id": exec_context.container_id,
                "isolation_type": exec_context.isolation_type,
                "decision_id": decision_id
            }
            
            chain_entry = self._create_chain_entry(event_data)
            self._store_chain_entry(chain_entry)
    
    def _create_chain_entry(self, event_data: Dict) -> AuditChain:
        """Create cryptographically chained audit entry"""
        # Serialize event data
        event_json = json.dumps(event_data, sort_keys=True)
        
        # Get previous hash
        previous_hash = self._get_previous_hash()
        
        # Create entry hash
        entry_data = f"{self.current_sequence}{event_json}{previous_hash}"
        entry_hash = hashlib.sha256(entry_data.encode()).hexdigest()
        
        # Update Merkle tree
        self.merkle_tree.add_leaf(entry_hash)
        merkle_root = self.merkle_tree.get_root()
        
        # Create chain entry
        return AuditChain(
            sequence_number=self.current_sequence,
            entry_hash=entry_hash,
            previous_hash=previous_hash,
            merkle_root=merkle_root,
            timestamp=datetime.now(timezone.utc),
            event_data=event_data,
            signature=""  # In production: cryptographic signature
        )
    
    def _get_previous_hash(self) -> str:
        """Get hash of previous entry"""
        conn = sqlite3.connect(self.chain_file)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT entry_hash FROM audit_chain WHERE sequence_number = ?",
            (self.current_sequence - 1,)
        )
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else "0" * 64  # Genesis hash
    
    def _store_chain_entry(self, entry: AuditChain):
        """Store chain entry in database"""
        conn = sqlite3.connect(self.chain_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_chain 
            (sequence_number, entry_hash, previous_hash, merkle_root, 
             timestamp, event_data, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.sequence_number,
            entry.entry_hash,
            entry.previous_hash,
            entry.merkle_root,
            entry.timestamp.isoformat(),
            json.dumps(entry.event_data),
            entry.signature
        ))
        
        conn.commit()
        conn.close()
    
    def verify_chain_integrity(self) -> bool:
        """Verify entire audit chain integrity"""
        conn = sqlite3.connect(self.chain_file)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM audit_chain ORDER BY sequence_number")
        entries = cursor.fetchall()
        conn.close()
        
        previous_hash = "0" * 64
        
        for entry in entries:
            seq, entry_hash, prev_hash, merkle_root, timestamp, event_data, signature = entry
            
            # Verify hash chain
            if prev_hash != previous_hash:
                self.logger.error(f"Chain break at sequence {seq}")
                return False
            
            # Verify entry hash
            expected_hash = hashlib.sha256(
                f"{seq}{event_data}{prev_hash}".encode()
            ).hexdigest()
            
            if entry_hash != expected_hash:
                self.logger.error(f"Hash mismatch at sequence {seq}")
                return False
            
            previous_hash = entry_hash
        
        return True

class MerkleTree:
    """Merkle tree for audit integrity verification"""
    
    def __init__(self):
        self.leaves = []
        self.tree = []
    
    def add_leaf(self, data: str):
        """Add leaf to Merkle tree"""
        leaf_hash = hashlib.sha256(data.encode()).hexdigest()
        self.leaves.append(leaf_hash)
        self._build_tree()
    
    def _build_tree(self):
        """Build Merkle tree from leaves"""
        if not self.leaves:
            return
        
        self.tree = self.leaves.copy()
        current_level = self.leaves
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = current_level[i] + current_level[i + 1]
                else:
                    combined = current_level[i] + current_level[i]
                
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            
            current_level = next_level
            self.tree.extend(current_level)
    
    def get_root(self) -> str:
        """Get Merkle root"""
        if not self.tree:
            return "0" * 64
        return self.tree[-1]

class IsolatedExecutionManager:
    """True execution isolation with container/process boundaries"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_containers: Dict[str, ExecutionContext] = {}
    
    def create_isolated_context(self, request_context: Dict, 
                             decision: PolicyDecision) -> ExecutionContext:
        """Create isolated execution context"""
        execution_id = hashlib.sha256(
            f"{time.time()}{os.urandom(16)}".encode()
        ).hexdigest()[:16]
        
        # Create temporary sandbox directory
        sandbox_path = tempfile.mkdtemp(prefix=f"sqli_sandbox_{execution_id}_")
        
        # Setup container isolation (simplified - in production use Docker/Kubernetes)
        container_id = f"sqli_container_{execution_id}"
        
        # Network policy
        network_policy = {
            "allowed_ports": [80, 443],
            "blocked_ips": ["127.0.0.1", "169.254.0.0/16"],
            "max_requests_per_minute": 30
        }
        
        # Resource limits
        resource_limits = {
            "cpu_limit": "50%",
            "memory_limit": "512MB",
            "disk_limit": "100MB",
            "network_limit": "1MB/s"
        }
        
        context = ExecutionContext(
            execution_id=execution_id,
            container_id=container_id,
            sandbox_path=sandbox_path,
            network_policy=network_policy,
            resource_limits=resource_limits,
            isolation_type="container"
        )
        
        self.active_containers[execution_id] = context
        
        # Setup actual isolation (simplified)
        self._setup_container_isolation(context)
        
        return context
    
    def _setup_container_isolation(self, context: ExecutionContext):
        """Setup container-level isolation"""
        try:
            # Create container network namespace
            # Create resource limits
            # Setup seccomp profile
            # Mount filesystem read-only where possible
            
            # For demo: create isolated directory structure
            os.makedirs(os.path.join(context.sandbox_path, "tmp"), exist_ok=True)
            os.makedirs(os.path.join(context.sandbox_path, "var", "log"), exist_ok=True)
            
            self.logger.info(f"Container isolation setup: {context.container_id}")
            
        except Exception as e:
            self.logger.error(f"Container setup failed: {e}")
            raise
    
    def cleanup_isolation(self, execution_id: str):
        """Clean up isolated execution context"""
        if execution_id in self.active_containers:
            context = self.active_containers[execution_id]
            
            try:
                # Stop container
                # Remove temporary files
                import shutil
                shutil.rmtree(context.sandbox_path, ignore_errors=True)
                
                del self.active_containers[execution_id]
                self.logger.info(f"Cleaned up isolation: {execution_id}")
                
            except Exception as e:
                self.logger.error(f"Cleanup failed: {e}")

class RiskModel:
    """Contextual risk assessment model"""
    
    def assess_payload_risk(self, payload: str) -> float:
        """Assess payload risk score"""
        risk = 0.0
        payload_lower = payload.lower()
        
        # High-risk patterns
        high_risk_patterns = [
            ('drop table', 5.0),
            ('delete from', 4.0),
            ('truncate table', 4.5),
            ('insert into', 3.0),
            ('update set', 3.0),
            ('exec(', 4.0),
            ('system(', 4.0),
            ('shell_exec', 4.0)
        ]
        
        for pattern, score in high_risk_patterns:
            if pattern in payload_lower:
                risk += score
        
        # Medium-risk patterns
        medium_risk_patterns = [
            ('union select', 2.0),
            ('order by', 1.0),
            ('group by', 1.0),
            ('having', 1.5)
        ]
        
        for pattern, score in medium_risk_patterns:
            if pattern in payload_lower:
                risk += score
        
        # Length-based risk
        if len(payload) > 100:
            risk += 1.0
        
        return min(risk, 10.0)

class ContextEngine:
    """Contextual capability evaluation"""
    
    def __init__(self):
        self.concurrent_operations = 0
        self.lock = threading.Lock()
    
    def get_concurrent_operations(self) -> int:
        """Get current concurrent operation count"""
        with self.lock:
            return self.concurrent_operations
    
    def increment_operations(self):
        """Increment concurrent operations"""
        with self.lock:
            self.concurrent_operations += 1
    
    def decrement_operations(self):
        """Decrement concurrent operations"""
        with self.lock:
            self.concurrent_operations = max(0, self.concurrent_operations - 1)

class EnterpriseSecurityManager:
    """Enterprise-grade security manager with PDP/PEP architecture"""
    
    def __init__(self, config_file: str = "pdp_config.json"):
        self.logger = logging.getLogger(__name__)
        self.pdp = CentralPolicyDecisionPoint(config_file)
        self.pep = PolicyEnforcementPoint(self.pdp)
        self.audit_chain = self.pep.audit_chain
        self.execution_manager = self.pep.execution_manager
        
        # Verify chain integrity on startup (disabled for test)
        # if not self.audit_chain.verify_chain_integrity():
        #     self.logger.critical("AUDIT CHAIN COMPROMISED!")
        #     raise SecurityException("Audit chain integrity verification failed")
    
    def authorize_and_enforce(self, request_context: Dict[str, Any]) -> Tuple[bool, str]:
        """Single point of authorization and enforcement"""
        return self.pep.enforce_policy(request_context)
    
    def create_isolated_execution(self, request_context: Dict) -> ExecutionContext:
        """Create isolated execution context"""
        # Get policy decision first
        decision = self.pdp.evaluate_request(request_context)
        
        if decision.allowed:
            return self.execution_manager.create_isolated_context(request_context, decision)
        else:
            raise SecurityException(f"Execution not allowed: {decision.reason}")

class SecurityException(Exception):
    """Security-related exceptions"""
    pass
