import { VulnerabilityType, Severity } from '../types';

interface SinkTest {
  type: VulnerabilityType;
  payload: string;
  sink: string;
  expectedBehavior: {
    execution: boolean;
    evidence: string[];
  };
}

interface SinkConfirmationResult {
  confirmed: boolean;
  sinkReached: boolean;
  evidence: string[];
  confidence: number;
}

export class SinkConfirmation {
  async confirmSink(findings: any[]): Promise<Map<string, SinkConfirmationResult>> {
    console.log(`🎯 Starting sink confirmation for ${findings.length} findings...`);
    
    const results = new Map<string, SinkConfirmationResult>();
    
    for (const finding of findings) {
      const result = await this.confirmSingleSink(finding);
      results.set(finding.id || `${finding.path}_${finding.payload}`, result);
      
      console.log(`  🎯 ${finding.path}: ${result.confirmed ? '✅ Sink confirmed' : '❌ Sink not confirmed'} (confidence: ${(result.confidence * 100).toFixed(0)}%)`);
    }
    
    const confirmedCount = Array.from(results.values()).filter(r => r.confirmed).length;
    console.log(`📊 Sink confirmation complete: ${confirmedCount}/${findings.length} findings confirmed`);
    
    return results;
  }

  private async confirmSingleSink(finding: any): Promise<SinkConfirmationResult> {
    const evidence: string[] = [];
    let sinkReached = false;
    let confidence = 0.0;
    
    switch (finding.type) {
      case 'SQL_INJECTION':
        const sqlResult = await this.confirmSQLSink(finding);
        sinkReached = sqlResult.sinkReached;
        evidence.push(...sqlResult.evidence);
        confidence = sqlResult.confidence;
        break;
      
      case 'XSS':
        const xssResult = await this.confirmXSSSink(finding);
        sinkReached = xssResult.sinkReached;
        evidence.push(...xssResult.evidence);
        confidence = xssResult.confidence;
        break;
      
      case 'DIRECTORY_TRAVERSAL':
        const traversalResult = await this.confirmTraversalSink(finding);
        sinkReached = traversalResult.sinkReached;
        evidence.push(...traversalResult.evidence);
        confidence = traversalResult.confidence;
        break;
      
      case 'FILE_INCLUSION':
        const inclusionResult = await this.confirmInclusionSink(finding);
        sinkReached = inclusionResult.sinkReached;
        evidence.push(...inclusionResult.evidence);
        confidence = inclusionResult.confidence;
        break;
      
      default:
        evidence.push('Unknown vulnerability type - cannot confirm sink');
        confidence = 0.0;
    }
    
    const confirmed = sinkReached && confidence > 0.5;
    
    return {
      confirmed,
      sinkReached,
      evidence,
      confidence
    };
  }

  private async confirmSQLSink(finding: any): Promise<{ sinkReached: boolean; evidence: string[]; confidence: number }> {
    const evidence: string[] = [];
    let sinkReached = false;
    let confidence = 0.0;
    
    // Check for SQL execution evidence
    if (finding.evidence) {
      const evidenceText = finding.evidence.toLowerCase();
      
      // Strong evidence of SQL execution
      if (evidenceText.includes('sql error') || evidenceText.includes('mysql error') || 
          evidenceText.includes('syntax error') || evidenceText.includes('ora-')) {
        sinkReached = true;
        confidence = 0.9;
        evidence.push('SQL execution error detected - sink reached');
      }
      
      // Medium evidence
      else if (evidenceText.includes('timing anomaly') || finding.timing?.diff > 2000) {
        sinkReached = true;
        confidence = 0.7;
        evidence.push('Timing-based SQL execution detected - sink likely reached');
      }
      
      // Weak evidence
      else if (evidenceText.includes('content difference') || finding.content?.diff > 50) {
        sinkReached = true;
        confidence = 0.5;
        evidence.push('Content difference detected - sink possibly reached');
      }
    }
    
    // Check payload for SQL injection patterns
    if (finding.payload) {
      const sqlPatterns = [
        /union\s+select/i,
        /or\s+'1'='1/i,
        /and\s+sleep/i,
        /waitfor\s+delay/i,
        /pg_sleep/i,
        /benchmark/i
      ];
      
      for (const pattern of sqlPatterns) {
        if (pattern.test(finding.payload)) {
          confidence = Math.max(confidence, 0.6);
          evidence.push('SQL injection payload pattern detected');
          break;
        }
      }
    }
    
    if (!sinkReached) {
      evidence.push('No SQL execution evidence detected');
    }
    
    return { sinkReached, evidence, confidence };
  }

  private async confirmXSSSink(finding: any): Promise<{ sinkReached: boolean; evidence: string[]; confidence: number }> {
    const evidence: string[] = [];
    let sinkReached = false;
    let confidence = 0.0;
    
    // Check for XSS execution evidence
    if (finding.evidence) {
      const evidenceText = finding.evidence.toLowerCase();
      
      // Strong evidence of XSS execution
      if (evidenceText.includes('xss executed') || evidenceText.includes('script execution') ||
          evidenceText.includes('alert executed')) {
        sinkReached = true;
        confidence = 0.9;
        evidence.push('JavaScript execution detected - XSS sink reached');
      }
      
      // Medium evidence
      else if (evidenceText.includes('script tag') || evidenceText.includes('event handler') ||
                evidenceText.includes('dom reflection')) {
        sinkReached = true;
        confidence = 0.7;
        evidence.push('Script tag or event handler detected - XSS sink likely reached');
      }
      
      // Weak evidence
      else if (evidenceText.includes('payload reflection') || evidenceText.includes('direct reflection')) {
        sinkReached = true;
        confidence = 0.5;
        evidence.push('Payload reflection detected - XSS sink possibly reached');
      }
    }
    
    // Check payload for XSS patterns
    if (finding.payload) {
      const xssPatterns = [
        /<script/i,
        /onerror|onload|onfocus|onclick/i,
        /javascript:/i,
        /fromCharCode/i,
        /eval\(/i
      ];
      
      for (const pattern of xssPatterns) {
        if (pattern.test(finding.payload)) {
          confidence = Math.max(confidence, 0.6);
          evidence.push('XSS payload pattern detected');
          break;
        }
      }
    }
    
    if (!sinkReached) {
      evidence.push('No XSS execution evidence detected');
    }
    
    return { sinkReached, evidence, confidence };
  }

  private async confirmTraversalSink(finding: any): Promise<{ sinkReached: boolean; evidence: string[]; confidence: number }> {
    const evidence: string[] = [];
    let sinkReached = false;
    let confidence = 0.0;
    
    // Check for path traversal evidence
    if (finding.evidence) {
      const evidenceText = finding.evidence.toLowerCase();
      
      // Strong evidence of file system access
      if (evidenceText.includes('system file') || evidenceText.includes('file content') ||
          evidenceText.includes('hostname') || evidenceText.includes('machine-id')) {
        sinkReached = true;
        confidence = 0.9;
        evidence.push('System file content detected - file system sink reached');
      }
      
      // Medium evidence
      else if (evidenceText.includes('linux') || evidenceText.includes('windows') ||
                evidenceText.includes('root:') || evidenceText.includes('bin/bash')) {
        sinkReached = true;
        confidence = 0.7;
        evidence.push('System information detected - file system sink likely reached');
      }
      
      // Weak evidence
      else if (evidenceText.includes('file accessible') || evidenceText.length > 200) {
        sinkReached = true;
        confidence = 0.5;
        evidence.push('File content accessible - file system sink possibly reached');
      }
    }
    
    // Check payload for traversal patterns
    if (finding.payload) {
      const traversalPatterns = [
        /\.\.\//,
        /%2e%2e%2f/i,
        /etc\/passwd/i,
        /windows/i,
        /system32/i
      ];
      
      for (const pattern of traversalPatterns) {
        if (pattern.test(finding.payload)) {
          confidence = Math.max(confidence, 0.6);
          evidence.push('Path traversal payload pattern detected');
          break;
        }
      }
    }
    
    if (!sinkReached) {
      evidence.push('No file system access evidence detected');
    }
    
    return { sinkReached, evidence, confidence };
  }

  private async confirmInclusionSink(finding: any): Promise<{ sinkReached: boolean; evidence: string[]; confidence: number }> {
    const evidence: string[] = [];
    let sinkReached = false;
    let confidence = 0.0;
    
    // Check for file inclusion evidence
    if (finding.evidence) {
      const evidenceText = finding.evidence.toLowerCase();
      
      // Strong evidence of file inclusion
      if (evidenceText.includes('wrapper executed') || evidenceText.includes('php filter') ||
          evidenceText.includes('system command')) {
        sinkReached = true;
        confidence = 0.9;
        evidence.push('PHP wrapper or filter executed - file inclusion sink reached');
      }
      
      // Medium evidence
      else if (evidenceText.includes('hello world') || evidenceText.includes('base64') ||
                evidenceText.includes('uid=')) {
        sinkReached = true;
        confidence = 0.7;
        evidence.push('Decoded content or system output detected - inclusion sink likely reached');
      }
      
      // Weak evidence
      else if (evidenceText.includes('file content') || evidenceText.length > 200) {
        sinkReached = true;
        confidence = 0.5;
        evidence.push('File content detected - inclusion sink possibly reached');
      }
    }
    
    // Check payload for inclusion patterns
    if (finding.payload) {
      const inclusionPatterns = [
        /php:\/\//i,
        /data:\/\//i,
        /expect:\/\//i,
        /glob:\/\//i,
        /zip:\/\//i
      ];
      
      for (const pattern of inclusionPatterns) {
        if (pattern.test(finding.payload)) {
          confidence = Math.max(confidence, 0.6);
          evidence.push('PHP wrapper pattern detected');
          break;
        }
      }
    }
    
    if (!sinkReached) {
      evidence.push('No file inclusion evidence detected');
    }
    
    return { sinkReached, evidence, confidence };
  }

  async generateSinkReport(results: Map<string, SinkConfirmationResult>): Promise<string> {
    const confirmed = Array.from(results.values()).filter(r => r.confirmed).length;
    const total = results.size;
    const confirmationRate = total > 0 ? confirmed / total : 0;
    
    return `
========================================
SINK CONFIRMATION REPORT
========================================

📊 SUMMARY:
- Total Findings: ${total}
- Sink Confirmed: ${confirmed}
- Confirmation Rate: ${(confirmationRate * 100).toFixed(2)}%

🎯 ASSESSMENT:
${this.generateAssessment(confirmationRate)}

📋 DETAILED RESULTS:
${this.generateDetailedResults(results)}

========================================
`;
  }

  private generateAssessment(rate: number): string {
    if (rate >= 0.8) {
      return '✅ EXCELLENT - High sink confirmation rate';
    } else if (rate >= 0.6) {
      return '✅ GOOD - Acceptable sink confirmation rate';
    } else if (rate >= 0.4) {
      return '⚠️  MODERATE - Some findings not confirmed';
    } else {
      return '❌ POOR - Most findings not confirmed';
    }
  }

  private generateDetailedResults(results: Map<string, SinkConfirmationResult>): string {
    let output = '';
    
    for (const [id, result] of results.entries()) {
      output += `
${id}:
  - Confirmed: ${result.confirmed ? 'Yes' : 'No'}
  - Sink Reached: ${result.sinkReached ? 'Yes' : 'No'}
  - Confidence: ${(result.confidence * 100).toFixed(2)}%
  - Evidence: ${result.evidence.join(', ')}
`;
    }
    
    return output;
  }
}
