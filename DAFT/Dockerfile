FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY layers/ ./layers/
COPY config/ ./config/
COPY tests/ ./tests/
COPY __init__.py .
COPY main.py .
COPY setup.py .

# Copy architectural corrections
COPY core/trust_boundaries.py ./core/
COPY core/causal_topology.py ./core/
COPY core/advanced_concurrency.py ./core/
COPY core/oracle_validation.py ./core/
COPY core/architectural_corrections.py ./core/
COPY core/enterprise_architecture.py ./core/
COPY core/final_architecture.py ./core/
COPY core/epistemic_layer.py ./core/

# Create results directory
RUN mkdir -p /app/results

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV EVENT_HORIZON_TARGET=dsmoto.ru
ENV EVENT_HORIZON_MODE=security_audit
ENV EVENT_HORIZON_AUTHORIZED=true

# Expose port for monitoring (if needed)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import event_horizon" || exit 1

# Default command
CMD ["python", "main.py", "run", "--config", "config/dsmoto_audit_config.yaml", "--output", "results"]
