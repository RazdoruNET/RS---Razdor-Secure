#!/usr/bin/env python3
"""
Enterprise Security Integration
Bridge between legacy modules and new PDP/PEP architecture
"""

import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
import logging
from urllib.parse import urlparse

from modules.enterprise_security import (
    EnterpriseSecurityManager, SecurityException, 
    ExecutionContext, PolicyDecision
)
from modules.analysis_engine import Vulnerability

class EnterpriseSecurityBridge:
    """Bridge between legacy security and new enterprise architecture"""
    
    def __init__(self, use_enterprise: bool = True):
        self.logger = logging.getLogger(__name__)
        self.use_enterprise = use_enterprise
        
        if use_enterprise:
            self.enterprise_manager = EnterpriseSecurityManager()
            self.logger.info("Enterprise Security Mode: ENABLED")
        else:
            self.enterprise_manager = None
            self.logger.info("Enterprise Security Mode: DISABLED - Using legacy")
    
    def authorize_execution(self, target_url: str, operation: str,
                         payload: Optional[str] = None,
                         user_context: Optional[Dict] = None) -> Tuple[bool, str, Optional[PolicyDecision]]:
        """Unified authorization interface"""
        
        if not self.use_enterprise:
            # Fallback to legacy security
            return self._legacy_authorize(target_url, operation, payload, user_context)
        
        # Enterprise PDP/PEP authorization
        request_context = {
            "target": target_url,
            "operation": operation,
            "payload": payload,
            "user_context": user_context or {},
            "timestamp": time.time(),
            "request_id": hashlib.sha256(f"{time.time()}{target_url}".encode()).hexdigest()[:16]
        }
        
        try:
            allowed, message = self.enterprise_manager.authorize_and_enforce(request_context)
            
            # Get policy decision for logging
            decision = self.enterprise_manager.pdp.evaluate_request(request_context)
            
            return allowed, message, decision
            
        except SecurityException as e:
            self.logger.error(f"Enterprise security exception: {e}")
            return False, f"Security exception: {e}", None
        except Exception as e:
            self.logger.error(f"Enterprise authorization error: {e}")
            return False, f"Authorization error: {e}", None
    
    def _legacy_authorize(self, target_url: str, operation: str,
                         payload: Optional[str] = None,
                         user_context: Optional[Dict] = None) -> Tuple[bool, str, None]:
        """Legacy authorization fallback"""
        # Simplified legacy logic
        blocked_domains = ["localhost", "127.0.0.1", "internal"]
        parsed = urlparse(target_url)
        
        if any(blocked in parsed.netloc.lower() for blocked in blocked_domains):
            return False, f"Target {parsed.netloc} in blocked list", None
        
        if operation == 'execute_requests' and not user_context:
            return False, "Authentication required for execution", None
        
        return True, "Legacy authorization passed", None
    
    def create_isolated_execution(self, target_url: str, operation: str,
                               payload: str, user_context: Dict) -> Optional[ExecutionContext]:
        """Create isolated execution context"""
        
        if not self.use_enterprise:
            return None
        
        request_context = {
            "target": target_url,
            "operation": operation,
            "payload": payload,
            "user_context": user_context,
            "requires_isolation": True
        }
        
        try:
            return self.enterprise_manager.create_isolated_execution(request_context)
        except Exception as e:
            self.logger.error(f"Isolation setup failed: {e}")
            return None
    
    def log_operation(self, event_type: str, target: str, action: str,
                     payload_hash: Optional[str] = None, 
                     response_code: Optional[int] = None,
                     duration_ms: Optional[int] = None, 
                     risk_score: Optional[float] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Unified operation logging"""
        
        if not self.use_enterprise:
            # Legacy logging
            self.logger.info(f"Legacy log: {event_type} on {target}")
            return
        
        # Enterprise audit chain logging
        try:
            # Create audit event for chain
            event_data = {
                "type": event_type,
                "target": target,
                "action": action,
                "payload_hash": payload_hash,
                "response_code": response_code,
                "duration_ms": duration_ms,
                "risk_score": risk_score,
                "metadata": metadata or {}
            }
            
            # Log to cryptographic audit chain
            self.enterprise_manager.audit_chain.log_decision(
                PolicyDecision(
                    decision_id=hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:16],
                    allowed=True,
                    reason="Operation logged",
                    risk_score=risk_score or 0.0,
                    expires_at=time.time() + 300,  # 5 minutes
                    context=event_data,
                    signature=""
                ),
                event_data
            )
            
        except Exception as e:
            self.logger.error(f"Enterprise logging failed: {e}")
    
    def cleanup_execution(self, execution_id: str):
        """Clean up isolated execution"""
        
        if not self.use_enterprise or not self.enterprise_manager:
            return
        
        try:
            self.enterprise_manager.execution_manager.cleanup_isolation(execution_id)
            self.logger.info(f"Cleaned up execution: {execution_id}")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")

class EnterpriseVulnerabilityScanner:
    """Vulnerability scanner with enterprise security integration"""
    
    def __init__(self, session, timeout: int = 30, 
                 security_bridge: Optional[EnterpriseSecurityBridge] = None):
        self.session = session
        self.timeout = timeout
        self.security_bridge = security_bridge or EnterpriseSecurityBridge()
        self.logger = logging.getLogger(__name__)
    
    def scan_parameter_enterprise(self, url: str, parameter: str, payloads: List[str],
                                injection_type: str, db_type: str,
                                user_context: Optional[Dict] = None) -> List[Vulnerability]:
        """Scan parameter with enterprise security enforcement"""
        
        vulnerabilities = []
        
        for payload in payloads:
            try:
                # Enterprise authorization for each payload
                allowed, auth_msg, decision = self.security_bridge.authorize_execution(
                    url, 'execute_requests', payload, user_context
                )
                
                if not allowed:
                    self.logger.warning(f"Payload blocked by enterprise security: {auth_msg}")
                    continue
                
                # Create isolated execution if high-risk
                exec_context = None
                if decision and decision.risk_score > 7.0:
                    exec_context = self.security_bridge.create_isolated_execution(
                        url, 'execute_requests', payload, user_context or {}
                    )
                
                # Execute payload with isolation
                vulnerability = self._execute_payload_isolated(
                    url, parameter, payload, injection_type, db_type, 
                    exec_context, decision
                )
                
                if vulnerability:
                    vulnerabilities.append(vulnerability)
                    self.logger.info(f"Vulnerability found: {vulnerability}")
                    break  # Stop after first vulnerability
                
                # Cleanup isolation
                if exec_context:
                    self.security_bridge.cleanup_execution(exec_context.execution_id)
                
            except Exception as e:
                self.logger.error(f"Enterprise scan error: {e}")
                continue
        
        return vulnerabilities
    
    def _execute_payload_isolated(self, url: str, parameter: str, payload: str,
                                 injection_type: str, db_type: str,
                                 exec_context: Optional[ExecutionContext],
                                 decision: Optional[PolicyDecision]) -> Optional[Vulnerability]:
        """Execute payload with enterprise isolation"""
        
        start_time = time.time()
        payload_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        
        try:
            # Log execution start
            self.security_bridge.log_operation(
                "payload_execution_enterprise", url, f"test_{parameter}",
                payload_hash=payload_hash,
                risk_score=decision.risk_score if decision else 0.0,
                metadata={
                    "injection_type": injection_type,
                    "db_type": db_type,
                    "isolation_type": exec_context.isolation_type if exec_context else "none",
                    "container_id": exec_context.container_id if exec_context else None
                }
            )
            
            # Execute request (with isolation if available)
            if exec_context:
                response = self._execute_in_container(url, parameter, payload, exec_context)
            else:
                response = self._execute_standard(url, parameter, payload)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log response
            self.security_bridge.log_operation(
                "payload_response_enterprise", url, f"response_{parameter}",
                payload_hash=payload_hash,
                response_code=response.status_code if response else None,
                duration_ms=duration_ms,
                metadata={
                    "isolation_used": exec_context is not None,
                    "decision_id": decision.decision_id if decision else None
                }
            )
            
            # Analyze response for vulnerability
            if response:
                return self._analyze_response_for_vulnerability(
                    response, url, parameter, payload, injection_type, db_type
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Isolated execution error: {e}")
            
            # Log error
            self.security_bridge.log_operation(
                "payload_error_enterprise", url, f"error_{parameter}",
                payload_hash=payload_hash,
                metadata={"error": str(e), "isolation_failed": True}
            )
            
            return None
    
    def _execute_in_container(self, url: str, parameter: str, payload: str,
                            exec_context: ExecutionContext):
        """Execute request in container isolation"""
        # In production, this would execute in actual container
        # For demo, simulate with additional checks
        
        # Check container constraints
        if exec_context.network_policy:
            parsed = urlparse(url)
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            if port not in exec_context.network_policy.get("allowed_ports", [80, 443]):
                raise SecurityException(f"Port {port} not allowed in isolation")
        
        # Execute with container constraints
        return self._execute_standard(url, parameter, payload)
    
    def _execute_standard(self, url: str, parameter: str, payload: str):
        """Standard request execution"""
        from urllib.parse import parse_qs
        
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        params[parameter] = [payload]
        
        query_string = '&'.join([f"{k}={v[0]}" for k, v in params.items()])
        test_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{query_string}"
        
        response = self.session.get(test_url, timeout=self.timeout)
        return response
    
    def _analyze_response_for_vulnerability(self, response, url: str, parameter: str,
                                         payload: str, injection_type: str, db_type: str) -> Optional[Vulnerability]:
        """Analyze response for vulnerability indicators"""
        
        response_text = response.text.lower()
        
        # Error-based detection
        if injection_type == "error_based":
            error_patterns = [
                "sql syntax", "mysql_fetch", "pg_query", 
                "microsoft ole db", "ora-"
            ]
            
            for pattern in error_patterns:
                if pattern in response_text:
                    return Vulnerability(
                        url=url,
                        parameter=parameter,
                        injection_type=injection_type,
                        database_type=db_type,
                        payload=payload,
                        evidence=f"SQL error pattern: {pattern}",
                        confidence=0.9,
                        response_time=response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                        status_code=response.status_code,
                        error_message=pattern
                    )
        
        # Boolean-based detection (simplified)
        elif injection_type == "boolean_based":
            if "1=1" in payload and len(response_text) > 100:
                return Vulnerability(
                    url=url,
                    parameter=parameter,
                    injection_type=injection_type,
                    database_type=db_type,
                    payload=payload,
                    evidence="Boolean-based response difference",
                    confidence=0.7,
                    response_time=response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    status_code=response.status_code
                )
        
        return None

class EnterpriseConfigurationManager:
    """Enterprise security configuration management"""
    
    def __init__(self, config_file: str = "enterprise_config.json"):
        self.config_file = config_file
        self.config = self._load_enterprise_config()
    
    def _load_enterprise_config(self) -> Dict[str, Any]:
        """Load enterprise security configuration"""
        try:
            import json
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return self._create_enterprise_config()
    
    def _create_enterprise_config(self) -> Dict[str, Any]:
        """Create enterprise security configuration"""
        config = {
            "enterprise_mode": True,
            "pdp_config": "pdp_config.json",
            "audit_chain_file": "audit_chain.db",
            "isolation_type": "container",
            "risk_thresholds": {
                "low": 3.0,
                "medium": 6.0,
                "high": 8.0
            },
            "policy_settings": {
                "default_deny": True,
                "require_auth": True,
                "audit_all": True,
                "contextual_capabilities": True,
                "risk_adaptive": True
            },
            "execution_settings": {
                "max_concurrent_operations": 5,
                "isolation_timeout": 300,
                "resource_limits": {
                    "cpu": "50%",
                    "memory": "512MB",
                    "network": "1MB/s"
                }
            }
        }
        
        import json
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def is_enterprise_enabled(self) -> bool:
        """Check if enterprise mode is enabled"""
        return self.config.get("enterprise_mode", False)
    
    def get_risk_threshold(self, level: str) -> float:
        """Get risk threshold for level"""
        return self.config.get("risk_thresholds", {}).get(level, 5.0)
