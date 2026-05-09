import OpenAI from 'openai';
import {
  SQLQuery,
  Vulnerability,
  VulnerabilityType,
  Severity,
  VulnerabilityCategory,
  AnalysisContext,
  GPTAnalysisRequest,
  GPTAnalysisResponse,
  AppConfig
} from '../types';

export class GPTAnalyzer {
  private config: AppConfig;
  private openai: OpenAI | null = null;

  constructor(config: AppConfig) {
    this.config = config;
    if (config.enableGPTAnalysis && process.env.OPENAI_API_KEY) {
      this.openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY
      });
    }
  }

  async analyze(
    queries: SQLQuery[],
    context: AnalysisContext,
    staticVulnerabilities: Vulnerability[]
  ): Promise<Vulnerability[]> {
    if (!this.openai) {
      console.warn('OpenAI not configured, skipping GPT analysis');
      return [];
    }

    const vulnerabilities: Vulnerability[] = [];

    for (const query of queries) {
      try {
        const gptVulnerabilities = await this.analyzeQuery(query, context, staticVulnerabilities);
        vulnerabilities.push(...gptVulnerabilities);
      } catch (error) {
        console.warn(`GPT analysis failed for query ${query.id}:`, error);
      }
    }

    return vulnerabilities;
  }

  private async analyzeQuery(
    query: SQLQuery,
    context: AnalysisContext,
    staticVulnerabilities: Vulnerability[]
  ): Promise<Vulnerability[]> {
    const request: GPTAnalysisRequest = {
      query,
      context,
      vulnerabilities: staticVulnerabilities.filter(v => 
        v.filePath === query.filePath && v.line === query.line
      )
    };

    const response = await this.performGPTAnalysis(request);
    return this.convertGPTResponseToVulnerabilities(request, response);
  }

  private async performGPTAnalysis(request: GPTAnalysisRequest): Promise<GPTAnalysisResponse> {
    if (!this.openai) {
      throw new Error('OpenAI not configured');
    }

    const prompt = this.buildAnalysisPrompt(request);

    try {
      const completion = await this.openai.chat.completions.create({
        model: 'gpt-4',
        messages: [
          {
            role: 'system',
            content: this.getSystemPrompt()
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 1500
      });

      const response = completion.choices[0]?.message?.content;
      if (!response) {
        throw new Error('No response from GPT');
      }

      return this.parseGPTResponse(response);
    } catch (error) {
      throw new Error(`GPT analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private getSystemPrompt(): string {
    return `You are an expert SQL security analyst with deep knowledge of:
- SQL injection vulnerabilities and prevention techniques
- Database performance optimization
- SQL best practices and coding standards
- OWASP security guidelines
- Database-specific security considerations for MySQL, PostgreSQL, MSSQL, and Oracle

Analyze the provided SQL query for security vulnerabilities, performance issues, and best practice violations. 
Focus on identifying issues that static analysis might miss, such as:
- Business logic vulnerabilities
- Context-specific security risks
- Semantic issues in the query logic
- Performance implications based on query structure
- Data privacy and compliance issues

Provide your analysis in JSON format with the following structure:
{
  "semanticAnalysis": "Detailed semantic analysis of the query",
  "businessLogic": "Analysis of business logic implications",
  "risks": ["List of identified risks"],
  "recommendations": ["List of specific recommendations"],
  "confidence": 0.8
}`;
  }

  private buildAnalysisPrompt(request: GPTAnalysisRequest): string {
    const { query, context, vulnerabilities } = request;

    return `Please analyze the following SQL query for security vulnerabilities, performance issues, and best practice violations.

**Query Details:**
- Type: ${query.type}
- Database: ${query.database}
- File: ${query.filePath}:${query.line}
- SQL: \`\`\`sql
${query.text}
\`\`\`

**Context:**
- Application context: ${context.applicationContext ? 'Available' : 'Not provided'}
- Database metadata: ${context.metadata ? 'Available' : 'Not provided'}

**Static Analysis Results:**
${vulnerabilities.length > 0 ? 
  vulnerabilities.map(v => `- ${v.type}: ${v.description}`).join('\n') : 
  'No static analysis vulnerabilities found'
}

**Analysis Requirements:**
1. Identify security vulnerabilities beyond basic SQL injection patterns
2. Analyze performance implications
3. Check for business logic flaws
4. Identify data privacy concerns
5. Suggest specific improvements
6. Provide confidence level for each finding

Focus on semantic analysis that goes beyond pattern matching.`;
  }

  private parseGPTResponse(response: string): GPTAnalysisResponse {
    try {
      // Try to parse as JSON first
      const jsonMatch = response.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch (error) {
      // If JSON parsing fails, create a structured response from text
      console.warn('Failed to parse GPT response as JSON, creating structured response');
    }

    // Fallback: parse text response
    return {
      semanticAnalysis: response.substring(0, 500),
      businessLogic: response.substring(500, 1000),
      risks: this.extractRisks(response),
      recommendations: this.extractRecommendations(response),
      confidence: 0.6
    };
  }

  private extractRisks(response: string): string[] {
    const risks: string[] = [];
    const riskPatterns = [
      /risk:\s*(.*?)(?=\n|$)/gi,
      /vulnerability:\s*(.*?)(?=\n|$)/gi,
      /issue:\s*(.*?)(?=\n|$)/gi
    ];

    for (const pattern of riskPatterns) {
      const matches = response.match(pattern);
      if (matches) {
        risks.push(...matches.map(m => m.replace(/^(risk|vulnerability|issue):\s*/i, '').trim()));
      }
    }

    return risks.slice(0, 5); // Limit to top 5 risks
  }

  private extractRecommendations(response: string): string[] {
    const recommendations: string[] = [];
    const recommendationPatterns = [
      /recommendation:\s*(.*?)(?=\n|$)/gi,
      /suggestion:\s*(.*?)(?=\n|$)/gi,
      /fix:\s*(.*?)(?=\n|$)/gi
    ];

    for (const pattern of recommendationPatterns) {
      const matches = response.match(pattern);
      if (matches) {
        recommendations.push(...matches.map(m => m.replace(/^(recommendation|suggestion|fix):\s*/i, '').trim()));
      }
    }

    return recommendations.slice(0, 5); // Limit to top 5 recommendations
  }

  private convertGPTResponseToVulnerabilities(
    request: GPTAnalysisRequest,
    response: GPTAnalysisResponse
  ): Vulnerability[] {
    const vulnerabilities: Vulnerability[] = [];
    const { query } = request;

    // Convert risks to vulnerabilities
    response.risks.forEach((risk, index) => {
      const vulnerability = this.createGPTVulnerability(
        query,
        risk,
        response.recommendations[index] || response.recommendations[0] || 'Review and fix the identified issue',
        response.confidence
      );
      vulnerabilities.push(vulnerability);
    });

    return vulnerabilities;
  }

  private createGPTVulnerability(
    query: SQLQuery,
    risk: string,
    recommendation: string,
    confidence: number
  ): Vulnerability {
    const vulnerabilityType = this.classifyVulnerabilityType(risk);
    const severity = this.classifySeverity(risk);
    const category = this.classifyCategory(risk);

    return {
      id: `gpt_${query.id}_${Math.random().toString(36).substr(2, 9)}`,
      type: vulnerabilityType,
      severity,
      title: 'GPT Analysis Finding',
      description: risk,
      recommendation,
      line: query.line,
      column: query.column,
      filePath: query.filePath,
      sqlQuery: query.text,
      confidence,
      category,
      cwe: this.mapToCWE(vulnerabilityType),
      owasp: this.mapToOWASP(vulnerabilityType)
    };
  }

  private classifyVulnerabilityType(risk: string): VulnerabilityType {
    const lowerRisk = risk.toLowerCase();

    if (lowerRisk.includes('injection') || lowerRisk.includes('sql injection')) {
      return VulnerabilityType.SQL_INJECTION;
    }
    if (lowerRisk.includes('performance') || lowerRisk.includes('slow') || lowerRisk.includes('efficient')) {
      return VulnerabilityType.PERFORMANCE_ISSUE;
    }
    if (lowerRisk.includes('logic') || lowerRisk.includes('condition') || lowerRisk.includes('join')) {
      return VulnerabilityType.LOGIC_ERROR;
    }
    if (lowerRisk.includes('data') || lowerRisk.includes('sensitive') || lowerRisk.includes('exposure')) {
      return VulnerabilityType.DATA_EXPOSURE;
    }
    if (lowerRisk.includes('permission') || lowerRisk.includes('access') || lowerRisk.includes('privilege')) {
      return VulnerabilityType.PERMISSION_ISSUE;
    }
    if (lowerRisk.includes('insecure') || lowerRisk.includes('unsafe')) {
      return VulnerabilityType.INSECURE_OPERATION;
    }

    return VulnerabilityType.BEST_PRACTICE_VIOLATION;
  }

  private classifySeverity(risk: string): Severity {
    const lowerRisk = risk.toLowerCase();

    if (lowerRisk.includes('critical') || lowerRisk.includes('severe') || lowerRisk.includes('dangerous')) {
      return Severity.CRITICAL;
    }
    if (lowerRisk.includes('high') || lowerRisk.includes('important') || lowerRisk.includes('major')) {
      return Severity.HIGH;
    }
    if (lowerRisk.includes('medium') || lowerRisk.includes('moderate')) {
      return Severity.MEDIUM;
    }
    if (lowerRisk.includes('low') || lowerRisk.includes('minor')) {
      return Severity.LOW;
    }

    return Severity.MEDIUM; // Default to medium
  }

  private classifyCategory(risk: string): VulnerabilityCategory {
    const lowerRisk = risk.toLowerCase();

    if (lowerRisk.includes('security') || lowerRisk.includes('injection') || lowerRisk.includes('vulnerability')) {
      return VulnerabilityCategory.SECURITY;
    }
    if (lowerRisk.includes('performance') || lowerRisk.includes('slow') || lowerRisk.includes('efficient')) {
      return VulnerabilityCategory.PERFORMANCE;
    }
    if (lowerRisk.includes('maintain') || lowerRisk.includes('readability') || lowerRisk.includes('standard')) {
      return VulnerabilityCategory.MAINTAINABILITY;
    }
    if (lowerRisk.includes('reliable') || lowerRisk.includes('error') || lowerRisk.includes('failure')) {
      return VulnerabilityCategory.RELIABILITY;
    }

    return VulnerabilityCategory.BEST_PRACTICE_VIOLATION;
  }

  private mapToCWE(vulnerabilityType: VulnerabilityType): string | undefined {
    const cweMapping: Record<VulnerabilityType, string> = {
      [VulnerabilityType.SQL_INJECTION]: 'CWE-89',
      [VulnerabilityType.PERFORMANCE_ISSUE]: 'CWE-1050',
      [VulnerabilityType.BEST_PRACTICE_VIOLATION]: 'CWE-1058',
      [VulnerabilityType.LOGIC_ERROR]: 'CWE-480',
      [VulnerabilityType.DATA_EXPOSURE]: 'CWE-200',
      [VulnerabilityType.PERMISSION_ISSUE]: 'CWE-862',
      [VulnerabilityType.INSECURE_OPERATION]: 'CWE-319'
    };

    return cweMapping[vulnerabilityType];
  }

  private mapToOWASP(vulnerabilityType: VulnerabilityType): string | undefined {
    const owaspMapping: Record<VulnerabilityType, string> = {
      [VulnerabilityType.SQL_INJECTION]: 'A03:2021 – Injection',
      [VulnerabilityType.DATA_EXPOSURE]: 'A02:2021 – Cryptographic Failures',
      [VulnerabilityType.INSECURE_OPERATION]: 'A05:2021 – Security Misconfiguration',
      [VulnerabilityType.PERMISSION_ISSUE]: 'A01:2021 – Broken Access Control',
      [VulnerabilityType.PERFORMANCE_ISSUE]: 'A05:2021 – Security Misconfiguration',
      [VulnerabilityType.BEST_PRACTICE_VIOLATION]: 'A05:2021 – Security Misconfiguration',
      [VulnerabilityType.LOGIC_ERROR]: 'A01:2021 – Broken Access Control'
    };

    return owaspMapping[vulnerabilityType];
  }

  // Method to analyze query complexity for performance insights
  private analyzeQueryComplexity(query: SQLQuery): number {
    let complexity = 1;

    // Add complexity for joins
    const joinCount = (query.text.match(/join/gi) || []).length;
    complexity += joinCount * 2;

    // Add complexity for subqueries
    const subqueryCount = (query.text.match(/\(.*select/gi) || []).length;
    complexity += subqueryCount * 3;

    // Add complexity for aggregate functions
    const aggregateCount = (query.text.match(/\b(count|sum|avg|min|max)\b/gi) || []).length;
    complexity += aggregateCount;

    // Add complexity for window functions
    const windowCount = (query.text.match(/over\s*\(/gi) || []).length;
    complexity += windowCount * 2;

    return complexity;
  }

  // Method to check for data privacy compliance
  private checkDataPrivacy(query: SQLQuery): string[] {
    const privacyIssues: string[] = [];
    const sql = query.text.toLowerCase();

    // Check for PII patterns
    const piiPatterns = [
      'ssn', 'social_security', 'credit_card', 'cc_number', 'bank_account',
      'email', 'phone', 'address', 'dob', 'date_of_birth'
    ];

    for (const pattern of piiPatterns) {
      if (sql.includes(pattern)) {
        privacyIssues.push(`Potential PII exposure: ${pattern}`);
      }
    }

    // Check for encryption requirements
    if (sql.includes('password') && !sql.includes('encrypt')) {
      privacyIssues.push('Password field should be encrypted');
    }

    return privacyIssues;
  }

  // Method to analyze business logic implications
  private analyzeBusinessLogic(query: SQLQuery): string[] {
    const logicIssues: string[] = [];
    const sql = query.text.toLowerCase();

    // Check for potential business logic flaws
    if (sql.includes('delete') && !sql.includes('where')) {
      logicIssues.push('DELETE without WHERE clause - potential data loss');
    }

    if (sql.includes('update') && !sql.includes('where')) {
      logicIssues.push('UPDATE without WHERE clause - potential data corruption');
    }

    if (sql.includes('select') && sql.includes('password')) {
      logicIssues.push('Password field in SELECT - potential exposure');
    }

    return logicIssues;
  }
}
