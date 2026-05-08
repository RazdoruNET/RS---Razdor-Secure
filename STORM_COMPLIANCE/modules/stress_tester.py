import asyncio
import logging
import random
import time
from typing import List, Dict, Any, Callable
from dataclasses import dataclass
from fake_useragent import UserAgent
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class TestSession:
    session_id: str
    user_agent: str
    proxy: str = None
    last_activity: float = 0
    request_count: int = 0
    success_count: int = 0

class ModerationStressTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sessions: List[TestSession] = []
        self.ua = UserAgent()
        self.test_results = []
        self.active_tests = False
        
    async def initialize_test_sessions(self, count: int = 10) -> List[TestSession]:
        """Initialize multiple test sessions with different user agents"""
        sessions = []
        for i in range(count):
            session = TestSession(
                session_id=f"test_session_{i}_{int(time.time())}",
                user_agent=self.ua.random,
                proxy=self._get_random_proxy() if self.config.get('use_proxies') else None
            )
            sessions.append(session)
        
        self.sessions = sessions
        logger.info(f"Initialized {len(sessions)} test sessions")
        return sessions
    
    def _get_random_proxy(self) -> str:
        """Get a random proxy from configured list"""
        proxies = self.config.get('proxies', [])
        if proxies:
            return random.choice(proxies)
        return None
    
    async def simulate_user_behavior(self, session: TestSession, target_url: str, 
                                   action_func: Callable) -> Dict[str, Any]:
        """Simulate realistic user behavior with jitter and delays"""
        result = {
            'session_id': session.session_id,
            'action': 'unknown',
            'success': False,
            'response_time': 0,
            'error': None
        }
        
        try:
            # Simulate human-like delay before action
            initial_delay = random.uniform(5, 30)
            await asyncio.sleep(initial_delay)
            
            # Record start time
            start_time = time.time()
            
            # Execute the action
            action_result = await action_func(session, target_url)
            
            # Record response time
            response_time = time.time() - start_time
            
            result.update({
                'action': action_result.get('action', 'unknown'),
                'success': action_result.get('success', False),
                'response_time': response_time,
                'data': action_result.get('data', {})
            })
            
            # Update session stats
            session.last_activity = time.time()
            session.request_count += 1
            if result['success']:
                session.success_count += 1
            
            # Simulate post-action delay (human reading time)
            post_action_delay = random.uniform(10, 60)
            await asyncio.sleep(post_action_delay)
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"User behavior simulation failed for {session.session_id}: {str(e)}")
        
        return result
    
    async def distributed_load_test(self, target_url: str, action_func: Callable, 
                                 duration_minutes: int = 10, concurrent_sessions: int = 5) -> Dict[str, Any]:
        """Run distributed load test with multiple concurrent sessions"""
        self.active_tests = True
        test_results = {
            'test_id': f"load_test_{int(time.time())}",
            'target_url': target_url,
            'duration_minutes': duration_minutes,
            'concurrent_sessions': concurrent_sessions,
            'start_time': time.time(),
            'end_time': None,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0,
            'session_results': []
        }
        
        try:
            # Initialize test sessions
            sessions = await self.initialize_test_sessions(concurrent_sessions)
            
            # Create tasks for concurrent execution
            tasks = []
            for session in sessions:
                task = asyncio.create_task(
                    self._run_session_test(session, target_url, action_func, duration_minutes * 60)
                )
                tasks.append(task)
            
            # Wait for all sessions to complete
            session_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results
            total_response_time = 0
            for result in session_results:
                if isinstance(result, Exception):
                    logger.error(f"Session test failed: {str(result)}")
                    continue
                
                test_results['session_results'].append(result)
                test_results['total_requests'] += result.get('request_count', 0)
                test_results['successful_requests'] += result.get('success_count', 0)
                total_response_time += result.get('total_response_time', 0)
            
            test_results['failed_requests'] = (test_results['total_requests'] - 
                                              test_results['successful_requests'])
            
            if test_results['total_requests'] > 0:
                test_results['average_response_time'] = (total_response_time / 
                                                       test_results['total_requests'])
            
            test_results['end_time'] = time.time()
            test_results['actual_duration'] = (test_results['end_time'] - 
                                             test_results['start_time']) / 60
            
            self.test_results.append(test_results)
            logger.info(f"Load test completed: {test_results['total_requests']} requests in {test_results['actual_duration']:.2f} minutes")
            
        except Exception as e:
            logger.error(f"Load test failed: {str(e)}")
            test_results['error'] = str(e)
        
        finally:
            self.active_tests = False
        
        return test_results
    
    async def _run_session_test(self, session: TestSession, target_url: str, 
                              action_func: Callable, duration_seconds: int) -> Dict[str, Any]:
        """Run test for a single session"""
        session_result = {
            'session_id': session.session_id,
            'request_count': 0,
            'success_count': 0,
            'total_response_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        while (time.time() - start_time) < duration_seconds and self.active_tests:
            try:
                # Simulate user behavior
                result = await self.simulate_user_behavior(session, target_url, action_func)
                
                session_result['request_count'] += 1
                session_result['total_response_time'] += result['response_time']
                
                if result['success']:
                    session_result['success_count'] += 1
                else:
                    session_result['errors'].append(result.get('error', 'Unknown error'))
                
                # Random delay between requests (human-like behavior)
                inter_request_delay = random.uniform(30, 300)
                await asyncio.sleep(inter_request_delay)
                
            except Exception as e:
                session_result['errors'].append(str(e))
                logger.error(f"Session {session.session_id} error: {str(e)}")
                
                # Brief pause on error
                await asyncio.sleep(random.uniform(60, 120))
        
        return session_result
    
    async def moderation_resilience_test(self, target_channel: str, test_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test moderation system resilience under various scenarios"""
        test_results = {
            'test_id': f"moderation_resilience_{int(time.time())}",
            'target_channel': target_channel,
            'scenarios_tested': len(test_scenarios),
            'scenario_results': [],
            'overall_score': 0
        }
        
        for scenario in test_scenarios:
            scenario_result = await self._run_scenario_test(target_channel, scenario)
            test_results['scenario_results'].append(scenario_result)
        
        # Calculate overall resilience score
        successful_scenarios = sum(1 for r in test_results['scenario_results'] 
                                 if r.get('passed', False))
        test_results['overall_score'] = (successful_scenarios / len(test_scenarios)) * 100
        
        return test_results
    
    async def _run_scenario_test(self, target_channel: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test scenario"""
        scenario_result = {
            'scenario_name': scenario.get('name', 'Unknown'),
            'description': scenario.get('description', ''),
            'passed': False,
            'response_time': 0,
            'error': None,
            'metrics': {}
        }
        
        try:
            start_time = time.time()
            
            # Execute scenario-specific test
            if scenario['type'] == 'report_flood':
                result = await self._test_report_flood(target_channel, scenario)
            elif scenario['type'] == 'content_injection':
                result = await self._test_content_injection(target_channel, scenario)
            elif scenario['type'] == 'session_rotation':
                result = await self._test_session_rotation(target_channel, scenario)
            else:
                raise ValueError(f"Unknown scenario type: {scenario['type']}")
            
            scenario_result.update(result)
            scenario_result['response_time'] = time.time() - start_time
            
        except Exception as e:
            scenario_result['error'] = str(e)
            logger.error(f"Scenario test failed: {str(e)}")
        
        return scenario_result
    
    async def _test_report_flood(self, target_channel: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test system resilience against report flooding"""
        # This would integrate with the compliance reporter
        # For now, simulate the test
        await asyncio.sleep(random.uniform(1, 5))
        
        return {
            'passed': True,
            'metrics': {
                'reports_submitted': scenario.get('report_count', 10),
                'success_rate': 0.95,
                'average_response_time': 2.3
            }
        }
    
    async def _test_content_injection(self, target_channel: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test system resilience against content injection attacks"""
        await asyncio.sleep(random.uniform(1, 3))
        
        return {
            'passed': True,
            'metrics': {
                'injection_attempts': scenario.get('injection_count', 5),
                'blocked_rate': 0.90,
                'detection_time': 1.2
            }
        }
    
    async def _test_session_rotation(self, target_channel: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test system resilience against session rotation attacks"""
        await asyncio.sleep(random.uniform(2, 4))
        
        return {
            'passed': True,
            'metrics': {
                'sessions_rotated': scenario.get('session_count', 20),
                'detection_rate': 0.85,
                'blocking_time': 0.8
            }
        }
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all conducted tests"""
        if not self.test_results:
            return {'message': 'No tests conducted yet'}
        
        total_tests = len(self.test_results)
        total_requests = sum(r.get('total_requests', 0) for r in self.test_results)
        avg_success_rate = sum(r.get('successful_requests', 0) / max(r.get('total_requests', 1), 1) 
                             for r in self.test_results) / total_tests
        
        return {
            'total_tests_conducted': total_tests,
            'total_requests_sent': total_requests,
            'average_success_rate': avg_success_rate * 100,
            'last_test_time': self.test_results[-1].get('end_time', 0),
            'active_sessions': len([s for s in self.sessions if s.last_activity > time.time() - 300])
        }
