"""
Mock Target Service for EVENT_HORIZON Testing

A simple Flask application that simulates various authentication
and API endpoints for testing the EVENT_HORIZON framework.
"""

import time
import random
import json
from flask import Flask, request, jsonify, Response
from functools import wraps
import threading
from collections import defaultdict
import hashlib

app = Flask(__name__)

# Global state for testing
request_counts = defaultdict(int)
session_store = {}
rate_limit_store = defaultdict(list)
error_injection = {
    "enabled": False,
    "error_rate": 0.1,
    "timeout_rate": 0.05
}

# Configuration
CONFIG = {
    "port": 9000,
    "log_level": "INFO",
    "rate_limit": {
        "requests_per_minute": 60,
        "burst_size": 10
    },
    "session": {
        "timeout": 3600,  # 1 hour
        "max_sessions": 1000
    }
}


def rate_limit():
    """Simple rate limiting implementation."""
    client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
    now = time.time()
    
    # Clean old requests
    rate_limit_store[client_ip] = [
        req_time for req_time in rate_limit_store[client_ip]
        if now - req_time < 60
    ]
    
    # Check limit
    if len(rate_limit_store[client_ip]) >= CONFIG["rate_limit"]["requests_per_minute"]:
        return False
    
    # Add current request
    rate_limit_store[client_ip].append(now)
    return True


def inject_errors():
    """Inject errors based on configuration."""
    if not error_injection["enabled"]:
        return None
    
    if random.random() < error_injection["error_rate"]:
        error_types = [500, 502, 503, 504]
        return random.choice(error_types)
    
    if random.random() < error_injection["timeout_rate"]:
        time.sleep(random.uniform(5, 15))
        return 408
    
    return None


def track_request(endpoint):
    """Track request statistics."""
    request_counts[endpoint] += 1


def generate_session_id():
    """Generate a session ID."""
    return hashlib.sha256(f"{time.time()}{random.random()}".encode()).hexdigest()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "request_counts": dict(request_counts)
    })


@app.route('/login', methods=['POST'])
def login():
    """Authentication endpoint."""
    track_request('/login')
    
    # Rate limiting
    if not rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    # Error injection
    error_code = inject_errors()
    if error_code:
        return jsonify({"error": "Simulated error"}), error_code
    
    # Simulate authentication
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    
    # Simulate authentication delay
    time.sleep(random.uniform(0.1, 0.5))
    
    # Simple authentication logic
    if username.startswith('test') and password.startswith('pass'):
        session_id = generate_session_id()
        session_store[session_id] = {
            "username": username,
            "created_at": time.time(),
            "last_access": time.time()
        }
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "user": {
                "username": username,
                "role": "user"
            }
        })
    
    elif username == 'admin' and password == 'admin123':
        session_id = generate_session_id()
        session_store[session_id] = {
            "username": username,
            "created_at": time.time(),
            "last_access": time.time(),
            "role": "admin"
        }
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "user": {
                "username": username,
                "role": "admin"
            }
        })
    
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/auth/validate', methods=['GET'])
def validate_auth():
    """Validate authentication session."""
    track_request('/auth/validate')
    
    session_id = request.headers.get('Authorization') or request.args.get('session_id')
    if not session_id:
        session_id = request.cookies.get('session_id')
    
    if not session_id:
        return jsonify({"error": "No session provided"}), 401
    
    # Rate limiting
    if not rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    # Error injection
    error_code = inject_errors()
    if error_code:
        return jsonify({"error": "Simulated error"}), error_code
    
    session = session_store.get(session_id)
    if not session:
        return jsonify({"error": "Invalid session"}), 401
    
    # Check session timeout
    if time.time() - session["created_at"] > CONFIG["session"]["timeout"]:
        del session_store[session_id]
        return jsonify({"error": "Session expired"}), 401
    
    # Update last access
    session["last_access"] = time.time()
    
    return jsonify({
        "status": "valid",
        "user": {
            "username": session["username"],
            "role": session.get("role", "user")
        }
    })


@app.route('/session/create', methods=['POST'])
def create_session():
    """Create a new session."""
    track_request('/session/create')
    
    if not rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    error_code = inject_errors()
    if error_code:
        return jsonify({"error": "Simulated error"}), error_code
    
    user_id = request.form.get('user_id', str(random.randint(1, 1000)))
    session_id = generate_session_id()
    
    session_store[session_id] = {
        "user_id": user_id,
        "created_at": time.time(),
        "last_access": time.time()
    }
    
    return jsonify({
        "session_id": session_id,
        "user_id": user_id,
        "created_at": session_store[session_id]["created_at"]
    })


@app.route('/session/<session_id>', methods=['GET', 'DELETE'])
def manage_session(session_id):
    """Get or delete a session."""
    track_request(f'/session/{session_id}')
    
    if not rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    error_code = inject_errors()
    if error_code:
        return jsonify({"error": "Simulated error"}), error_code
    
    if request.method == 'GET':
        session = session_store.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({
            "session_id": session_id,
            "session_data": session
        })
    
    elif request.method == 'DELETE':
        if session_id in session_store:
            del session_store[session_id]
            return jsonify({"status": "deleted"})
        else:
            return jsonify({"error": "Session not found"}), 404


@app.route('/api/normalize', methods=['GET'])
def normalize_input():
    """Input normalization endpoint."""
    track_request('/api/normalize')
    
    if not rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    error_code = inject_errors()
    if error_code:
        return jsonify({"error": "Simulated error"}), error_code
    
    # Get input parameter
    input_text = request.args.get('input', '')
    
    # Apply various normalizations
    normalized = input_text.strip().lower()
    normalized = ' '.join(normalized.split())  # Normalize whitespace
    
    return jsonify({
        "original": input_text,
        "normalized": normalized,
        "operations": [
            "strip_whitespace",
            "lowercase",
            "normalize_spaces"
        ]
    })


@app.route('/api/query', methods=['POST'])
def execute_query():
    """Safe SQL query endpoint."""
    track_request('/api/query')
    
    if not rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    error_code = inject_errors()
    if error_code:
        return jsonify({"error": "Simulated error"}), error_code
    
    query = request.form.get('query', '')
    
    # Safe query patterns only
    safe_queries = [
        "SELECT 1",
        "SELECT 'test'",
        "SELECT 1 FROM dual",
        "SELECT (1)"
    ]
    
    if query.strip().upper() in [q.upper() for q in safe_queries]:
        return jsonify({
            "status": "success",
            "query": query,
            "result": "query_executed_safely",
            "execution_time": random.uniform(0.01, 0.1)
        })
    
    else:
        return jsonify({"error": "Query not allowed"}), 400


@app.route('/api/endpoint', methods=['GET'])
def general_endpoint():
    """General API endpoint for testing."""
    track_request('/api/endpoint')
    
    if not rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    error_code = inject_errors()
    if error_code:
        return jsonify({"error": "Simulated error"}), error_code
    
    # Simulate various response times
    response_time = random.uniform(0.1, 2.0)
    time.sleep(response_time)
    
    return jsonify({
        "message": "Request processed successfully",
        "timestamp": time.time(),
        "headers": dict(request.headers),
        "response_time": response_time
    })


@app.route('/api/data', methods=['GET'])
def data_endpoint():
    """Data endpoint for rate limiting tests."""
    track_request('/api/data')
    
    if not rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    error_code = inject_errors()
    if error_code:
        return jsonify({"error": "Simulated error"}), error_code
    
    # Simulate data processing
    data_size = random.randint(100, 10000)
    data = [{"id": i, "value": random.random()} for i in range(data_size)]
    
    return jsonify({
        "data": data,
        "count": len(data),
        "timestamp": time.time()
    })


@app.route('/admin/control', methods=['POST'])
def admin_control():
    """Admin control endpoint for error injection."""
    track_request('/admin/control')
    
    # Check for admin session
    session_id = request.headers.get('Authorization')
    session = session_store.get(session_id)
    
    if not session or session.get("role") != "admin":
        return jsonify({"error": "Admin access required"}), 403
    
    action = request.form.get('action')
    
    if action == "enable_errors":
        error_injection["enabled"] = True
        error_injection["error_rate"] = float(request.form.get('error_rate', 0.1))
        error_injection["timeout_rate"] = float(request.form.get('timeout_rate', 0.05))
        
        return jsonify({
            "status": "success",
            "error_injection": error_injection
        })
    
    elif action == "disable_errors":
        error_injection["enabled"] = False
        
        return jsonify({
            "status": "success",
            "error_injection": error_injection
        })
    
    elif action == "reset_stats":
        request_counts.clear()
        session_store.clear()
        rate_limit_store.clear()
        
        return jsonify({
            "status": "success",
            "message": "Statistics reset"
        })
    
    else:
        return jsonify({"error": "Unknown action"}), 400


@app.route('/metrics', methods=['GET'])
def metrics():
    """Metrics endpoint for monitoring."""
    return jsonify({
        "request_counts": dict(request_counts),
        "active_sessions": len(session_store),
        "rate_limit_store_size": sum(len(ips) for ips in rate_limit_store.values()),
        "error_injection": error_injection,
        "timestamp": time.time()
    })


@app.route('/simulate/load', methods=['POST'])
def simulate_load():
    """Simulate system load for testing."""
    track_request('/simulate/load')
    
    load_type = request.form.get('type', 'cpu')
    duration = float(request.form.get('duration', 10))
    intensity = float(request.form.get('intensity', 0.5))
    
    def cpu_load():
        end_time = time.time() + duration
        while time.time() < end_time:
            # CPU intensive work
            sum(i * i for i in range(1000))
            time.sleep(0.01 * (1 - intensity))
    
    def memory_load():
        # Memory intensive work
        data = []
        end_time = time.time() + duration
        while time.time() < end_time:
            data.extend([random.random() for _ in range(1000)])
            if len(data) > 100000:
                data = data[-50000:]  # Keep some data
            time.sleep(0.1 * (1 - intensity))
    
    if load_type == 'cpu':
        thread = threading.Thread(target=cpu_load)
    elif load_type == 'memory':
        thread = threading.Thread(target=memory_load)
    else:
        return jsonify({"error": "Invalid load type"}), 400
    
    thread.start()
    
    return jsonify({
        "status": "success",
        "load_type": load_type,
        "duration": duration,
        "intensity": intensity,
        "thread_id": thread.ident
    })


if __name__ == '__main__':
    print(f"Mock Target Service starting on port {CONFIG['port']}")
    print(f"Log level: {CONFIG['log_level']}")
    print("Available endpoints:")
    print("  GET  /health")
    print("  POST /login")
    print("  GET  /auth/validate")
    print("  POST /session/create")
    print("  GET  /session/<id>")
    print("  DELETE /session/<id>")
    print("  GET  /api/normalize")
    print("  POST /api/query")
    print("  GET  /api/endpoint")
    print("  GET  /api/data")
    print("  POST /admin/control")
    print("  GET  /metrics")
    print("  POST /simulate/load")
    
    app.run(
        host='0.0.0.0',
        port=CONFIG['port'],
        debug=False
    )
