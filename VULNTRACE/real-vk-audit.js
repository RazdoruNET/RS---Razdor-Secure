#!/usr/bin/env node

const RealAuditEngine = require('./real-audit-engine');

async function performRealVKAudit() {
    console.log('🔥 REAL VK.COM SECURITY AUDIT');
    console.log('Authorized by domain owner');
    console.log('Using Real Audit Engine with evidence collection');
    console.log('=' .repeat(80));
    
    const engine = new RealAuditEngine('vk.com', {
        timeout: 60000, // 1 minute per request
        maxRetries: 3,
        userAgent: 'RealAuditEngine/1.0 - Authorized Security Testing'
    });
    
    try {
        const report = await engine.performRealAudit();
        
        console.log('\n📊 REAL AUDIT RESULTS:');
        console.log('='.repeat(80));
        console.log(`🎯 Target: ${report.metadata.target}`);
        console.log(`📋 Session ID: ${report.metadata.sessionId}`);
        console.log(`⏱️  Duration: ${report.metadata.duration}ms`);
        console.log(`🔍 Total Traces: ${report.metadata.totalTraces}`);
        console.log(`🔍 Traces with Evidence: ${report.evidence.tracesWithEvidence}`);
        
        console.log('\n🔍 RECONNAISSANCE RESULTS:');
        if (report.reconnaissance) {
            console.log(`   DNS Records: ${Object.keys(report.reconnaissance.dns || {}).length}`);
            console.log(`   Open Ports: ${report.reconnaissance.ports?.length || 0}`);
            console.log(`   Technologies: ${report.reconnaissance.technologies?.length || 0}`);
        }
        
        console.log('\n🚨 VULNERABILITY TEST RESULTS:');
        if (report.vulnerabilityTests) {
            for (const [testType, results] of Object.entries(report.vulnerabilityTests)) {
                console.log(`   ${testType}: ${results.length} findings`);
            }
        }
        
        console.log('\n🔍 EVIDENCE DISTRIBUTION:');
        if (report.evidence.evidenceTypes) {
            for (const [type, count] of Object.entries(report.evidence.evidenceTypes)) {
                console.log(`   ${type}: ${count}`);
            }
        }
        
        if (report.rawTraces && report.rawTraces.length > 0) {
            console.log('\n📋 SAMPLE TRACE (with evidence):');
            const sampleTrace = report.rawTraces.find(t => t.evidence.length > 0);
            if (sampleTrace) {
                console.log(`   Trace ID: ${sampleTrace.traceId}`);
                console.log(`   Payload: ${sampleTrace.payload}`);
                console.log(`   Request: ${sampleTrace.request.method} ${sampleTrace.request.url}`);
                console.log(`   Response Status: ${sampleTrace.response.status}`);
                console.log(`   Response Duration: ${sampleTrace.response.duration}ms`);
                console.log(`   Evidence Count: ${sampleTrace.evidence.length}`);
                if (sampleTrace.evidence.length > 0) {
                    console.log(`   Evidence Types: ${sampleTrace.evidence.map(e => e.type).join(', ')}`);
                }
                console.log(`   Classification: ${sampleTrace.classification.vulnerable ? 'VULNERABLE' : 'SAFE'}`);
            }
        }
        
        console.log('\n' + '='.repeat(80));
        console.log('✅ REAL AUDIT COMPLETED');
        console.log('='.repeat(80));
        
        return report;
        
    } catch (error) {
        console.error('❌ Real audit failed:', error.message);
        throw error;
    }
}

// Run real audit
if (require.main === module) {
    performRealVKAudit().catch(console.error);
}

module.exports = { performRealVKAudit };
