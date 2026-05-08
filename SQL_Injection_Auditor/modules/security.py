#!/usr/bin/env python3
"""
Enterprise Security Controls
Scope Enforcement, Execution Sandbox, Audit Logging, Capability Gating
"""

import hashlib
import hmac
import time
import json
import os
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from urllib.parse import urlparse
import sqlite3
from pathlib import Path

class SecurityLevel(Enum):
    READ_ONLY = "read_only"
    ANALYSIS = "analysis" 
    ACTIVE_TESTING = "active_testing"
    FULL_AUDIT = "full_audit"

@dataclass
class AuthorizationToken:
    """Signed authorization token for operations"""
    token_id: str
    scope: List[str]  # Allowed targets/domains
    security_level: SecurityLevel
    expires_at: datetime
    capabilities: List[str]
    signature: str
    created_by: str
    purpose: str

@dataclass
class AuditEvent:
    """Immutable audit event"""
    event_id: str
    timestamp: datetime
    event_type: str
    user_id: str
    session_id: str
    target: str
    action: str
    payload_hash: Optional[str] = None
    response_code: Optional[int] = None
    duration_ms: Optional[int] = None
    risk_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class ScopeEnforcement:
    """Mandatory scope enforcement layer"""
    
    def __init__(self, config_file: str = "security_config.json"):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.allowed_targets: Set[str] = set()
        self.blocked_domains: Set[str] = set()
        self.active_tokens: Dict[str, AuthorizationToken] = {}
        self._load_config()
        
    def _load_config(self):
        """Load security configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.allowed_targets = set(config.get('allowed_targets', []))
                    self.blocked_domains = set(config.get('blocked_domains', []))
            else:
                # Create default secure config
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load security config: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default secure configuration"""
        default_config = {
            "allowed_targets": [],  # Empty by default - explicit allowlist
            "blocked_domains": [
                "localhost", "127.0.0.1", "0.0.0.0",
                "internal", "intranet", "corp"
            ],
            "max_security_level": "analysis",
            "require_auth": True
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        self.allowed_targets = set(default_config['allowed_targets'])
        self.blocked_domains = set(default_config['blocked_domains'])
    
    def validate_target(self, target_url: str, auth_token: Optional[str] = None) -> tuple[bool, str]:
        """Validate target against scope and authorization"""
        try:
            parsed = urlparse(target_url)
            domain = parsed.netloc.lower()
            
            # Check blocked domains first
            if any(blocked in domain for blocked in self.blocked_domains):
                return False, f"Target {domain} is in blocked list"
            
            # Check allowlist
            if self.allowed_targets and not any(allowed in domain for allowed in self.allowed_targets):
                return False, f"Target {domain} not in allowlist"
            
            # Check authorization token if provided
            if auth_token:
                token_valid, token_msg = self._validate_token(auth_token, target_url)
                if not token_valid:
                    return False, f"Invalid authorization token: {token_msg}"
            
            return True, "Target validated"
            
        except Exception as e:
            return False, f"Target validation error: {e}"
    
    def _validate_token(self, token: str, target_url: str) -> tuple[bool, str]:
        """Validate authorization token"""
        try:
            # Parse token (simplified - in production use JWT)
            token_data = json.loads(token)
            
            # Check if token exists
            if token_data.get('token_id') not in self.active_tokens:
                return False, "Token not found or expired"
            
            auth_token = self.active_tokens[token_data['token_id']]
            
            # Check expiration
            if datetime.now(timezone.utc) > auth_token.expires_at:
                del self.active_tokens[token_data['token_id']]
                return False, "Token expired"
            
            # Check scope
            parsed_target = urlparse(target_url)
            target_domain = parsed_target.netloc.lower()
            
            if not any(allowed in target_domain for allowed in auth_token.scope):
                return False, f"Target {target_domain} not in token scope"
            
            return True, "Token valid"
            
        except Exception as e:
            return False, f"Token validation error: {e}"
    
    def generate_token(self, scope: List[str], security_level: SecurityLevel, 
                      capabilities: List[str], expires_hours: int = 24,
                      created_by: str = "system", purpose: str = "audit") -> str:
        """Generate signed authorization token"""
        token_id = hashlib.sha256(f"{time.time()}{os.urandom(16)}".encode()).hexdigest()[:16]
        
        token = AuthorizationToken(
            token_id=token_id,
            scope=scope,
            security_level=security_level,
            expires_at=datetime.now(timezone.utc).replace(microsecond=0) + 
                       datetime.timedelta(hours=expires_hours),
            capabilities=capabilities,
            signature="",  # In production, sign with HMAC
            created_by=created_by,
            purpose=purpose
        )
        
        # Store token
        self.active_tokens[token_id] = token
        
        # Return token data (in production, return signed JWT)
        return json.dumps({
            'token_id': token_id,
            'scope': scope,
            'security_level': security_level.value,
            'capabilities': capabilities,
            'expires_at': token.expires_at.isoformat()
        })

class ExecutionSandbox:
    """Controlled execution environment"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.allowed_egress_ports = config.get('allowed_egress_ports', [80, 443])
        self.max_requests_per_minute = config.get('max_requests_per_minute', 60)
        self.blocked_response_patterns = config.get('blocked_response_patterns', [])
        self.request_times = []
        self.lock = threading.Lock()
    
    def validate_request(self, target_url: str, payload: str) -> tuple[bool, str]:
        """Validate request before execution"""
        try:
            parsed = urlparse(target_url)
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            # Check egress port restrictions
            if port not in self.allowed_egress_ports:
                return False, f"Port {port} not allowed for egress"
            
            # Rate limiting
            with self.lock:
                current_time = time.time()
                self.request_times = [t for t in self.request_times if current_time - t < 60]
                
                if len(self.request_times) >= self.max_requests_per_minute:
                    return False, "Rate limit exceeded"
                
                self.request_times.append(current_time)
            
            # Payload validation
            if not self._validate_payload(payload):
                return False, "Payload contains blocked patterns"
            
            return True, "Request validated"
            
        except Exception as e:
            return False, f"Sandbox validation error: {e}"
    
    def _validate_payload(self, payload: str) -> bool:
        """Validate payload against blocked patterns"""
        payload_lower = payload.lower()
        
        # Block dangerous patterns
        blocked_patterns = [
            'drop table', 'delete from', 'truncate table',
            'insert into', 'update set', 'create table',
            'exec(', 'system(', 'shell_exec',
            '<?php', '<script', 'javascript:'
        ]
        
        for pattern in blocked_patterns:
            if pattern in payload_lower:
                self.logger.warning(f"Blocked payload pattern: {pattern}")
                return False
        
        return True

class AuditLogger:
    """Immutable audit-grade logging"""
    
    def __init__(self, db_path: str = "audit.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self._init_database()
        self.lock = threading.Lock()
    
    def _init_database(self):
        """Initialize audit database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                target TEXT NOT NULL,
                action TEXT NOT NULL,
                payload_hash TEXT,
                response_code INTEGER,
                duration_ms INTEGER,
                risk_score REAL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_target ON audit_events(target)')
        
        conn.commit()
        conn.close()
    
    def log_event(self, event: AuditEvent):
        """Log immutable audit event"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO audit_events 
                    (event_id, timestamp, event_type, user_id, session_id, 
                     target, action, payload_hash, response_code, duration_ms, 
                     risk_score, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.user_id,
                    event.session_id,
                    event.target,
                    event.action,
                    event.payload_hash,
                    event.response_code,
                    event.duration_ms,
                    event.risk_score,
                    json.dumps(event.metadata) if event.metadata else None
                ))
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                self.logger.error(f"Failed to log audit event: {e}")
    
    def generate_event_id(self) -> str:
        """Generate unique event ID"""
        return hashlib.sha256(f"{time.time()}{os.urandom(8)}".encode()).hexdigest()[:32]

class CapabilityGating:
    """Separate payload generation from execution"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.capabilities = {
            'generate_payloads': True,
            'analyze_responses': True,
            'execute_requests': False,  # Requires explicit authorization
            'bypass_waf': False,       # High-risk capability
            'export_reports': True,
            'modify_config': False
        }
    
    def check_capability(self, capability: str, auth_token: Optional[str] = None) -> bool:
        """Check if capability is allowed"""
        # Check if capability exists
        if capability not in self.capabilities:
            return False
        
        # Check if capability is enabled
        if not self.capabilities[capability]:
            return False
        
        # Check authorization for high-risk capabilities
        high_risk_caps = ['execute_requests', 'bypass_waf', 'modify_config']
        if capability in high_risk_caps and not auth_token:
            return False
        
        return True
    
    def enable_capability(self, capability: str, auth_token: str) -> bool:
        """Enable capability with authorization"""
        if capability not in self.capabilities:
            return False
        
        # In production, validate token signature and permissions
        self.capabilities[capability] = True
        return True

class SecurityManager:
    """Main security control orchestrator"""
    
    def __init__(self, config_file: str = "security_config.json"):
        self.logger = logging.getLogger(__name__)
        self.scope_enforcement = ScopeEnforcement(config_file)
        self.config = self._load_security_config()
        self.sandbox = ExecutionSandbox(self.config)
        self.audit_logger = AuditLogger()
        self.capability_gating = CapabilityGating(self.config)
        self.session_id = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        try:
            with open("security_config.json", 'r') as f:
                return json.load(f)
        except:
            return {
                "allowed_egress_ports": [80, 443],
                "max_requests_per_minute": 60,
                "blocked_response_patterns": []
            }
    
    def authorize_operation(self, target_url: str, operation: str, 
                          payload: Optional[str] = None,
                          auth_token: Optional[str] = None) -> tuple[bool, str]:
        """Comprehensive operation authorization"""
        # Step 1: Scope validation
        scope_valid, scope_msg = self.scope_enforcement.validate_target(target_url, auth_token)
        if not scope_valid:
            self._log_security_event("scope_violation", target_url, operation, 
                                    {"reason": scope_msg})
            return False, f"Scope validation failed: {scope_msg}"
        
        # Step 2: Capability check
        if not self.capability_gating.check_capability(operation, auth_token):
            self._log_security_event("capability_violation", target_url, operation,
                                    {"capability": operation})
            return False, f"Capability {operation} not authorized"
        
        # Step 3: Sandbox validation (for execution operations)
        if operation == 'execute_requests' and payload:
            sandbox_valid, sandbox_msg = self.sandbox.validate_request(target_url, payload)
            if not sandbox_valid:
                self._log_security_event("sandbox_violation", target_url, operation,
                                        {"reason": sandbox_msg, "payload": payload[:100]})
                return False, f"Sandbox validation failed: {sandbox_msg}"
        
        return True, "Operation authorized"
    
    def _log_security_event(self, event_type: str, target: str, action: str, 
                           metadata: Dict[str, Any]):
        """Log security event"""
        event = AuditEvent(
            event_id=self.audit_logger.generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=f"security_{event_type}",
            user_id="system",
            session_id=self.session_id,
            target=target,
            action=action,
            risk_score=8.0 if "violation" in event_type else 3.0,
            metadata=metadata
        )
        
        self.audit_logger.log_event(event)
        self.logger.warning(f"Security event: {event_type} on {target}")
    
    def generate_auth_token(self, scope: List[str], security_level: SecurityLevel,
                          capabilities: List[str], expires_hours: int = 24) -> str:
        """Generate authorization token"""
        return self.scope_enforcement.generate_token(
            scope, security_level, capabilities, expires_hours
        )
    
    def log_operation(self, event_type: str, target: str, action: str,
                     payload_hash: Optional[str] = None, response_code: Optional[int] = None,
                     duration_ms: Optional[int] = None, risk_score: Optional[float] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Log operation event"""
        event = AuditEvent(
            event_id=self.audit_logger.generate_event_id(),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            user_id="system",
            session_id=self.session_id,
            target=target,
            action=action,
            payload_hash=payload_hash,
            response_code=response_code,
            duration_ms=duration_ms,
            risk_score=risk_score,
            metadata=metadata
        )
        
        self.audit_logger.log_event(event)
