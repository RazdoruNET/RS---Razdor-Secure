# System Truth Report

Generated: 2026-05-10 14:01:35 UTC

## 🎯 System Overview

**REALITY_SCORE**: 0.0%
**SIMULATION_RATIO**: 1.000

### Execution Statistics
- **Total Runs**: 3
- **Network Verified**: 0
- **Simulation Detected**: 3
- **Failed**: 0

### Success Rate Real
0.0%

---

## 📊 Pipeline Breakdown

### DNS_Tunnel

**Executed**: 2
**Network Verified**: 0
**Simulation Detected**: 2
**Reality Score**: 0.0%
**Simulation Ratio**: 1.000

### HTTPFragmentation

**Executed**: 1
**Network Verified**: 0
**Simulation Detected**: 1
**Reality Score**: 0.0%
**Simulation Ratio**: 1.000

## 🕐 Recent Runs (Last 10)

🎭 **HTTPFragmentation** - simulation_detected (0.001s)
   Reason: no network syscall observed

🎭 **DNS_Tunnel** - simulation_detected (0.000s)
   Reason: no network syscall observed

🎭 **DNS_Tunnel** - simulation_detected (0.000s)
   Reason: no network syscall observed


---

## 🧬 Metrics Formula

```
REALITY_SCORE = (network_verified_runs / total_runs) * 100
SIMULATION_RATIO = simulated_runs / total_runs
```

## 📝 Notes

- **Network Verified**: Real network operations confirmed by OS-level verification
- **Simulation Detected**: Pipeline execution patterns indicate simulation/mock behavior  
- **Failed**: Pipeline execution failed or returned error
- **Reality Score**: Percentage of runs with verified real network operations
- **Simulation Ratio**: Ratio of simulated runs to total runs

*This report is generated automatically by the Truth-Based Metrics Engine*
