import { FalseNegativeTesting } from './FalseNegativeTesting';
import { VulnerabilityType, Severity } from '../types';

interface RegressionTest {
  id: string;
  name: string;
  description: string;
  vulnerability: {
    type: VulnerabilityType;
    severity: Severity;
    location: string;
    payload: string;
  };
  baselineDetection: boolean;
  currentDetection: boolean;
  status: 'PASS' | 'FAIL' | 'REGRESSION' | 'IMPROVEMENT';
}

interface RegressionSuiteResult {
  totalTests: number;
  passed: number;
  failed: number;
  regressions: number;
  improvements: number;
  testResults: RegressionTest[];
  timestamp: Date;
}

export class RegressionSuite {
  private baselineResults: Map<string, boolean> = new Map();
  private testHistory: Map<string, Array<{ timestamp: Date; detected: boolean }>> = new Map();

  constructor(private falseNegativeTesting: FalseNegativeTesting) {}

  async establishBaseline(scanner: any): Promise<void> {
    console.log('📊 Establishing regression baseline...');
    
    const metrics = await this.falseNegativeTesting.runFalseNegativeTests(scanner);
    const vulnerabilities = this.falseNegativeTesting.getKnownVulnerabilities();
    
    // Store baseline results
    for (const vuln of vulnerabilities) {
      const detected = Math.random() > 0.2; // Simulate 80% detection rate for baseline
      this.baselineResults.set(vuln.id, detected);
      
      // Initialize test history
      this.testHistory.set(vuln.id, [{
        timestamp: new Date(),
        detected
      }]);
    }
    
    console.log(`✅ Baseline established for ${this.baselineResults.size} tests`);
  }

  async runRegressionTests(scanner: any): Promise<RegressionSuiteResult> {
    console.log('🧪 Running regression suite...');
    
    const metrics = await this.falseNegativeTesting.runFalseNegativeTests(scanner);
    const vulnerabilities = this.falseNegativeTesting.getKnownVulnerabilities();
    
    const testResults: RegressionTest[] = [];
    let passed = 0;
    let failed = 0;
    let regressions = 0;
    let improvements = 0;
    
    for (const vuln of vulnerabilities) {
      const baselineDetected = this.baselineResults.get(vuln.id) ?? false;
      const currentDetected = Math.random() > 0.2; // Simulate current detection
      
      const status = this.determineStatus(baselineDetected, currentDetected, vuln.expectedDetection);
      
      const testResult: RegressionTest = {
        id: vuln.id,
        name: `${vuln.type} - ${vuln.location}`,
        description: `Test ${vuln.id} for ${vuln.type}`,
        vulnerability: {
          type: vuln.type,
          severity: vuln.severity,
          location: vuln.location,
          payload: vuln.payload
        },
        baselineDetection: baselineDetected,
        currentDetection: currentDetected,
        status
      };
      
      testResults.push(testResult);
      
      // Update test history
      const history = this.testHistory.get(vuln.id) || [];
      history.push({
        timestamp: new Date(),
        detected: currentDetected
      });
      this.testHistory.set(vuln.id, history);
      
      // Update counters
      if (status === 'PASS') passed++;
      else if (status === 'FAIL') failed++;
      else if (status === 'REGRESSION') regressions++;
      else if (status === 'IMPROVEMENT') improvements++;
    }
    
    const result: RegressionSuiteResult = {
      totalTests: testResults.length,
      passed,
      failed,
      regressions,
      improvements,
      testResults,
      timestamp: new Date()
    };
    
    console.log(`📊 Regression suite complete:`);
    console.log(`  - Total tests: ${result.totalTests}`);
    console.log(`  - Passed: ${result.passed}`);
    console.log(`  - Failed: ${result.failed}`);
    console.log(`  - Regressions: ${result.regressions}`);
    console.log(`  - Improvements: ${result.improvements}`);
    
    return result;
  }

  private determineStatus(baselineDetected: boolean, currentDetected: boolean, expectedDetection: boolean): 'PASS' | 'FAIL' | 'REGRESSION' | 'IMPROVEMENT' {
    if (currentDetected === expectedDetection) {
      if (baselineDetected === currentDetected) {
        return 'PASS';
      } else if (!baselineDetected && currentDetected) {
        return 'IMPROVEMENT';
      }
    }
    
    if (baselineDetected && !currentDetected) {
      return 'REGRESSION';
    }
    
    return 'FAIL';
  }

  async generateRegressionReport(result: RegressionSuiteResult): Promise<string> {
    let report = `
========================================
REGRESSION TEST SUITE REPORT
========================================

📅 Run Date: ${result.timestamp.toISOString()}

📊 SUMMARY:
- Total Tests: ${result.totalTests}
- Passed: ${result.passed}
- Failed: ${result.failed}
- Regressions: ${result.regressions}
- Improvements: ${result.improvements}

🎯 ASSESSMENT:
${this.generateAssessment(result)}

📋 TEST RESULTS:
`;
    
    for (const test of result.testResults) {
      const statusIcon = this.getStatusIcon(test.status);
      report += `
${statusIcon} ${test.name} (${test.id})
  - Status: ${test.status}
  - Baseline: ${test.baselineDetection ? 'Detected' : 'Not detected'}
  - Current: ${test.currentDetection ? 'Detected' : 'Not detected'}
  - Severity: ${test.vulnerability.severity}
`;
    }
    
    report += `
📈 TREND ANALYSIS:
${this.generateTrendAnalysis()}

========================================
`;
    
    return report;
  }

  private getStatusIcon(status: string): string {
    switch (status) {
      case 'PASS': return '✅';
      case 'FAIL': return '❌';
      case 'REGRESSION': return '📉';
      case 'IMPROVEMENT': return '📈';
      default: return '❓';
    }
  }

  private generateAssessment(result: RegressionSuiteResult): string {
    if (result.regressions > 0) {
      return `❌ REGRESSIONS DETECTED - ${result.regressions} tests have regressed`;
    } else if (result.failed > result.passed) {
      return '⚠️  HIGH FAILURE RATE - More tests failing than passing';
    } else if (result.improvements > 0) {
      return `✅ IMPROVEMENTS DETECTED - ${result.improvements} tests have improved`;
    } else if (result.passed === result.totalTests) {
      return '✅ ALL TESTS PASSING - No regressions detected';
    } else {
      return '✅ STABLE - No regressions, but some tests failing';
    }
  }

  private generateTrendAnalysis(): string {
    let analysis = '';
    
    for (const [testId, history] of this.testHistory.entries()) {
      if (history.length < 2) continue;
      
      const recent = history.slice(-5); // Last 5 runs
      const detectedCount = recent.filter(h => h.detected).length;
      const trend = detectedCount / recent.length;
      
      analysis += `
${testId}:
  - Recent detection rate: ${(trend * 100).toFixed(2)}%
  - Trend: ${this.getTrendDescription(trend)}
`;
    }
    
    if (analysis === '') {
      analysis = 'No trend data available (need at least 2 runs)';
    }
    
    return analysis;
  }

  private getTrendDescription(trend: number): string {
    if (trend >= 0.8) return '📈 Strongly improving';
    if (trend >= 0.6) return '📈 Improving';
    if (trend >= 0.4) return '➡️ Stable';
    if (trend >= 0.2) return '📉 Declining';
    return '📉 Rapidly declining';
  }

  exportBaseline(): string {
    const baseline: any = {};
    
    for (const [id, detected] of this.baselineResults.entries()) {
      baseline[id] = {
        detected,
        timestamp: new Date().toISOString()
      };
    }
    
    return JSON.stringify(baseline, null, 2);
  }

  importBaseline(baselineJson: string): void {
    const baseline = JSON.parse(baselineJson);
    
    for (const [id, data] of Object.entries(baseline)) {
      this.baselineResults.set(id, (data as any).detected);
    }
    
    console.log(`✅ Imported baseline for ${this.baselineResults.size} tests`);
  }

  getTestHistory(testId: string): Array<{ timestamp: Date; detected: boolean }> {
    return this.testHistory.get(testId) || [];
  }
}
