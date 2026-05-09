# Multi-stage build for Prophecy Sandbox
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY src/ ./src/

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS production

# Install system dependencies for sandbox
RUN apk add --no-cache \
    docker \
    docker-cli \
    python3 \
    nodejs \
    npm \
    gcc \
    g++ \
    make \
    bash \
    strace \
    procps \
    coreutils \
    curl

# Create non-root user
RUN addgroup -g 1001 -S prophecy && \
    adduser -S prophecy -u 1001 -G prophecy

# Set working directory
WORKDIR /app

# Copy built application
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package*.json ./

# Create necessary directories
RUN mkdir -p /app/.prophecy-sandbox /app/logs /tmp/prophecy-sandbox && \
    chown -R prophecy:prophecy /app

# Copy monitoring script
COPY src/prophecy-sandbox/sandbox/monitoring.sh /usr/local/bin/monitoring.sh
RUN chmod +x /usr/local/bin/monitoring.sh

# Switch to non-root user
USER prophecy

# Expose ports
EXPOSE 3000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node dist/prophecy-sandbox/cli/CLIInterface.js system status || exit 1

# Default command
CMD ["node", "dist/prophecy-sandbox/ProphecySandbox.js"]
