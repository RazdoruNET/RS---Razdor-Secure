# Truth Storage Layer Documentation

## Overview

The Truth Storage Layer is a SQLite-based storage system for execution results in the SUPER_DPI_COMBINER project. It provides persistent storage, querying capabilities, and comprehensive analytics for pipeline execution results.

## Features

### Core Functionality
- **SQLite Backend**: Efficient, ACID-compliant storage with full-text search capabilities
- **Thread-Safe Operations**: Concurrent access support with proper locking mechanisms
- **Comprehensive Data Model**: Stores execution metadata, I/O statistics, and verification results
- **Query Interface**: Flexible querying by pipeline, success status, network verification, and simulation flags
- **Statistics & Analytics**: Built-in analytics for pipeline performance and success rates
- **Export Functionality**: JSONL export for data analysis and backup
- **Cleanup Management**: Automatic cleanup of old data with configurable retention policies

### Data Schema

The storage layer stores the following fields for each execution:

```python
@dataclass
class ExecutionResult:
    execution_id: str          # Unique identifier
    pipeline: str             # Pipeline name
    success: bool             # Execution success status
    network_verified: bool    # Real network operations verification
    simulation_flag: bool     # Simulation mode detection
    timestamp: float          # Execution timestamp
    metadata: Dict[str, Any]  # Additional metadata
    io_operations_count: int  # Number of I/O operations
    execution_duration: float # Execution time in seconds
    error_message: Optional[str]  # Error details if failed
```

## Architecture

### Core Components

1. **TruthStorage** (`core/truth/storage.py`)
   - Main storage implementation with SQLite backend
   - CRUD operations for execution results
   - Query methods and statistics calculation
   - Export and cleanup functionality

2. **TruthStorageInterface** (`core/truth/storage_interface.py`)
   - Integration layer with pipeline wrapper
   - Automatic metadata extraction from execution traces
   - Pipeline-specific statistics
   - Auto-store decorator for functions

3. **ExecutionResult** (`core/truth/storage.py`)
   - Data model for execution results
   - Serialization/deserialization support
   - Validation and type safety

### Integration Points

- **Pipeline Wrapper**: Automatic storage of execution traces
- **Instrumentation Layer**: I/O operation statistics integration
- **Network Reality Verifier**: Real network operation verification
- **Simulation Detector**: Simulation mode detection

## Usage Examples

### Basic Storage Operations

```python
from core.truth.storage import TruthStorage, create_execution_result

# Create storage instance
storage = TruthStorage("execution_results.db")

# Create execution result
result = create_execution_result(
    execution_id="exec_001",
    pipeline="http_bypass",
    success=True,
    network_verified=True,
    simulation_flag=False,
    metadata={"target": "example.com", "technique": "domain_fronting"},
    io_operations_count=8,
    execution_duration=2.5
)

# Store result
storage.store_execution(result)

# Retrieve result
retrieved = storage.get_execution("exec_001")
```

### Query Operations

```python
# Get successful executions
successful = storage.get_successful_executions()

# Get network verified executions
network_verified = storage.get_network_verified_executions()

# Get simulation executions
simulation = storage.get_simulation_executions()

# Get pipeline-specific results
pipeline_results = storage.get_executions_by_pipeline("http_bypass")
```

### Statistics and Analytics

```python
# Get overall statistics
stats = storage.get_statistics()
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Network verification rate: {stats['network_verification_rate']:.2%}")

# Pipeline-specific statistics
for pipeline_stat in stats['pipeline_statistics']:
    print(f"{pipeline_stat['pipeline']}: {pipeline_stat['success_rate']:.2%}")
```

### Integration with Pipeline Wrapper

```python
from core.truth.storage_interface import TruthStorageInterface

# Create interface
interface = TruthStorageInterface("execution_results.db")

# Store execution trace
interface.store_trace(execution_trace)

# Get execution summary
summary = interface.get_execution_summary("trace_001")

# Get pipeline statistics
pipeline_stats = interface.get_pipeline_statistics("http_bypass")
```

### Auto-Store Decorator

```python
from core.truth.storage_interface import auto_store_execution

@auto_store_execution("execution_results.db")
def bypass_function(target_url, technique):
    # Function implementation
    # Results automatically stored
    pass
```

### Export Functionality

```python
# Export all data to JSONL
storage.export_to_jsonl("all_executions.jsonl")

# Export specific pipeline
storage.export_to_jsonl("http_bypass.jsonl", "http_bypass")
```

### Cleanup Operations

```python
# Clean up old data (older than 30 days)
deleted_count = storage.cleanup_old_executions(days_old=30)
print(f"Cleaned up {deleted_count} old executions")
```

## Database Schema

```sql
CREATE TABLE execution_results (
    execution_id TEXT PRIMARY KEY,
    pipeline TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    network_verified BOOLEAN NOT NULL,
    simulation_flag BOOLEAN NOT NULL,
    timestamp REAL NOT NULL,
    metadata TEXT,
    io_operations_count INTEGER DEFAULT 0,
    execution_duration REAL DEFAULT 0.0,
    error_message TEXT
);

-- Indexes for performance
CREATE INDEX idx_pipeline ON execution_results(pipeline);
CREATE INDEX idx_timestamp ON execution_results(timestamp);
CREATE INDEX idx_success ON execution_results(success);
CREATE INDEX idx_network_verified ON execution_results(network_verified);
```

## Performance Considerations

### Indexing Strategy
- Primary key on `execution_id` for fast lookups
- Index on `pipeline` for efficient pipeline-specific queries
- Index on `timestamp` for time-based queries and cleanup
- Index on `success` and `network_verified` for filtered queries

### Concurrency
- Thread-safe operations with SQLite locking
- Connection pooling for high-throughput scenarios
- Atomic transactions for data consistency

### Storage Optimization
- JSON metadata for flexible schema evolution
- Efficient binary storage for large data
- Configurable cleanup policies for storage management

## Testing

The implementation includes comprehensive tests covering:

- Basic CRUD operations
- Query functionality
- Interface integration
- Export functionality
- Auto-store decorator
- Cleanup operations
- Thread safety

Run tests with:
```bash
python3 test_truth_storage.py
```

## Demonstration

A complete demonstration is available showing all features:

```bash
python3 demo_truth_storage.py
```

## Configuration

### Database Configuration
```python
# Custom database path
storage = TruthStorage("/path/to/custom.db")

# In-memory database for testing
storage = TruthStorage(":memory:")
```

### Cleanup Configuration
```python
# Custom cleanup policy
deleted = storage.cleanup_old_executions(days_old=90)
```

### Export Configuration
```python
# Custom export with filtering
storage.export_to_jsonl("output.jsonl", pipeline="http_bypass")
```

## Security Considerations

- SQLite file permissions should be properly configured
- Database connections use parameterized queries to prevent SQL injection
- Metadata validation ensures data integrity
- Error handling prevents information leakage

## Future Enhancements

### Planned Features
- **Time-series Analysis**: Advanced temporal analytics
- **Performance Metrics**: Detailed performance tracking
- **Alerting System**: Automatic failure detection and notification
- **Data Retention Policies**: Advanced retention management
- **Backup & Recovery**: Automated backup and recovery systems

### Scalability Options
- **PostgreSQL Migration**: Option for PostgreSQL backend
- **Distributed Storage**: Multi-node storage support
- **Caching Layer**: Redis caching for frequent queries
- **Data Partitioning**: Time-based partitioning for large datasets

## Troubleshooting

### Common Issues

1. **Database Lock Errors**
   - Ensure proper connection management
   - Use connection pooling for high concurrency

2. **Performance Issues**
   - Check index usage with EXPLAIN QUERY PLAN
   - Consider database optimization (VACUUM, ANALYZE)

3. **Storage Growth**
   - Implement regular cleanup policies
   - Monitor database size and growth rate

### Debug Information

Enable debug logging:
```python
import logging
logging.getLogger("truth_storage").setLevel(logging.DEBUG)
```

## API Reference

### TruthStorage Class

#### Methods
- `store_execution(result: ExecutionResult) -> bool`
- `get_execution(execution_id: str) -> Optional[ExecutionResult]`
- `get_executions_by_pipeline(pipeline: str, limit: int = 100) -> List[ExecutionResult]`
- `get_recent_executions(limit: int = 50) -> List[ExecutionResult]`
- `get_successful_executions(pipeline: Optional[str] = None, limit: int = 100) -> List[ExecutionResult]`
- `get_network_verified_executions(limit: int = 100) -> List[ExecutionResult]`
- `get_simulation_executions(limit: int = 100) -> List[ExecutionResult]`
- `get_statistics() -> Dict[str, Any]`
- `delete_execution(execution_id: str) -> bool`
- `cleanup_old_executions(days_old: int = 30) -> int`
- `export_to_jsonl(output_path: str, pipeline: Optional[str] = None) -> bool`

### TruthStorageInterface Class

#### Methods
- `store_trace(trace: ExecutionTrace) -> bool`
- `get_execution_summary(execution_id: str) -> Optional[Dict[str, Any]]`
- `get_pipeline_statistics(pipeline: str) -> Dict[str, Any]`
- `export_pipeline_data(pipeline: str, output_path: str) -> bool`
- `cleanup_old_data(days_old: int = 30) -> int`

### Decorators

- `@auto_store_execution(db_path: str = "truth_storage.db")`

## Conclusion

The Truth Storage Layer provides a robust, scalable, and feature-rich solution for storing and analyzing pipeline execution results. It integrates seamlessly with the existing SUPER_DPI_COMBINER architecture while providing comprehensive analytics and management capabilities.

The implementation follows best practices for:
- Data integrity and consistency
- Performance and scalability
- Security and reliability
- Maintainability and extensibility

This storage layer serves as the foundation for advanced pipeline analytics, monitoring, and optimization in the SUPER_DPI_COMBINER ecosystem.
