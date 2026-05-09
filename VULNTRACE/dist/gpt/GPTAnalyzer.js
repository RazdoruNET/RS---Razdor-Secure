"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.GPTAnalyzer = void 0;
const openai_1 = __importDefault(require("openai"));
const types_1 = require("../types");
class GPTAnalyzer {
    constructor(config) {
        this.openai = null;
        this.config = config;
        if (config.enableGPTAnalysis && process.env.OPENAI_API_KEY) {
            this.openai = new openai_1.default({
                apiKey: process.env.OPENAI_API_KEY
            });
        }
    }
    async analyze(queries, context, staticVulnerabilities) {
        if (!this.openai) {
            console.warn('OpenAI not configured, skipping GPT analysis');
            return [];
        }
        const vulnerabilities = [];
        for (const query of queries) {
            try {
                const gptVulnerabilities = await this.analyzeQuery(query, context, staticVulnerabilities);
                vulnerabilities.push(...gptVulnerabilities);
            }
            catch (error) {
                console.warn(`GPT analysis failed for query ${query.id}:`, error);
            }
        }
        return vulnerabilities;
    }
    async analyzeQuery(query, context, staticVulnerabilities) {
        const request = {
            query,
            context,
            vulnerabilities: staticVulnerabilities.filter(v => v.filePath === query.filePath && v.line === query.line)
        };
        const response = await this.performGPTAnalysis(request);
        return this.convertGPTResponseToVulnerabilities(request, response);
    }
    async performGPTAnalysis(request) {
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
        }
        catch (error) {
            throw new Error(`GPT analysis failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    getSystemPrompt() {
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
    buildAnalysisPrompt(request) {
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
            'No static analysis vulnerabilities found'}

**Analysis Requirements:**
1. Identify security vulnerabilities beyond basic SQL injection patterns
2. Analyze performance implications
3. Check for business logic flaws
4. Identify data privacy concerns
5. Suggest specific improvements
6. Provide confidence level for each finding

Focus on semantic analysis that goes beyond pattern matching.`;
    }
    parseGPTResponse(response) {
        try {
            // Try to parse as JSON first
            const jsonMatch = response.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                return JSON.parse(jsonMatch[0]);
            }
        }
        catch (error) {
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
    extractRisks(response) {
        const risks = [];
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
    extractRecommendations(response) {
        const recommendations = [];
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
    convertGPTResponseToVulnerabilities(request, response) {
        const vulnerabilities = [];
        const { query } = request;
        // Convert risks to vulnerabilities
        response.risks.forEach((risk, index) => {
            const vulnerability = this.createGPTVulnerability(query, risk, response.recommendations[index] || response.recommendations[0] || 'Review and fix the identified issue', response.confidence);
            vulnerabilities.push(vulnerability);
        });
        return vulnerabilities;
    }
    createGPTVulnerability(query, risk, recommendation, confidence) {
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
    classifyVulnerabilityType(risk) {
        const lowerRisk = risk.toLowerCase();
        if (lowerRisk.includes('injection') || lowerRisk.includes('sql injection')) {
            return types_1.VulnerabilityType.SQL_INJECTION;
        }
        if (lowerRisk.includes('performance') || lowerRisk.includes('slow') || lowerRisk.includes('efficient')) {
            return types_1.VulnerabilityType.PERFORMANCE_ISSUE;
        }
        if (lowerRisk.includes('logic') || lowerRisk.includes('condition') || lowerRisk.includes('join')) {
            return types_1.VulnerabilityType.LOGIC_ERROR;
        }
        if (lowerRisk.includes('data') || lowerRisk.includes('sensitive') || lowerRisk.includes('exposure')) {
            return types_1.VulnerabilityType.DATA_EXPOSURE;
        }
        if (lowerRisk.includes('permission') || lowerRisk.includes('access') || lowerRisk.includes('privilege')) {
            return types_1.VulnerabilityType.PERMISSION_ISSUE;
        }
        if (lowerRisk.includes('insecure') || lowerRisk.includes('unsafe')) {
            return types_1.VulnerabilityType.INSECURE_OPERATION;
        }
        return types_1.VulnerabilityType.BEST_PRACTICE_VIOLATION;
    }
    classifySeverity(risk) {
        const lowerRisk = risk.toLowerCase();
        if (lowerRisk.includes('critical') || lowerRisk.includes('severe') || lowerRisk.includes('dangerous')) {
            return types_1.Severity.CRITICAL;
        }
        if (lowerRisk.includes('high') || lowerRisk.includes('important') || lowerRisk.includes('major')) {
            return types_1.Severity.HIGH;
        }
        if (lowerRisk.includes('medium') || lowerRisk.includes('moderate')) {
            return types_1.Severity.MEDIUM;
        }
        if (lowerRisk.includes('low') || lowerRisk.includes('minor')) {
            return types_1.Severity.LOW;
        }
        return types_1.Severity.MEDIUM; // Default to medium
    }
    classifyCategory(risk) {
        const lowerRisk = risk.toLowerCase();
        if (lowerRisk.includes('security') || lowerRisk.includes('injection') || lowerRisk.includes('vulnerability')) {
            return types_1.VulnerabilityCategory.SECURITY;
        }
        if (lowerRisk.includes('performance') || lowerRisk.includes('slow') || lowerRisk.includes('efficient')) {
            return types_1.VulnerabilityCategory.PERFORMANCE;
        }
        if (lowerRisk.includes('maintain') || lowerRisk.includes('readability') || lowerRisk.includes('standard')) {
            return types_1.VulnerabilityCategory.MAINTAINABILITY;
        }
        if (lowerRisk.includes('reliable') || lowerRisk.includes('error') || lowerRisk.includes('failure')) {
            return types_1.VulnerabilityCategory.RELIABILITY;
        }
        return types_1.VulnerabilityCategory.BEST_PRACTICE_VIOLATION;
    }
    mapToCWE(vulnerabilityType) {
        const cweMapping = {
            [types_1.VulnerabilityType.SQL_INJECTION]: 'CWE-89',
            [types_1.VulnerabilityType.PERFORMANCE_ISSUE]: 'CWE-1050',
            [types_1.VulnerabilityType.BEST_PRACTICE_VIOLATION]: 'CWE-1058',
            [types_1.VulnerabilityType.LOGIC_ERROR]: 'CWE-480',
            [types_1.VulnerabilityType.DATA_EXPOSURE]: 'CWE-200',
            [types_1.VulnerabilityType.PERMISSION_ISSUE]: 'CWE-862',
            [types_1.VulnerabilityType.INSECURE_OPERATION]: 'CWE-319'
        };
        return cweMapping[vulnerabilityType];
    }
    mapToOWASP(vulnerabilityType) {
        const owaspMapping = {
            [types_1.VulnerabilityType.SQL_INJECTION]: 'A03:2021 – Injection',
            [types_1.VulnerabilityType.DATA_EXPOSURE]: 'A02:2021 – Cryptographic Failures',
            [types_1.VulnerabilityType.INSECURE_OPERATION]: 'A05:2021 – Security Misconfiguration',
            [types_1.VulnerabilityType.PERMISSION_ISSUE]: 'A01:2021 – Broken Access Control',
            [types_1.VulnerabilityType.PERFORMANCE_ISSUE]: 'A05:2021 – Security Misconfiguration',
            [types_1.VulnerabilityType.BEST_PRACTICE_VIOLATION]: 'A05:2021 – Security Misconfiguration',
            [types_1.VulnerabilityType.LOGIC_ERROR]: 'A01:2021 – Broken Access Control'
        };
        return owaspMapping[vulnerabilityType];
    }
    // Method to analyze query complexity for performance insights
    analyzeQueryComplexity(query) {
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
    checkDataPrivacy(query) {
        const privacyIssues = [];
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
    analyzeBusinessLogic(query) {
        const logicIssues = [];
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
exports.GPTAnalyzer = GPTAnalyzer;
//# sourceMappingURL=GPTAnalyzer.js.map