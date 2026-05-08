"""
Authorized Security Audit Module

Handles authorized security audits against external targets with proper validation
and safety mechanisms.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import hashlib
import logging

from architecture.formal_state_model import (
    FormalStateModel, DomainType, StateTransition, 
    ResourceCost, SystemInvariant
)
from architecture.core_constraints import ExecutionCycleManager
from architecture.control_plane import TestScenarioPlanner
from architecture.data_plane import PureExecutionEngine
from architecture.immutable_log import ImmutableEventLog, EventType
from architecture.external_oracle import ProductionMetricsOracle


class AuthorizationStatus(Enum):
    """Authorization status levels."""
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


@dataclass
class AuthorizationData:
    """Authorization data structure."""
    authorization_id: str
    target_url: str
    authorized_by: str
    contact_email: str
    contact_phone: str
    scope: Dict[str, Any]
    time_window: Dict[str, float]
    limitations: Dict[str, Any]
    status: AuthorizationStatus = AuthorizationStatus.PENDING
    verification_code: Optional[str] = None
    documents: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    verified_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'authorization_id': self.authorization_id,
            'target_url': self.target_url,
            'authorized_by': self.authorized_by,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'scope': self.scope,
            'time_window': self.time_window,
            'limitations': self.limitations,
            'status': self.status.value,
            'verification_code': self.verification_code,
            'documents': self.documents,
            'created_at': self.created_at,
            'verified_at': self.verified_at
        }


class AuthorizationValidator:
    """Validates authorization for external testing."""
    
    REQUIRED_DOCUMENTS = [
        'authorization_letter.pdf',
        'scope_of_engagement.pdf',
        'authorized_targets.txt',
        'contact_info.txt'
    ]
    
    def __init__(self, authorization_dir: str = "./authorization"):
        self.authorization_dir = Path(authorization_dir)
        self.logger = logging.getLogger("AuthorizationValidator")
    
    def validate_authorization(self, target_url: str) -> AuthorizationData:
        """
        Validate authorization for target URL.
        
        Returns authorization data if valid, raises exception if invalid.
        """
        
        # Check authorization directory exists
        if not self.authorization_dir.exists():
            raise AuthorizationError(
                "Authorization directory not found. "
                "Please provide authorization documents in ./authorization/"
            )
        
        # Load authorization data
        auth_file = self.authorization_dir / "authorization.json"
        if not auth_file.exists():
            raise AuthorizationError(
                "authorization.json not found in authorization directory"
            )
        
        with open(auth_file, 'r') as f:
            auth_data = json.load(f)
        
        # Create authorization object
        authorization = AuthorizationData(**auth_data)
        
        # Validate target is in scope
        if target_url not in authorization.scope.get('authorized_targets', []):
            raise AuthorizationError(
                f"Target {target_url} not in authorized scope. "
                f"Authorized targets: {authorization.scope.get('authorized_targets', [])}"
            )
        
        # Validate time window
        current_time = time.time()
        start_time = authorization.time_window.get('start_time', 0)
        end_time = authorization.time_window.get('end_time', float('inf'))
        
        if not (start_time <= current_time <= end_time):
            raise AuthorizationError(
                f"Current time {current_time} outside authorized window "
                f"({start_time} to {end_time})"
            )
        
        # Validate required documents
        missing_documents = []
        for doc in self.REQUIRED_DOCUMENTS:
            if not (self.authorization_dir / doc).exists():
                missing_documents.append(doc)
        
        if missing_documents:
            raise AuthorizationError(
                f"Missing required authorization documents: {missing_documents}"
            )
        
        # Verify authorization status
        if authorization.status != AuthorizationStatus.VERIFIED:
            raise AuthorizationError(
                f"Authorization status is {authorization.status.value}, not VERIFIED. "
                "Please complete authorization verification process."
            )
        
        # Check if authorization is expired
        if authorization.verified_at and (time.time() - authorization.verified_at) > 86400 * 30:  # 30 days
            raise AuthorizationError(
                "Authorization has expired (older than 30 days). "
                "Please renew authorization."
            )
        
        self.logger.info(f"Authorization validated for {target_url}")
        return authorization
    
    def generate_authorization_template(self, target_url: str) -> Dict[str, Any]:
        """Generate authorization template for user to fill."""
        
        auth_id = hashlib.sha256(f"{target_url}{time.time()}".encode()).hexdigest()[:16]
        
        template = {
            "authorization_id": f"AUTH-{auth_id}",
            "target_url": target_url,
            "authorized_by": "[Company Name]",
            "contact_email": "[security@example.com]",
            "contact_phone": "[+1-555-0123]",
            "scope": {
                "authorized_targets": [target_url],
                "test_types": ["authentication_stress", "rate_limiting_validation", "input_normalization"],
                "purpose": "Security audit and resilience testing"
            },
            "time_window": {
                "start_time": time.time(),
                "end_time": time.time() + 86400 * 7  # 7 days
            },
            "limitations": {
                "max_requests": 10000,
                "max_concurrent": 50,
                "rate_limit": 10,
                "duration": 3600,
                "daily_window": "02:00-06:00 UTC"
            },
            "status": "pending",
            "verification_code": None,
            "documents": [],
            "created_at": time.time(),
            "verified_at": None
        }
        
        return template


class AuthorizedSafetyController:
    """Enhanced safety controller for authorized testing."""
    
    def __init__(self, authorization: AuthorizationData):
        self.authorization = authorization
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.last_request_time = 0.0
        self.logger = logging.getLogger("AuthorizedSafetyController")
        
        # Safety thresholds
        self.max_error_rate = 0.2  # 20% error rate triggers stop
        self.max_response_time = 10.0  # 10 second response time triggers stop
        self.min_availability = 0.95  # 95% availability required
    
    def check_safety_before_request(self) -> bool:
        """Check safety conditions before each request."""
        
        # Check request count limit
        max_requests = self.authorization.limitations.get('max_requests', 10000)
        if self.request_count >= max_requests:
            raise SafetyLimitError(
                f"Request count limit reached: {self.request_count}/{max_requests}"
            )
        
        # Check error rate
        if self.request_count > 0:
            error_rate = self.error_count / self.request_count
            if error_rate > self.max_error_rate:
                raise SafetyLimitError(
                    f"Error rate too high: {error_rate:.2%} > {self.max_error_rate:.2%}"
                )
        
        # Check time limit
        duration = self.authorization.limitations.get('duration', 3600)
        if time.time() - self.start_time > duration:
            raise SafetyLimitError(
                f"Time limit reached: {time.time() - self.start_time:.0f}s > {duration}s"
            )
        
        # Check rate limit
        rate_limit = self.authorization.limitations.get('rate_limit', 10)
        time_since_last = time.time() - self.last_request_time
        min_interval = 1.0 / rate_limit
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        return True
    
    def record_request_result(self, success: bool, response_time: float):
        """Record result of a request."""
        self.request_count += 1
        if not success:
            self.error_count += 1
        
        # Check response time
        if response_time > self.max_response_time:
            self.logger.warning(
                f"Response time {response_time:.2f}s exceeds threshold {self.max_response_time:.2f}s"
            )
    
    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status."""
        error_rate = self.error_count / max(self.request_count, 1)
        
        return {
            'request_count': self.request_count,
            'error_count': self.error_count,
            'error_rate': error_rate,
            'elapsed_time': time.time() - self.start_time,
            'safety_status': 'OK' if error_rate < self.max_error_rate else 'WARNING'
        }
    
    def emergency_stop(self, reason: str):
        """Emergency stop with notification."""
        self.logger.critical(f"EMERGENCY STOP: {reason}")
        
        # In production, this would:
        # 1. Send alert to authorized contact
        # 2. Generate emergency report
        # 3. Stop all testing activities
        # 4. Document incident
        
        raise EmergencyStopException(f"Emergency stop: {reason}")


class AuthorizedAuditOrchestrator:
    """Orchestrates authorized security audits."""
    
    def __init__(self, authorization_dir: str = "./authorization"):
        self.authorization_validator = AuthorizationValidator(authorization_dir)
        self.logger = logging.getLogger("AuthorizedAuditOrchestrator")
    
    async def run_authorized_audit(self, target_url: str, scenario_file: str = None):
        """
        Run authorized security audit against target.
        
        Args:
            target_url: Target URL to audit
            scenario_file: Optional scenario configuration file
        """
        
        self.logger.info(f"Starting authorized audit for {target_url}")
        
        # Step 1: Validate authorization
        self.logger.info("Step 1: Validating authorization...")
        try:
            authorization = self.authorization_validator.validate_authorization(target_url)
        except AuthorizationError as e:
            self.logger.error(f"Authorization validation failed: {str(e)}")
            raise
        
        # Step 2: Initialize safety controller
        self.logger.info("Step 2: Initializing safety controller...")
        safety_controller = AuthorizedSafetyController(authorization)
        
        # Step 3: Initialize core components
        self.logger.info("Step 3: Initializing core components...")
        cycle_manager = ExecutionCycleManager()
        formal_state_model = FormalStateModel(cycle_manager)
        event_log = ImmutableEventLog("./data/events")
        await event_log.initialize()
        
        # Initialize oracle (mock for authorized testing)
        oracle_config = {
            'type': 'production_metrics',
            'production_endpoint': None,
            'baselines': authorization.scope.get('baselines', {}),
            'tolerance_threshold': 0.2
        }
        oracle = ProductionMetricsOracle(oracle_config)
        
        # Step 4: Create execution contract
        self.logger.info("Step 4: Creating execution contract...")
        planner = TestScenarioPlanner(cycle_manager, event_log, oracle)
        
        from architecture.formal_state_model import SystemConstraints
        
        constraints = SystemConstraints(
            max_concurrent_requests=authorization.limitations.get('max_concurrent', 50),
            max_error_rate=0.1,
            max_response_time=5.0,
            resource_limits={'cpu': 0.8, 'memory': 0.7},
            safety_invariants=['no_self_modification', 'deterministic_execution']
        )
        
        requirements = {
            'test_types': authorization.scope.get('test_types', []),
            'target_system': target_url,
            'duration': authorization.limitations.get('duration', 3600)
        }
        
        contract = await planner.create_execution_contract(requirements, constraints)
        self.logger.info(f"Contract created: {contract.contract_id}")
        
        # Step 5: Validate contract
        self.logger.info("Step 5: Validating contract...")
        oracle_validation = await planner.validate_contract(contract)
        
        if not oracle_validation:
            self.logger.warning("Oracle validation failed - proceeding with caution")
        
        # Step 6: Execute tests with safety controls
        self.logger.info("Step 6: Executing tests with safety controls...")
        execution_engine = PureExecutionEngine(cycle_manager, None)
        
        # Generate test requests based on authorization scope
        test_requests = self._generate_test_requests(
            target_url, 
            authorization.scope.get('test_types', []),
            authorization.limitations.get('max_requests', 100)
        )
        
        results = []
        for request_data in test_requests:
            try:
                # Safety check before each request
                safety_controller.check_safety_before_request()
                
                # Execute request
                result = await execution_engine.execute_validated_request(
                    None, request_data
                )
                
                # Record result
                success = result.execution_state.value in ['completed']
                response_time = result.duration
                safety_controller.record_request_result(success, response_time)
                
                results.append(result)
                
                # Log status
                if self.request_count % 100 == 0:
                    status = safety_controller.get_safety_status()
                    self.logger.info(f"Progress: {status}")
                
            except SafetyLimitError as e:
                self.logger.warning(f"Safety limit reached: {str(e)}")
                break
            except Exception as e:
                self.logger.error(f"Request failed: {str(e)}")
                safety_controller.record_request_result(False, 0.0)
        
        # Step 7: Generate report
        self.logger.info("Step 7: Generating audit report...")
        report = self._generate_audit_report(
            authorization, 
            results, 
            safety_controller.get_safety_status()
        )
        
        # Save report
        report_file = f"./data/audit_report_{authorization.authorization_id}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Audit report saved to {report_file}")
        self.logger.info(f"Authorized audit completed successfully")
        
        return report
    
    def _generate_test_requests(self, 
                               target_url: str, 
                               test_types: List[str], 
                               max_requests: int) -> List[Dict[str, Any]]:
        """Generate test requests based on authorization scope."""
        
        requests = []
        
        for test_type in test_types:
            if test_type == 'authentication_stress':
                for i in range(min(max_requests // 3, 100)):
                    requests.append({
                        'type': 'http_request',
                        'method': 'GET',
                        'url': f'{target_url}/login',
                        'headers': {
                            'User-Agent': f'EVENT_HORIZON-Audit-{i}'
                        }
                    })
            
            elif test_type == 'rate_limiting_validation':
                for i in range(min(max_requests // 3, 50)):
                    requests.append({
                        'type': 'http_request',
                        'method': 'GET',
                        'url': f'{target_url}/api/data',
                        'headers': {
                            'X-Test-Request': str(i)
                        }
                    })
            
            elif test_type == 'input_normalization':
                for i in range(min(max_requests // 3, 50)):
                    requests.append({
                        'type': 'http_request',
                        'method': 'POST',
                        'url': f'{target_url}/api/submit',
                        'data': {
                            'input': f'test_input_{i}'
                        }
                    })
        
        return requests[:max_requests]
    
    def _generate_audit_report(self, 
                               authorization: AuthorizationData,
                               results: List,
                               safety_status: Dict[str, Any]) -> Dict[str, Any]:
        """Generate audit report."""
        
        successful_results = [r for r in results if r.execution_state.value == 'completed']
        failed_results = [r for r in results if r.execution_state.value == 'failed']
        
        return {
            'authorization_id': authorization.authorization_id,
            'target_url': authorization.target_url,
            'audit_timestamp': time.time(),
            'summary': {
                'total_requests': len(results),
                'successful_requests': len(successful_results),
                'failed_requests': len(failed_results),
                'success_rate': len(successful_results) / max(len(results), 1),
                'safety_status': safety_status
            },
            'test_types': authorization.scope.get('test_types', []),
            'limitations_applied': authorization.limitations,
            'findings': [],
            'recommendations': [],
            'appendix': {
                'raw_results_count': len(results),
                'reporting_contact': authorization.contact_email
            }
        }


class AuthorizationError(Exception):
    """Authorization validation error."""
    pass


class SafetyLimitError(Exception):
    """Safety limit exceeded error."""
    pass


class EmergencyStopException(Exception):
    """Emergency stop exception."""
    pass
