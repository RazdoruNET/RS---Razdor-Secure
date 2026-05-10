# Instrumentation Layer Documentation

## Overview

The instrumentation layer (`/core/truth/instrumentation.py`) provides comprehensive monitoring and logging of real I/O operations in the SUPER_DPI_COMBINER system. It ensures that all network operations are tracked, logged, and verified for authenticity.

## Features Implemented

### ✅ Socket Operations Monitoring
- **socket.send()** - Intercepts and logs all outgoing data
- **socket.recv()** - Monitors incoming data with proper type handling
- **socket.sendall()** - Tracks bulk send operations
- **socket.recv_into()** - Handles buffer-based receive operations

### ✅ AsyncIO Streams Instrumentation
- **asyncio.StreamWriter.write()** - Logs async write operations
- **asyncio.StreamReader.read()** - Monitors async read operations

### ✅ HTTP Client Operations
- **aiohttp.ClientSession.request()** - Tracks HTTP requests/responses
- Request/response data logging
- Status code and header capture

### ✅ Real Bytes Logging
- Captures actual byte data (first 64 bytes as samples)
- Records data sizes and timestamps
- Hex representation for analysis

### ✅ System Call Logging
- Logs wrapper-level system calls
- Captures arguments, return values, and errors
- Thread-aware tracking

### ✅ Real I/O Verification
- `@require_real_io` decorator for functions
- `@async_require_real_io` for async functions
- Prevents logical successes without actual I/O

## Architecture

### Core Components

```python
IOMonitor
├── record_operation()     # Records I/O operations
├── record_syscall()       # Records system calls  
├── verify_real_io()       # Checks for real I/O
├── get_statistics()       # Returns operation stats
└── get_recent_operations() # Gets recent records

Instrumentation Functions
├── instrument_socket_send()
├── instrument_socket_recv()
├── instrument_asyncio_write()
├── instrument_asyncio_read()
├── instrument_http_request()
├── require_real_io()
└── async_require_real_io()
```

### Data Structures

```python
IOOperationRecord
├── operation_type: IOOperationType
├── timestamp: float
├── thread_id: int
├── data_size: int
├── data_bytes: bytes
├── source_location: str
├── success: bool
├── error: Optional[str]
└── metadata: Dict[str, Any]

SystemCallRecord
├── syscall_name: str
├── timestamp: float
├── thread_id: int
├── args: tuple
├── kwargs: dict
├── return_value: Any
├── success: bool
└── error: Optional[str]
```

## Usage

### Basic Usage

```python
from core.truth import enable_instrumentation, get_io_monitor

# Enable instrumentation
enable_instrumentation()

# Get monitor for statistics
monitor = get_io_monitor()
stats = monitor.get_statistics()
```

### Real I/O Requirements

```python
from core.truth import require_real_io, async_require_real_io

@require_real_io
def critical_operation():
    # This function will raise RuntimeError if no real I/O occurs
    pass

@async_require_real_io
async def async_critical_operation():
    # Async version with same verification
    pass
```

## Output Examples

### Operation Logging
```
IO_OPERATION: {
    'type': 'socket_send',
    'timestamp': 1778420697.200843,
    'thread': 140704271082304,
    'size': 40,
    'success': True,
    'location': '/path/to/instrumentation.py:249',
    'metadata': {
        'sent_bytes': 40,
        'duration': 5.5e-05
    },
    'data_sample': '474554202f20485454502f312e310d0a...'
}
```

### System Call Logging
```
SYSCALL: {
    'syscall': 'socket.send',
    'timestamp': 1778420697.201429,
    'thread': 140704271082304,
    'args': "(<socket.socket...>, b'GET / HTTP/1.1...')",
    'success': True,
    'return': '40'
}
```

## Statistics

The system provides comprehensive statistics:

```python
stats = {
    'total_operations': 25,
    'total_syscalls': 25,
    'operation_stats': {
        'socket_send': 12,
        'socket_recv': 10,
        'http_request': 2,
        'http_response': 1
    },
    'byte_stats': {
        'socket_send': 2048,
        'socket_recv': 15360,
        'http_request': 1024,
        'http_response': 4096
    },
    'error_stats': {
        'socket_recv': 2
    },
    'io_operations_in_session': True,
    'session_duration': 2.45
}
```

## Integration Points

### With BasePipeline
The instrumentation layer integrates with existing pipeline infrastructure:

```python
# In base_pipeline.py
from core.truth import async_require_real_io

@async_require_real_io
async def execute(self, request: BypassRequest) -> BypassResponse:
    # Pipeline execution with I/O verification
    pass
```

### With HTTP Client
HTTP operations are automatically instrumented:

```python
# In http_client.py
# HTTP requests are automatically logged through instrumentation
```

## Security Considerations

- **Data Privacy**: Only first 64 bytes logged as samples
- **Performance**: Minimal overhead with efficient data structures
- **Thread Safety**: All operations are thread-safe
- **Memory Management**: Configurable record limits with deque

## Testing

Run the demonstration script:

```bash
python3 demo_instrumentation.py
```

This will show:
- Real socket operations
- Byte logging
- System call tracking
- Statistics collection
- Real I/O verification

## Files Created

- `/core/truth/instrumentation.py` - Main instrumentation layer
- `/core/truth/__init__.py` - Module initialization
- `/demo_instrumentation.py` - Demonstration script
- `/test_instrumentation.py` - Comprehensive test suite

## Conclusion

The instrumentation layer successfully implements all requirements for TASK 8.1:

✅ **Socket send/recv wrapping** - Complete monitoring of socket operations  
✅ **AsyncIO streams instrumentation** - Full async operation tracking  
✅ **HTTP client monitoring** - Request/response logging  
✅ **Actual bytes logging** - Real data capture with samples  
✅ **System call logging** - Wrapper-level syscall tracking  
✅ **Real I/O verification** - Prevention of logical successes without I/O  

The system provides comprehensive visibility into all I/O operations while maintaining performance and security standards.
