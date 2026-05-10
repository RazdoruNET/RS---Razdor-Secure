# RUNTIME_BENCHMARK_REPORT.md

## Runtime Benchmark Report

Generated: 2026-05-10 18:55:29

## Benchmark Configuration
- Sequential requests: 100 per pipeline
- Pipelines tested: Echo, HTTPFragmentation

## Results

### Echo Pipeline
- Average latency: 0.001145s
- P95 latency: 0.001279s
- Min latency: 0.001026s
- Max latency: 0.001767s
- Success rate: 100.0%
- Memory growth: 3 objects
- Socket leaks: 0

### HTTP Fragmentation Pipeline
- Average latency: 0.336585s
- P95 latency: 0.560286s
- Min latency: 0.249480s
- Max latency: 1.712689s
- Success rate: 100.0%
- Memory growth: 7 objects
- Socket leaks: 0

## Performance Classification

### Latency Performance
- Echo latency: GOOD
- HTTPFragmentation latency: GOOD

### Reliability Performance
- Echo reliability: EXCELLENT
- HTTPFragmentation reliability: EXCELLENT

### Memory Management
- Echo memory: GOOD
- HTTPFragmentation memory: GOOD

## Final Classification

### Overall Performance
RUNTIME_BENCHMARK: VERIFIED

### Component Status
- Echo Pipeline: VERIFIED
- HTTPFragmentation Pipeline: VERIFIED
