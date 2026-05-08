"""
Tests for EVENT_HORIZON Testing Layers
"""

import pytest
import asyncio
import time

from event_horizon.core.models import TestRequest
from event_horizon.layers.nsl.normalization_stress import NormalizationStressLayer
from event_horizon.layers.scs.session_collapse import SessionCollapseSimulator
from event_horizon.layers.rlpm.rate_limit_pressure import RateLimitPressureModule
from event_horizon.layers.dbsil.db_stress import DBStressInterfaceLayer


class TestNormalizationStressLayer:
    """Test cases for NormalizationStressLayer"""
    
    @pytest.fixture
    def nsl(self):
        """Create a test NSL instance"""
        return NormalizationStressLayer()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample test request"""
        return TestRequest(
            id="test_req",
            timestamp=time.time(),
            source_ip="192.168.1.100",
            user_agent="Test-Agent/1.0",
            auth_token="test_token",
            session_id="test_session",
            payload={"username": "test_user", "password": "test_pass"},
            expected_result="success"
        )
    
    @pytest.mark.asyncio
    async def test_utf8_overlong_injection(self, nsl, sample_request):
        """Test UTF-8 overlong sequence injection"""
        await nsl._inject_utf8_overlong(sample_request)
        
        assert "nsl_utf8_overlong" in sample_request.anomaly_flags
        
        # Check for overlong sequences in payload
        if "username" in sample_request.payload:
            username = sample_request.payload["username"]
            assert b'\xc0\xaf' in username.encode('latin1') or b'\xc0\xae' in username.encode('latin1')
    
    @pytest.mark.asyncio
    async def test_unicode_normalization_injection(self, nsl, sample_request):
        """Test Unicode normalization issues injection"""
        await nsl._inject_unicode_normalization_issues(sample_request)
        
        assert "nsl_unicode_normalization" in sample_request.anomaly_flags
        
        # Check for Unicode variants
        if "normalization_test" in sample_request.payload:
            test_str = sample_request.payload["normalization_test"]
            assert any(ord(c) > 127 for c in test_str)  # Contains non-ASCII chars
    
    @pytest.mark.asyncio
    async def test_url_encoding_injection(self, nsl, sample_request):
        """Test URL encoding ambiguity injection"""
        await nsl._inject_url_encoding_ambiguity(sample_request)
        
        assert "nsl_url_encoding" in sample_request.anomaly_flags
        
        # Check for encoded content
        if "path" in sample_request.payload:
            path = sample_request.payload["path"]
            assert "%2F" in path or "%u002f" in path
    
    @pytest.mark.asyncio
    async def test_character_set_injection(self, nsl, sample_request):
        """Test character set issues injection"""
        await nsl._inject_character_set_issues(sample_request)
        
        assert "nsl_character_set" in sample_request.anomaly_flags
        
        # Check for problematic characters
        if "charset_test" in sample_request.payload:
            charset_test = sample_request.payload["charset_test"]
            assert any(ord(c) > 127 for c in charset_test)
    
    @pytest.mark.asyncio
    async def test_control_character_injection(self, nsl, sample_request):
        """Test control character injection"""
        await nsl._inject_control_characters(sample_request)
        
        assert "nsl_control_characters" in sample_request.anomaly_flags
        
        # Check for control characters in payload
        for field_value in sample_request.payload.values():
            if isinstance(field_value, str):
                if any(ord(c) < 32 for c in field_value if c != '\n' and c != '\t'):
                    break
        else:
            pytest.fail("No control characters found in payload")
    
    @pytest.mark.asyncio
    async def test_process_request(self, nsl, sample_request):
        """Test complete request processing"""
        await nsl.process_request(sample_request)
        
        # Should have exactly one anomaly flag
        assert len(sample_request.anomaly_flags) == 1
        assert sample_request.anomaly_flags[0].startswith("nsl_")
    
    def test_normalization_loss_analysis(self, nsl):
        """Test normalization loss analysis"""
        original = {"username": "test_user", "data": "test€\u201c"}
        normalized = {"username": "test_user", "data": "test€"}  # Lost some characters
        
        analysis = nsl.analyze_normalization_loss(original, normalized)
        
        assert "fields_changed" in analysis
        assert "characters_lost" in analysis
        assert "semantic_drift" in analysis
        assert "encoding_issues" in analysis
        assert analysis["characters_lost"] > 0
    
    def test_get_test_cases(self, nsl):
        """Test getting predefined test cases"""
        test_cases = nsl.get_normalization_test_cases()
        
        assert len(test_cases) > 0
        assert all("name" in case for case in test_cases)
        assert all("input" in case for case in test_cases)
        assert all("expected_behavior" in case for case in test_cases)


class TestSessionCollapseSimulator:
    """Test cases for SessionCollapseSimulator"""
    
    @pytest.fixture
    def scs(self):
        """Create a test SCS instance"""
        return SessionCollapseSimulator()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample test request"""
        return TestRequest(
            id="test_req",
            timestamp=time.time(),
            source_ip="192.168.1.100",
            user_agent="Test-Agent/1.0",
            auth_token="test_token",
            session_id="test_session",
            payload={"username": "test_user"},
            expected_result="success"
        )
    
    @pytest.mark.asyncio
    async def test_session_flood_simulation(self, scs, sample_request):
        """Test session flood simulation"""
        initial_session_count = len(scs.active_sessions)
        
        await scs._simulate_session_flood(sample_request)
        
        assert "scs_session_flood" in sample_request.anomaly_flags
        assert len(scs.active_sessions) > initial_session_count
    
    @pytest.mark.asyncio
    async def test_race_condition_simulation(self, scs, sample_request):
        """Test race condition simulation"""
        await scs._simulate_race_condition(sample_request)
        
        assert "scs_race_condition" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_ghost_session_simulation(self, scs, sample_request):
        """Test ghost session simulation"""
        await scs._simulate_ghost_session(sample_request)
        
        assert "scs_ghost_session" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_session_desync_simulation(self, scs, sample_request):
        """Test session desync simulation"""
        await scs._simulate_session_desync(sample_request)
        
        assert "scs_session_desync" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_memory_leak_simulation(self, scs, sample_request):
        """Test memory leak simulation"""
        initial_session_count = len(scs.active_sessions)
        
        await scs._simulate_memory_leak(sample_request)
        
        assert "scs_memory_leak" in sample_request.anomaly_flags
        assert len(scs.active_sessions) > initial_session_count
    
    @pytest.mark.asyncio
    async def test_invalidation_race_simulation(self, scs, sample_request):
        """Test invalidation race simulation"""
        await scs._simulate_invalidation_race(sample_request)
        
        assert "scs_invalidation_race" in sample_request.anomaly_flags
    
    def test_session_integrity_metrics(self, scs):
        """Test session integrity metrics calculation"""
        # Add some test data
        from event_horizon.layers.scs.session_collapse import SessionConflict
        scs.conflicts.append(SessionConflict(
            session_id="test",
            node_a="node1",
            node_b="node2",
            state_a={"test": "data1"},
            state_b={"test": "data2"},
            conflict_type="data_mismatch"
        ))
        
        metrics = scs.get_session_integrity_metrics()
        
        assert "total_sessions" in metrics
        assert "total_conflicts" in metrics
        assert "conflict_rate" in metrics
        assert "node_consistency" in metrics
        assert metrics["total_conflicts"] == 1
    
    def test_session_heatmap_data(self, scs):
        """Test session integrity heatmap data generation"""
        heatmap_data = scs.get_session_heatmap_data()
        
        assert "nodes" in heatmap_data
        assert "conflict_hotspots" in heatmap_data
        assert "session_density" in heatmap_data
        assert "risk_areas" in heatmap_data
        assert len(heatmap_data["nodes"]) == len(scs.nodes)


class TestRateLimitPressureModule:
    """Test cases for RateLimitPressureModule"""
    
    @pytest.fixture
    def rlpm(self):
        """Create a test RLPM instance"""
        return RateLimitPressureModule()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample test request"""
        return TestRequest(
            id="test_req",
            timestamp=time.time(),
            source_ip="192.168.1.100",
            user_agent="Test-Agent/1.0",
            auth_token="test_token",
            session_id="test_session",
            payload={"username": "test_user"},
            expected_result="success"
        )
    
    @pytest.mark.asyncio
    async def test_burst_traffic_simulation(self, rlpm, sample_request):
        """Test burst traffic simulation"""
        await rlpm._simulate_burst_traffic(sample_request)
        
        assert "rlpm_burst_traffic" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_distributed_spoofing_simulation(self, rlpm, sample_request):
        """Test distributed spoofing simulation"""
        await rlpm._simulate_distributed_spoofing(sample_request)
        
        assert "rlpm_distributed_spoof" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_evasion_attempt_simulation(self, rlpm, sample_request):
        """Test evasion attempt simulation"""
        await rlpm._simulate_evasion_attempt(sample_request)
        
        assert "rlpm_evasion_attempt" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_header_rotation_evasion(self, rlpm, sample_request):
        """Test header rotation evasion"""
        initial_bypass_attempts = rlpm.bypass_attempts
        
        await rlpm._rotate_headers_evasion(sample_request)
        
        assert rlpm.bypass_attempts > initial_bypass_attempts
    
    @pytest.mark.asyncio
    async def test_rate_limit_checking(self, rlpm):
        """Test rate limit checking"""
        from event_horizon.core.models import TestRequest
        request = TestRequest(
            id="test_req",
            timestamp=time.time(),
            source_ip="192.168.1.100",
            user_agent="Test-Agent/1.0",
            auth_token="test_token",
            session_id="test_session",
            payload={"test": "data"},
            expected_result="success"
        )
        
        # First request should be allowed
        await rlpm._check_rate_limits(request)
        assert rlpm.allowed_requests == 1
        assert rlpm.blocked_requests == 0
    
    def test_rate_limit_metrics(self, rlpm):
        """Test rate limit metrics calculation"""
        metrics = rlpm.get_rate_limit_metrics()
        
        assert "total_requests" in metrics
        assert "allowed_requests" in metrics
        assert "blocked_requests" in metrics
        assert "block_rate" in metrics
        assert "bypass_attempts" in metrics
        assert "active_rate_limits" in metrics
    
    def test_spoofed_ip_generation(self, rlpm):
        """Test spoofed IP generation"""
        ip = rlpm._generate_spoofed_ip()
        
        assert isinstance(ip, str)
        assert ip.count('.') == 3  # Valid IPv4 format
        parts = ip.split('.')
        assert all(0 <= int(part) <= 254 for part in parts)


class TestDBStressInterfaceLayer:
    """Test cases for DBStressInterfaceLayer"""
    
    @pytest.fixture
    def dbsil(self):
        """Create a test DB-SIL instance"""
        return DBStressInterfaceLayer()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample test request"""
        return TestRequest(
            id="test_req",
            timestamp=time.time(),
            source_ip="192.168.1.100",
            user_agent="Test-Agent/1.0",
            auth_token="test_token",
            session_id="test_session",
            payload={"username": "test_user"},
            expected_result="success"
        )
    
    @pytest.mark.asyncio
    async def test_connection_exhaustion_simulation(self, dbsil, sample_request):
        """Test connection exhaustion simulation"""
        initial_exhaustion_count = dbsil.connection_exhaustion_count
        
        await dbsil._simulate_connection_exhaustion(sample_request)
        
        assert "dbsil_connection_exhaustion" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_transaction_starvation_simulation(self, dbsil, sample_request):
        """Test transaction starvation simulation"""
        await dbsil._simulate_transaction_starvation(sample_request)
        
        assert "dbsil_transaction_starvation" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_queue_saturation_simulation(self, dbsil, sample_request):
        """Test query queue saturation simulation"""
        await dbsil._simulate_queue_saturation(sample_request)
        
        assert "dbsil_queue_saturation" in sample_request.anomaly_flags
    
    @pytest.mark.asyncio
    async def test_deadlock_simulation(self, dbsil, sample_request):
        """Test deadlock simulation"""
        initial_deadlock_count = dbsil.deadlock_count
        
        await dbsil._simulate_deadlock(sample_request)
        
        assert "dbsil_deadlock_simulation" in sample_request.anomaly_flags
        assert dbsil.deadlock_count > initial_deadlock_count
    
    @pytest.mark.asyncio
    async def test_connection_management(self, dbsil):
        """Test connection pool management"""
        # Get connection
        connection_id = await dbsil._get_connection()
        
        assert connection_id is not None
        assert connection_id in dbsil.active_connections
        assert len(dbsil.active_connections) <= dbsil.max_connections
        
        # Release connection
        await dbsil._release_connection(connection_id)
        
        assert connection_id not in dbsil.active_connections
    
    @pytest.mark.asyncio
    async def test_query_execution(self, dbsil):
        """Test query execution"""
        connection_id = await dbsil._get_connection()
        
        if connection_id:
            initial_query_count = dbsil.total_queries
            
            success = await dbsil._execute_query(connection_id, "SELECT 1")
            
            assert dbsil.total_queries > initial_query_count
            assert isinstance(success, bool)
            
            await dbsil._release_connection(connection_id)
    
    def test_database_metrics(self, dbsil):
        """Test database metrics calculation"""
        metrics = dbsil.get_database_metrics()
        
        assert "total_queries" in metrics
        assert "failed_queries" in metrics
        assert "query_success_rate" in metrics
        assert "active_connections" in metrics
        assert "max_connections" in metrics
        assert "connection_utilization" in metrics
        assert "deadlock_count" in metrics
        assert "queue_size" in metrics
    
    def test_malformed_queries(self, dbsil):
        """Test malformed query generation"""
        malformed_queries = dbsil._generate_malformed_queries()
        
        assert len(malformed_queries) > 0
        assert all(isinstance(query, str) for query in malformed_queries)
        assert all("SELECT" in query or "INSERT" in query or "UPDATE" in query or "DELETE" in query 
                  or "CREATE" in query for query in malformed_queries)


if __name__ == "__main__":
    pytest.main([__file__])
