"""
DB Stress Interface Layer (DB-SIL)

Tests database connection pool resilience, transaction starvation,
and query queue saturation under malformed auth payloads.
"""

import asyncio
import random
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import structlog

from ...core.models import TestRequest, FailureEvent

logger = structlog.get_logger(__name__)


@dataclass
class ConnectionState:
    """Represents a database connection state"""
    connection_id: str
    created_at: float
    last_used: float
    is_active: bool = True
    is_locked: bool = False
    query_count: int = 0
    lock_holder: Optional[str] = None
    lock_time: float = 0.0


@dataclass
class TransactionState:
    """Represents a database transaction state"""
    transaction_id: str
    connection_id: str
    started_at: float
    queries: List[str] = field(default_factory=list)
    is_active: bool = True
    isolation_level: str = "READ_COMMITTED"
    rollback_reason: Optional[str] = None


@dataclass
class QueryQueue:
    """Represents the database query queue"""
    pending_queries: List[Dict[str, Any]] = field(default_factory=list)
    max_size: int = 1000
    current_size: int = field(default_factory=lambda: 0)
    
    def add_query(self, query: Dict[str, Any]) -> bool:
        """Add query to queue, return False if full"""
        if self.current_size >= self.max_size:
            return False
        
        self.pending_queries.append(query)
        self.current_size += 1
        return True
    
    def get_next_query(self) -> Optional[Dict[str, Any]]:
        """Get next query from queue"""
        if not self.pending_queries:
            return None
        
        query = self.pending_queries.pop(0)
        self.current_size -= 1
        return query


class DBStressInterfaceLayer:
    """
    Tests database resilience under various stress conditions.
    
    This layer simulates:
    - Connection pool exhaustion
    - Transaction starvation
    - Query queue saturation
    - Deadlock scenarios
    - Lock contention
    """
    
    def __init__(self):
        # Connection pool simulation
        self.max_connections = 100
        self.active_connections: Dict[str, ConnectionState] = {}
        self.connection_pool: List[str] = []
        
        # Transaction management
        self.active_transactions: Dict[str, TransactionState] = {}
        self.transaction_counter = 0
        
        # Query queue
        self.query_queue = QueryQueue(max_size=500)
        
        # Lock management
        self.table_locks: Dict[str, str] = {}  # table -> connection_id
        self.row_locks: Dict[str, str] = {}    # row_id -> connection_id
        
        # Statistics
        self.total_queries = 0
        self.failed_queries = 0
        self.deadlock_count = 0
        self.timeout_count = 0
        self.connection_exhaustion_count = 0
        
        # Malformed query patterns
        self.malformed_queries = self._generate_malformed_queries()
        
        logger.info("DB Stress Interface Layer initialized")
    
    async def process_request(self, request: TestRequest) -> None:
        """
        Process a request through database stress testing.
        
        Args:
            request: The test request to process
        """
        # Randomly apply database stress techniques
        stress_type = random.choice([
            "connection_exhaustion", "transaction_starvation", "queue_saturation",
            "deadlock_simulation", "lock_contention", "malformed_query"
        ])
        
        if stress_type == "connection_exhaustion":
            await self._simulate_connection_exhaustion(request)
        elif stress_type == "transaction_starvation":
            await self._simulate_transaction_starvation(request)
        elif stress_type == "queue_saturation":
            await self._simulate_queue_saturation(request)
        elif stress_type == "deadlock_simulation":
            await self._simulate_deadlock(request)
        elif stress_type == "lock_contention":
            await self._simulate_lock_contention(request)
        elif stress_type == "malformed_query":
            await self._simulate_malformed_query(request)
        
        # Add anomaly flag
        request.anomaly_flags.append(f"dbsil_{stress_type}")
        
        logger.debug("Applied database stress", 
                    request_id=request.id, 
                    stress_type=stress_type)
    
    async def _simulate_connection_exhaustion(self, request: TestRequest) -> None:
        """Simulate connection pool exhaustion"""
        # Create many connections to exhaust the pool
        exhaustion_size = min(self.max_connections + 20, 150)
        
        for i in range(exhaustion_size):
            connection_id = f"conn_{i}"
            
            if len(self.active_connections) >= self.max_connections:
                self.connection_exhaustion_count += 1
                logger.debug("Connection pool exhausted", 
                           active_connections=len(self.active_connections),
                           max_connections=self.max_connections)
                break
            
            connection = ConnectionState(
                connection_id=connection_id,
                created_at=time.time(),
                last_used=time.time()
            )
            
            self.active_connections[connection_id] = connection
            
            # Simulate connection usage
            await self._use_connection(connection_id, request)
    
    async def _simulate_transaction_starvation(self, request: TestRequest) -> None:
        """Simulate transaction starvation scenarios"""
        # Create long-running transactions
        starvation_count = random.randint(5, 15)
        
        for i in range(starvation_count):
            transaction_id = f"tx_{self.transaction_counter}"
            self.transaction_counter += 1
            
            # Get connection
            connection_id = await self._get_connection()
            if not connection_id:
                continue
            
            # Create long-running transaction
            transaction = TransactionState(
                transaction_id=transaction_id,
                connection_id=connection_id,
                started_at=time.time(),
                isolation_level=random.choice(["READ_COMMITTED", "REPEATABLE_READ", "SERIALIZABLE"])
            )
            
            self.active_transactions[transaction_id] = transaction
            
            # Add queries that will run for a long time
            long_queries = [
                "SELECT * FROM large_table WHERE complex_condition",
                "UPDATE sensitive_table SET status = 'processing' WHERE id IN (SELECT id FROM another_table)",
                "INSERT INTO audit_log SELECT * FROM activity_log WHERE timestamp > NOW() - INTERVAL '1 hour'"
            ]
            
            for query in long_queries:
                transaction.queries.append(query)
                await self._execute_query(connection_id, query, transaction_id)
            
            # Simulate long transaction duration
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # Randomly rollback some transactions
            if random.random() < 0.3:
                transaction.rollback_reason = "timeout"
                transaction.is_active = False
                await self._release_connection(connection_id)
    
    async def _simulate_queue_saturation(self, request: TestRequest) -> None:
        """Simulate query queue saturation"""
        # Generate many queries to saturate the queue
        saturation_size = random.randint(100, 600)
        
        for i in range(saturation_size):
            query = {
                "id": f"query_{i}",
                "sql": random.choice([
                    "SELECT * FROM users WHERE id = ?",
                    "UPDATE sessions SET last_access = NOW() WHERE session_id = ?",
                    "INSERT INTO auth_log (user_id, action, timestamp) VALUES (?, ?, NOW())",
                    "DELETE FROM temp_tokens WHERE expires < NOW()"
                ]),
                "params": [f"param_{i}"],
                "priority": random.choice(["high", "medium", "low"]),
                "timestamp": time.time(),
                "request_id": request.id
            }
            
            # Try to add to queue
            if not self.query_queue.add_query(query):
                # Queue is full
                logger.debug("Query queue saturated", queue_size=self.query_queue.current_size)
                break
        
        # Process some queries from queue
        processed = 0
        while self.query_queue.pending_queries and processed < 50:
            query = self.query_queue.get_next_query()
            if query:
                connection_id = await self._get_connection()
                if connection_id:
                    await self._execute_query(connection_id, query["sql"])
                    processed += 1
                    await self._release_connection(connection_id)
    
    async def _simulate_deadlock(self, request: TestRequest) -> None:
        """Simulate deadlock scenarios"""
        # Create multiple transactions that will deadlock
        deadlock_transactions = []
        
        for i in range(3):  # Create 3 transactions
            transaction_id = f"deadlock_tx_{i}"
            connection_id = await self._get_connection()
            
            if not connection_id:
                continue
            
            transaction = TransactionState(
                transaction_id=transaction_id,
                connection_id=connection_id,
                started_at=time.time(),
                isolation_level="SERIALIZABLE"  # More likely to deadlock
            )
            
            self.active_transactions[transaction_id] = transaction
            deadlock_transactions.append(transaction)
        
        # Create deadlock scenario: each transaction locks different tables in different order
        lock_orders = [
            ["users", "sessions"],
            ["sessions", "auth_tokens"],
            ["auth_tokens", "users"]
        ]
        
        tasks = []
        for i, transaction in enumerate(deadlock_transactions):
            lock_order = lock_orders[i]
            task = self._execute_deadlock_transaction(transaction, lock_order)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for deadlocks and resolve
        self.deadlock_count += 1
        await self._resolve_deadlocks()
    
    async def _execute_deadlock_transaction(self, transaction: TransactionState, lock_order: List[str]) -> None:
        """Execute a transaction that will potentially deadlock"""
        for table in lock_order:
            # Lock table
            if table in self.table_locks:
                # Wait for lock (potential deadlock)
                await asyncio.sleep(0.1)
            
            self.table_locks[table] = transaction.connection_id
            
            # Execute query
            query = f"SELECT * FROM {table} FOR UPDATE"
            await self._execute_query(transaction.connection_id, query, transaction.transaction_id)
            
            # Hold lock for a bit
            await asyncio.sleep(0.05)
        
        # Release locks
        for table in lock_order:
            self.table_locks.pop(table, None)
    
    async def _simulate_lock_contention(self, request: TestRequest) -> None:
        """Simulate lock contention scenarios"""
        # Create multiple transactions competing for the same resources
        contention_count = random.randint(5, 10)
        target_table = "users"
        target_row = f"user_{random.randint(1, 100)}"
        
        tasks = []
        for i in range(contention_count):
            task = self._compete_for_lock(target_table, target_row, f"contention_tx_{i}")
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _compete_for_lock(self, table: str, row: str, transaction_id: str) -> None:
        """Compete for a specific lock"""
        connection_id = await self._get_connection()
        if not connection_id:
            return
        
        transaction = TransactionState(
            transaction_id=transaction_id,
            connection_id=connection_id,
            started_at=time.time()
        )
        
        self.active_transactions[transaction_id] = transaction
        
        # Try to acquire row lock
        lock_key = f"{table}:{row}"
        
        if lock_key in self.row_locks:
            # Wait for lock to be released
            await asyncio.sleep(random.uniform(0.01, 0.1))
        
        self.row_locks[lock_key] = connection_id
        
        # Execute query
        query = f"UPDATE {table} SET last_login = NOW() WHERE id = '{row}'"
        await self._execute_query(connection_id, query, transaction_id)
        
        # Hold lock briefly
        await asyncio.sleep(0.02)
        
        # Release lock
        self.row_locks.pop(lock_key, None)
        await self._release_connection(connection_id)
    
    async def _simulate_malformed_query(self, request: TestRequest) -> None:
        """Simulate malformed query execution"""
        malformed_query = random.choice(self.malformed_queries)
        
        connection_id = await self._get_connection()
        if not connection_id:
            return
        
        # Execute malformed query
        await self._execute_query(connection_id, malformed_query)
        
        await self._release_connection(connection_id)
    
    async def _get_connection(self) -> Optional[str]:
        """Get a connection from the pool"""
        # Check if pool has available connections
        if len(self.active_connections) >= self.max_connections:
            return None
        
        # Create new connection
        connection_id = f"conn_{len(self.active_connections)}_{time.time()}"
        connection = ConnectionState(
            connection_id=connection_id,
            created_at=time.time(),
            last_used=time.time()
        )
        
        self.active_connections[connection_id] = connection
        return connection_id
    
    async def _release_connection(self, connection_id: str) -> None:
        """Release a connection back to the pool"""
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            connection.is_active = False
            del self.active_connections[connection_id]
    
    async def _use_connection(self, connection_id: str, request: TestRequest) -> None:
        """Simulate using a connection"""
        if connection_id not in self.active_connections:
            return
        
        connection = self.active_connections[connection_id]
        connection.last_used = time.time()
        connection.query_count += 1
        
        # Execute a simple query
        query = f"SELECT 1 FROM test_table WHERE request_id = '{request.id}'"
        await self._execute_query(connection_id, query)
        
        # Randomly hold connection for a bit
        if random.random() < 0.1:
            await asyncio.sleep(random.uniform(0.01, 0.05))
    
    async def _execute_query(self, connection_id: str, query: str, transaction_id: Optional[str] = None) -> bool:
        """Execute a query and return success status"""
        self.total_queries += 1
        
        # Simulate query execution time
        execution_time = random.uniform(0.001, 0.05)
        await asyncio.sleep(execution_time)
        
        # Simulate query failure based on complexity
        failure_probability = 0.05  # 5% base failure rate
        
        # Increase failure rate for malformed queries
        if any(keyword in query.upper() for keyword in ["MALFORMED", "INVALID", "CORRUPT"]):
            failure_probability = 0.8
        
        # Increase failure rate under stress
        if len(self.active_connections) > self.max_connections * 0.8:
            failure_probability += 0.2
        
        if random.random() < failure_probability:
            self.failed_queries += 1
            logger.debug("Query failed", query=query[:50], connection_id=connection_id)
            return False
        
        # Add query to transaction if provided
        if transaction_id and transaction_id in self.active_transactions:
            self.active_transactions[transaction_id].queries.append(query)
        
        return True
    
    async def _resolve_deadlocks(self) -> None:
        """Resolve deadlocks by rolling back victim transactions"""
        # Find transactions involved in deadlocks
        victim_transactions = []
        
        for transaction_id, transaction in self.active_transactions.items():
            if transaction.is_active and len(transaction.queries) > 2:
                # Simple heuristic: longer transactions are more likely to be victims
                if time.time() - transaction.started_at > 0.1:
                    victim_transactions.append(transaction_id)
        
        # Rollback victim transactions
        for transaction_id in victim_transactions[:1]:  # Rollback one victim
            if transaction_id in self.active_transactions:
                transaction = self.active_transactions[transaction_id]
                transaction.rollback_reason = "deadlock_victim"
                transaction.is_active = False
                
                # Release connection
                await self._release_connection(transaction.connection_id)
                
                logger.debug("Transaction rolled back", transaction_id=transaction_id)
    
    def _generate_malformed_queries(self) -> List[str]:
        """Generate malformed SQL queries for testing"""
        return [
            "SELECT * FROM users WHERE id = 'MALFORMED'",
            "INSERT INTO sessions VALUES (INVALID_SYNTAX)",
            "UPDATE users SET email = 'test@example.com' WHERE id = UNBALANCED_PARENTHESIS(",
            "DELETE FROM auth_tokens WHERE token = 'UNCLOSED_STRING'",
            "SELECT * FROM table_that_doesnt_exist",
            "UPDATE users SET /* UNCLOSED COMMENT",
            "SELECT * FROM users WHERE id = 1; DROP TABLE users; --",
            "INSERT INTO users (id, name) VALUES (1, 'name', EXTRA_COLUMN)",
            "SELECT * FROM users WHERE id = CONVERSION_ERROR('invalid_date')",
            "UPDATE users SET name = CHAR(128) WHERE id = 1",  # Invalid character
            "SELECT * FROM users WHERE name = x'414243'",  # Invalid hex
            "CREATE OR REPLACE FUNCTION invalid_function() RETURNS VOID AS $$ BEGIN INVALID_SYNTAX; END; $$ LANGUAGE plpgsql",
        ]
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance and stress metrics"""
        return {
            "total_queries": self.total_queries,
            "failed_queries": self.failed_queries,
            "query_success_rate": (self.total_queries - self.failed_queries) / max(self.total_queries, 1),
            "active_connections": len(self.active_connections),
            "max_connections": self.max_connections,
            "connection_utilization": len(self.active_connections) / self.max_connections,
            "active_transactions": len(self.active_transactions),
            "deadlock_count": self.deadlock_count,
            "timeout_count": self.timeout_count,
            "connection_exhaustion_count": self.connection_exhaustion_count,
            "queue_size": self.query_queue.current_size,
            "queue_utilization": self.query_queue.current_size / self.query_queue.max_size,
            "table_locks": len(self.table_locks),
            "row_locks": len(self.row_locks),
            "average_query_time": 0.025,  # Simulated average
            "connection_turnover": self._calculate_connection_turnover(),
        }
    
    def _calculate_connection_turnover(self) -> float:
        """Calculate connection turnover rate"""
        # This would normally track connections created/destroyed over time
        return len(self.active_connections) / max(self.max_connections, 1)
