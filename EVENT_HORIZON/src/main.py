"""
EVENT_HORIZON Main Entry Point

Defensive authentication resilience testing framework.
Designed for isolated laboratory environments and authorized external audits.
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from architecture.formal_state_model import FormalStateModel, DomainType, StateTransition
from architecture.core_constraints import ExecutionCycleManager
from architecture.control_plane import TestScenarioPlanner
from architecture.data_plane import PureExecutionEngine
from architecture.observation_plane import CausalGraphBuilder, SystemPressureMonitor
from architecture.immutable_log import ImmutableEventLog, EventType
from architecture.external_oracle import ProductionMetricsOracle, OracleManager
from authorized_audit import AuthorizedAuditOrchestrator, AuthorizationValidator


async def run_isolated_lab_test(target_url: str, scenario_file: str = None):
    """
    Run EVENT_HORIZON in isolated laboratory environment.
    
    CRITICAL: This function is designed ONLY for isolated lab environments.
    Never run against production systems without explicit authorization.
    """
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("EVENT_HORIZON")
    
    logger.info("=" * 60)
    logger.info("EVENT_HORIZON - Defensive Authentication Resilience Framework")
    logger.info("=" * 60)
    logger.info(f"Target: {target_url}")
    logger.info("Environment: ISOLATED LABORATORY")
    logger.info("Mode: DEFENSIVE TESTING ONLY")
    logger.info("=" * 60)
    
    # Validate target is isolated
    if not _validate_isolated_target(target_url):
        logger.error("Target validation failed - not an isolated environment")
        logger.error("EVENT_HORIZON is designed for isolated laboratory testing only")
        sys.exit(1)
    
    # Initialize core components
    cycle_manager = ExecutionCycleManager()
    formal_state_model = FormalStateModel(cycle_manager)
    causal_graph = CausalGraphBuilder(cycle_manager)
    pressure_monitor = SystemPressureMonitor(cycle_manager)
    event_log = ImmutableEventLog("./data/events")
    await event_log.initialize()
    
    # Initialize external oracle
    oracle_config = {
        'type': 'production_metrics',
        'production_endpoint': None,  # No external oracle for isolated lab
        'baselines': {
            'error_rate': 0.05,
            'response_time_p95': 2.0,
            'throughput': 1000
        },
        'tolerance_threshold': 0.2
    }
    oracle = ProductionMetricsOracle(oracle_config)
    
    # Initialize components
    planner = TestScenarioPlanner(cycle_manager, event_log, oracle)
    execution_engine = PureExecutionEngine(cycle_manager, None)  # No backpressure for simple test
    
    try:
        # Create execution contract
        from architecture.formal_state_model import SystemConstraints, ResourceCost
        
        constraints = SystemConstraints(
            max_concurrent_requests=50,
            max_error_rate=0.1,
            max_response_time=5.0,
            resource_limits={'cpu': 0.8, 'memory': 0.7},
            safety_invariants=['no_self_modification', 'deterministic_execution']
        )
        
        requirements = {
            'test_types': ['authentication_stress', 'rate_limiting_test'],
            'target_system': target_url,
            'duration': 300
        }
        
        logger.info("Creating execution contract...")
        contract = await planner.create_execution_contract(requirements, constraints)
        logger.info(f"Contract created: {contract.contract_id}")
        
        # Validate contract
        logger.info("Validating contract against external oracle...")
        oracle_validation = await planner.validate_contract(contract)
        
        if not oracle_validation:
            logger.warning("Oracle validation failed - proceeding with caution")
        
        # Execute test
        logger.info("Starting execution...")
        
        # Create sample requests
        sample_requests = [
            (None, {'type': 'http_request', 'method': 'GET', 'url': f'{target_url}/health'})
            for _ in range(10)
        ]
        
        results = await execution_engine.execute_batch(sample_requests)
        
        logger.info(f"Execution completed: {len(results)} results")
        
        # Record final state
        final_state = formal_state_model.create_state(
            domain_states={
                DomainType.GENERATION: {'status': 'completed'},
                DomainType.EXECUTION: {'results': len(results)},
                DomainType.OBSERVATION: {'events': len(causal_graph.events)},
                DomainType.PLANNING: {'contract_id': contract.contract_id}
            },
            resource_usage=ResourceCost(
                cpu_cycles=100000,
                memory_bytes=50 * 1024 * 1024,
                network_bytes=1 * 1024 * 1024,
                time_units=10.0,
                io_operations=100
            )
        )
        
        logger.info("Final state created")
        logger.info(f"State hash: {final_state.state_hash}")
        
        # Export results
        formal_state_model.export_state_model("./data/state_model.json")
        logger.info("State model exported to ./data/state_model.json")
        
        logger.info("=" * 60)
        logger.info("EVENT_HORIZON test completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        raise


def _validate_isolated_target(target_url: str) -> bool:
    """
    Validate that target is in isolated laboratory environment.
    
    CRITICAL: Prevents execution against production systems.
    """
    
    # Only allow localhost or specific lab domains
    allowed_domains = [
        'localhost',
        '127.0.0.1',
        'mock-target',
        'event-horizon-mock',
        'event-horizon-target'
    ]
    
    if not target_url:
        return False
    
    # Check if target is in allowed list
    for domain in allowed_domains:
        if domain in target_url:
            return True
    
    # Additional check for Docker network
    if '172.17' in target_url or '172.20' in target_url:
        return True
    
    return False


async def run_authorized_audit(target_url: str, scenario_file: str = None):
    """
    Run EVENT_HORIZON authorized audit against external target.
    
    CRITICAL: This function requires formal authorization documents.
    Authorization will be validated before any testing begins.
    """
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("EVENT_HORIZON")
    
    logger.info("=" * 60)
    logger.info("EVENT_HORIZON - Authorized Security Audit")
    logger.info("=" * 60)
    logger.info(f"Target: {target_url}")
    logger.info("Mode: AUTHORIZED AUDIT")
    logger.info("=" * 60)
    
    # Initialize authorized audit orchestrator
    orchestrator = AuthorizedAuditOrchestrator()
    
    try:
        # Run authorized audit with full validation
        report = await orchestrator.run_authorized_audit(target_url, scenario_file)
        
        logger.info("=" * 60)
        logger.info("Authorized audit completed successfully")
        logger.info(f"Authorization ID: {report['authorization_id']}")
        logger.info(f"Total requests: {report['summary']['total_requests']}")
        logger.info(f"Success rate: {report['summary']['success_rate']:.2%}")
        logger.info("=" * 60)
        
        return report
        
    except Exception as e:
        logger.error(f"Authorized audit failed: {str(e)}")
        logger.error("Please ensure authorization documents are properly configured in ./authorization/")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='EVENT_HORIZON - Defensive Authentication Resilience Framework'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        default='http://mock-target:9000',
        help='Target URL (isolated laboratory only by default)'
    )
    
    parser.add_argument(
        '--scenario',
        type=str,
        default=None,
        help='Scenario file path'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['isolated', 'authorized'],
        default='isolated',
        help='Execution mode: isolated (default) or authorized (requires authorization)'
    )
    
    parser.add_argument(
        '--validate-isolation',
        action='store_true',
        help='Validate isolated environment only'
    )
    
    parser.add_argument(
        '--validate-authorization',
        action='store_true',
        help='Validate authorization documents only'
    )
    
    parser.add_argument(
        '--authorization-dir',
        type=str,
        default='./authorization',
        help='Directory containing authorization documents'
    )
    
    args = parser.parse_args()
    
    if args.validate_isolation:
        # Just validate isolation
        is_valid = _validate_isolated_target(args.target)
        print(f"Isolation validation: {'PASS' if is_valid else 'FAIL'}")
        sys.exit(0 if is_valid else 1)
    
    if args.validate_authorization:
        # Validate authorization documents
        validator = AuthorizationValidator(args.authorization_dir)
        try:
            template = validator.generate_authorization_template(args.target)
            print("Authorization template generated:")
            print(json.dumps(template, indent=2))
            
            # Try to validate if authorization.json exists
            try:
                authorization = validator.validate_authorization(args.target)
                print(f"Authorization validation: PASS")
                print(f"Authorization ID: {authorization.authorization_id}")
                print(f"Status: {authorization.status.value}")
            except Exception as e:
                print(f"Authorization validation: FAIL - {str(e)}")
                print("Please complete authorization documents in ./authorization/")
            
        except Exception as e:
            print(f"Authorization validation error: {str(e)}")
            sys.exit(1)
        
        sys.exit(0)
    
    # Determine execution mode
    if args.mode == 'authorized':
        # Check if target is isolated (should not be for authorized mode)
        if _validate_isolated_target(args.target):
            print("WARNING: Authorized mode selected but target appears to be isolated")
            print("Use --mode isolated for isolated laboratory testing")
            response = input("Continue in authorized mode? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborting")
                sys.exit(1)
        
        # Run authorized audit
        asyncio.run(run_authorized_audit(args.target, args.scenario))
    
    else:
        # Default: isolated lab mode
        if not _validate_isolated_target(args.target):
            print("ERROR: Target is not in isolated laboratory environment")
            print("For authorized external testing, use --mode authorized")
            print("Ensure authorization documents are in ./authorization/")
            sys.exit(1)
        
        # Run isolated lab test
        asyncio.run(run_isolated_lab_test(args.target, args.scenario))


if __name__ == '__main__':
    main()
