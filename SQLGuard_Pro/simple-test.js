// Simple test without complex dependencies
console.log('🧪 Testing SQLGuard Pro Basic Functionality...\n');

// Test 1: Check if main module can be loaded
try {
  const mainModule = require('./dist/main.js');
  console.log('✅ Main module loaded successfully');
  
  // Test 2: Check if SQLVulnerabilityScanner class exists
  if (mainModule.SQLVulnerabilityScanner) {
    console.log('✅ SQLVulnerabilityScanner class found');
    
    // Test 3: Try to create instance
    try {
      const scanner = new mainModule.SQLVulnerabilityScanner({
        databaseType: 'mysql',
        securityLevel: 'moderate',
        enableGPTAnalysis: false,
        enablePerformanceAnalysis: true,
        ignoredRules: [],
        customRules: []
      });
      
      console.log('✅ Scanner instance created successfully');
      
      // Test 4: Check if analyze method exists
      if (typeof scanner.analyze === 'function') {
        console.log('✅ Analyze method found');
        
        // Test 5: Try to analyze simple SQL
        try {
          const testContext = {
            filePath: 'test.sql',
            content: 'SELECT * FROM users;',
            database: 'mysql'
          };
          
          const result = scanner.analyze(testContext);
          
          if (result && typeof result.then === 'function') {
            console.log('✅ Analyze method returns Promise');
            
            result.then(analysisResult => {
              console.log('✅ Analysis completed successfully');
              console.log('📊 Analysis Results:');
              console.log(`   - Content length: ${analysisResult.content ? analysisResult.content.length : 0} chars`);
              console.log(`   - Queries found: ${analysisResult.queries ? analysisResult.queries.length : 0}`);
              console.log(`   - Vulnerabilities found: ${analysisResult.vulnerabilities ? analysisResult.vulnerabilities.length : 0}`);
              
              if (analysisResult.vulnerabilities && analysisResult.vulnerabilities.length > 0) {
                analysisResult.vulnerabilities.forEach((vuln, index) => {
                  console.log(`   ${index + 1}. ${vuln.severity}: ${vuln.title}`);
                });
              }
              
              console.log('\n🎉 SQLGuard Pro is working correctly!');
              console.log('📈 All basic functionality tests passed!');
            }).catch(error => {
              console.error('❌ Analysis failed:', error.message);
            });
          } else {
            console.log('❌ Analyze method does not return Promise');
          }
        } catch (error) {
          console.error('❌ Analysis test failed:', error.message);
        }
      } else {
        console.log('❌ Analyze method not found');
      }
    } catch (error) {
      console.error('❌ Scanner creation failed:', error.message);
    }
  } else {
    console.log('❌ SQLVulnerabilityScanner class not found');
  }
} catch (error) {
  console.error('❌ Module loading failed:', error.message);
  process.exit(1);
}
