#!/usr/bin/env node

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class GroundTruthEvaluation {
    constructor() {
        this.traces = [];
        this.metrics = {
            truePositives: 0,
            falsePositives: 0,
            trueNegatives: 0,
            falseNegatives: 0
        };
        this.evidenceStore = new Map();
        this.executionLog = [];
    }

    createTrace(traceId, target, payload, request, response, timestamp) {
        const trace = {
            traceId,
            target,
            payload,
            request: {
                method: request.method,
                url: request.url,
                headers: request.headers,
                body: request.body,
                timestamp: request.timestamp
            },
            response: {
                status: response.status,
                headers: response.headers,
                body: response.body,
                timestamp: response.timestamp,
                duration: response.duration
            },
            timestamp,
            evidence: this.extractEvidence(request, response),
            classification: this.classifyResponse(response)
        };

        this.traces.push(trace);
        this.executionLog.push({
            type: 'trace_created',
            traceId,
            timestamp: new Date().toISOString()
        });

        return trace;
    }

    extractEvidence(request, response) {
        const evidence = [];

        // SQL Injection evidence
        if (this.containsSQLErrors(response.body)) {
            evidence.push({
                type: 'sql_error',
                pattern: this.extractSQLPattern(response.body),
                confidence: 0.9,
                source: 'response_body'
            });
        }

        // XSS evidence
        if (this.containsXSSPayload(request.body) && this.containsXSSInResponse(response.body)) {
            evidence.push({
                type: 'xss_reflection',
                payload: this.extractXSSPayload(request.body),
                reflected: this.extractReflectedXSS(response.body),
                confidence: 0.85,
                source: 'request_response_correlation'
            });
        }

        // Command injection evidence
        if (this.containsCommandErrors(response.body)) {
            evidence.push({
                type: 'command_error',
                pattern: this.extractCommandPattern(response.body),
                confidence: 0.95,
                source: 'response_body'
            });
        }

        return evidence;
    }

    containsSQLErrors(responseBody) {
        const sqlErrors = [
            /SQL syntax.*MySQL/i,
            /Warning.*mysql_/i,
            /valid PostgreSQL result/i,
            /ORA-\d{5}/i,
            /Microsoft OLE DB Provider/i
        ];
        return sqlErrors.some(pattern => pattern.test(responseBody));
    }

    containsXSSPayload(requestBody) {
        const xssPatterns = [
            /<script[^>]*>/i,
            /on\w+\s*=/i,
            /javascript:/i,
            /<iframe[^>]*>/i
        ];
        return xssPatterns.some(pattern => pattern.test(requestBody));
    }

    containsXSSInResponse(responseBody) {
        return responseBody.includes(this.extractXSSPayload(this.lastRequest?.body || ''));
    }

    containsCommandErrors(responseBody) {
        const commandErrors = [
            /sh: .+: not found/i,
            /bash: .+: command not found/i,
            /cmd\.exe .+: not recognized/i,
            /Permission denied/i
        ];
        return commandErrors.some(pattern => pattern.test(responseBody));
    }

    extractSQLPattern(responseBody) {
        const patterns = {
            mysql: /SQL syntax.*MySQL/gi,
            postgresql: /valid PostgreSQL result/gi,
            oracle: /ORA-\d{5}/g
        };
        
        for (const [db, pattern] of Object.entries(patterns)) {
            if (pattern.test(responseBody)) {
                return { database: db, match: responseBody.match(pattern)[0] };
            }
        }
        return null;
    }

    extractXSSPayload(requestBody) {
        const xssMatch = requestBody.match(/<script[^>]*>(.*?)<\/script>/i) ||
                       requestBody.match(/on\w+\s*=\s*["']([^"']+)["']/i);
        return xssMatch ? xssMatch[1] : null;
    }

    extractReflectedXSS(responseBody) {
        const payload = this.extractXSSPayload(this.lastRequest?.body || '');
        return payload ? responseBody.includes(payload) : false;
    }

    extractCommandPattern(responseBody) {
        const patterns = {
            bash: /sh: .+: not found/gi,
            cmd: /cmd\.exe .+: not recognized/gi
        };
        
        for (const [shell, pattern] of Object.entries(patterns)) {
            if (pattern.test(responseBody)) {
                return { shell, match: responseBody.match(pattern)[0] };
            }
        }
        return null;
    }

    classifyResponse(response) {
        const classification = {
            vulnerable: false,
            vulnerability: null,
            confidence: 0,
            cwe: null,
            severity: null
        };

        // SQL Injection classification
        if (this.containsSQLErrors(response.body)) {
            classification.vulnerable = true;
            classification.vulnerability = 'sql_injection';
            classification.confidence = 0.9;
            classification.cwe = 'CWE-89';
            classification.severity = 'high';
        }

        // XSS classification
        if (this.containsXSSPayload(this.lastRequest?.body || '') && 
            this.containsXSSInResponse(response.body)) {
            classification.vulnerable = true;
            classification.vulnerability = 'xss';
            classification.confidence = 0.85;
            classification.cwe = 'CWE-79';
            classification.severity = 'medium';
        }

        // Command injection classification
        if (this.containsCommandErrors(response.body)) {
            classification.vulnerable = true;
            classification.vulnerability = 'command_injection';
            classification.confidence = 0.95;
            classification.cwe = 'CWE-78';
            classification.severity = 'critical';
        }

        return classification;
    }

    calculateMetrics(groundTruth) {
        const results = {
            precision: 0,
            recall: 0,
            f1Score: 0,
            falsePositiveRate: 0,
            falseNegativeRate: 0,
            truePositiveRate: 0,
            trueNegativeRate: 0,
            confusionMatrix: {
                tp: 0, fp: 0, fn: 0, tn: 0
            }
        };

        // Compare traces with ground truth
        for (const trace of this.traces) {
            const groundTruthFinding = groundTruth.find(gt => 
                gt.endpoint === trace.request.url && 
                gt.payload === trace.payload
            );

            if (groundTruthFinding) {
                if (trace.classification.vulnerable && groundTruthFinding.vulnerable) {
                    results.confusionMatrix.tp++; // True Positive
                    this.metrics.truePositives++;
                } else if (!trace.classification.vulnerable && !groundTruthFinding.vulnerable) {
                    results.confusionMatrix.tn++; // True Negative
                    this.metrics.trueNegatives++;
                } else if (trace.classification.vulnerable && !groundTruthFinding.vulnerable) {
                    results.confusionMatrix.fp++; // False Positive
                    this.metrics.falsePositives++;
                } else {
                    results.confusionMatrix.fn++; // False Negative
                    this.metrics.falseNegatives++;
                }
            }
        }

        // Calculate metrics
        const total = results.confusionMatrix.tp + results.confusionMatrix.fp + 
                     results.confusionMatrix.fn + results.confusionMatrix.tn;

        results.precision = results.confusionMatrix.tp / 
                          (results.confusionMatrix.tp + results.confusionMatrix.fp) || 0;
        
        results.recall = results.confusionMatrix.tp / 
                       (results.confusionMatrix.tp + results.confusionMatrix.fn) || 0;
        
        results.f1Score = 2 * (results.precision * results.recall) / 
                           (results.precision + results.recall) || 0;

        results.falsePositiveRate = results.confusionMatrix.fp / 
                                 (results.confusionMatrix.fp + results.confusionMatrix.tn) || 0;
        
        results.falseNegativeRate = results.confusionMatrix.fn / 
                                 (results.confusionMatrix.fn + results.confusionMatrix.tp) || 0;
        
        results.truePositiveRate = results.confusionMatrix.tp / total;
        results.trueNegativeRate = results.confusionMatrix.tn / total;

        return results;
    }

    generateEvidenceReport() {
        const report = {
            timestamp: new Date().toISOString(),
            totalTraces: this.traces.length,
            evidenceTypes: {},
            evidenceDistribution: {},
            reproducibilityRate: 0
        };

        // Analyze evidence distribution
        for (const trace of this.traces) {
            for (const evidence of trace.evidence) {
                if (!report.evidenceTypes[evidence.type]) {
                    report.evidenceTypes[evidence.type] = 0;
                }
                report.evidenceTypes[evidence.type]++;
            }
        }

        // Calculate reproducibility
        const reproducibleTraces = this.traces.filter(trace => 
            trace.evidence.length > 0
        );
        report.reproducibilityRate = (reproducibleTraces.length / this.traces.length) * 100;

        return report;
    }

    saveTraces(filename) {
        const traceData = {
            metadata: {
                generated: new Date().toISOString(),
                totalTraces: this.traces.length,
                evaluationFramework: 'GroundTruthEvaluation v1.0'
            },
            traces: this.traces,
            metrics: this.metrics,
            executionLog: this.executionLog
        };

        const filepath = path.join(process.cwd(), 'traces', filename);
        const tracesDir = path.dirname(filepath);
        
        // Ensure traces directory exists
        if (!fs.existsSync(tracesDir)) {
            fs.mkdirSync(tracesDir, { recursive: true });
        }
        
        fs.writeFileSync(filepath, JSON.stringify(traceData, null, 2));
        console.log(`📄 Traces saved: ${filepath}`);
    }

    generateReplayScript(traceId) {
        const trace = this.traces.find(t => t.traceId === traceId);
        if (!trace) {
            throw new Error(`Trace ${traceId} not found`);
        }

        const script = `#!/usr/bin/env node
const https = require('https');

// Replay script for trace: ${traceId}
const target = '${trace.request.url}';
const payload = '${trace.payload}';

const options = {
    hostname: new URL(target).hostname,
    port: 443,
    path: new URL(target).pathname,
    method: '${trace.request.method}',
    headers: ${JSON.stringify(trace.request.headers, null, 2)},
    timeout: 10000
};

const req = https.request(options, (res) => {
    let data = '';
    res.on('data', (chunk) => data += chunk);
    res.on('end', () => {
        console.log('Status:', res.statusCode);
        console.log('Headers:', res.headers);
        console.log('Body:', data);
        console.log('Duration:', Date.now() - startTime);
    });
});

const startTime = Date.now();
req.write('${trace.request.body}');
req.end();
`;

        const scriptPath = path.join(process.cwd(), 'replay', `replay_${traceId}.js`);
        fs.writeFileSync(scriptPath, script);
        console.log(`📄 Replay script created: ${scriptPath}`);
        
        return scriptPath;
    }
}

// Ground truth environments
class GroundTruthEnvironment {
    constructor(name, config) {
        this.name = name;
        this.config = config;
        this.vulnerabilities = [];
    }

    addVulnerability(endpoint, payload, vulnerability, severity, cwe) {
        this.vulnerabilities.push({
            endpoint,
            payload,
            vulnerability,
            severity,
            cwe,
            id: crypto.randomBytes(8).toString('hex')
        });
    }

    exportGroundTruth() {
        return {
            environment: this.name,
            config: this.config,
            vulnerabilities: this.vulnerabilities,
            generated: new Date().toISOString()
        };
    }
}

// Create test environments
const dvwa = new GroundTruthEnvironment('DVWA', {
    url: 'http://localhost/vulnerabilities/',
    authentication: 'basic',
    difficulty: 'low'
});

dvwa.addVulnerability(
    'http://localhost/vulnerabilities/sqli/?id=1',
    "1' OR '1'='1",
    'sql_injection',
    'high',
    'CWE-89'
);

dvwa.addVulnerability(
    'http://localhost/vulnerabilities/xss_reflected/?name=test',
    '<script>alert(1)</script>',
    'xss',
    'medium',
    'CWE-79'
);

const juiceShop = new GroundTruthEnvironment('Juice Shop', {
    url: 'http://localhost:3000',
    authentication: 'form-based',
    framework: 'Node.js/Express'
});

juiceShop.addVulnerability(
    'http://localhost:3000/rest/user/login',
    '{"email": "admin@juice-sh.op","password": "admin"; echo test"}',
    'command_injection',
    'critical',
    'CWE-78'
);

module.exports = { GroundTruthEvaluation, GroundTruthEnvironment, dvwa, juiceShop };
