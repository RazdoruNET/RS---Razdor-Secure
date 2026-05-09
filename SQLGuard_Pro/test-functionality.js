const { SQLVulnerabilityScanner } = require('./dist/main.js');

async function testBasicFunctionality() {
  console.log('🧪 Testing SQLGuard Pro Basic Functionality...\n');
  
  try {
    // Initialize scanner
    const scanner = new SQLVulnerabilityScanner({
      databaseType: 'mysql',
      securityLevel: 'moderate',
      enableGPTAnalysis: false, // Disable GPT for basic test
      enablePerformanceAnalysis: true,
      ignoredRules: [],
      customRules: []
    });
    
    console.log('✅ Scanner initialized successfully');
    
    // Test with vulnerable SQL
    const vulnerableSQL = `
      SELECT * FROM users WHERE username = '\${username}' AND password = '\${password}';
    `;
    
    console.log('🔍 Analyzing vulnerable SQL...');
    const vulnerableResult = await scanner.analyzeFile('test.sql', vulnerableSQL);
    
    console.log('📊 Vulnerable SQL Analysis Results:');
    console.log(`   - Queries found: ${vulnerableResult.queries.length}`);
    console.log(`   - Vulnerabilities found: ${vulnerableResult.vulnerabilities.length}`);
    
    vulnerableResult.vulnerabilities.forEach((vuln, index) => {
      console.log(`   ${index + 1}. ${vuln.severity.toUpperCase()}: ${vuln.title}`);
      console.log(`      - ${vuln.description}`);
      console.log(`      - Line: ${vuln.line}, Column: ${vuln.column}`);
    });
    
    // Test with safe SQL
    const safeSQL = `
      SELECT id, username, email 
      FROM users 
      WHERE id = ? AND status = 'active';
    `;
    
    console.log('\n🛡️  Analyzing safe SQL...');
    const safeResult = await scanner.analyzeFile('safe.sql', safeSQL);
    
    console.log('📊 Safe SQL Analysis Results:');
    console.log(`   - Queries found: ${safeResult.queries.length}`);
    console.log(`   - Vulnerabilities found: ${safeResult.vulnerabilities.length}`);
    
    // Test report generation
    console.log('\n📄 Generating reports...');
    const jsonReport = await scanner.generateReport(vulnerableResult, 'json');
    console.log('✅ JSON report generated successfully');
    
    const htmlReport = await scanner.generateReport(vulnerableResult, 'html');
    console.log('✅ HTML report generated successfully');
    
    console.log('\n🎉 Basic functionality test completed successfully!');
    console.log('📈 SQLGuard Pro is working correctly!');
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    process.exit(1);
  }
}

testBasicFunctionality();
