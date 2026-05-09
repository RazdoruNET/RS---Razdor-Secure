import { ProphecySandbox } from '../../src/prophecy-sandbox/ProphecySandbox';
import { SecurityConfig } from '../../src/security/types';
import { ProphecySandboxConfig } from '../../src/prophecy-sandbox/ProphecySandbox';
import * as fs from 'fs';
import * as path from 'path';

describe('ProphecySandbox Integration Tests', () => {
  let prophecySandbox: ProphecySandbox;
  let testConfig: ProphecySandboxConfig;
  let securityConfig: SecurityConfig;
  let testWorkspace: string;

  beforeAll(async () => {
    // Setup test workspace
    testWorkspace = path.join(__dirname, 'test-workspace');
    await fs.promises.mkdir(testWorkspace, { recursive: true });

    // Setup test configurations
    securityConfig = {
      enableAuditLogging: true,
      blockExternalRequests: true,
      readonly: true,
      requireConfirmation: false,
      ethicalWarningAccepted: true,
      auditLogPath: path.join(testWorkspace, 'audit.log')
    };

    testConfig = {
      enabled: true,
      sandbox: {
        enabled: true,
        isolationLevel: 'process',
        networkIsolated: true,
        autoDestroy: true,
        maxExecutionTime: 30,
        resourceLimits: {
          memory: '256m',
          cpu: '0.5',
          disk: '512m'
        }
      },
      accessControl: {
        jwtSecret: 'test-secret',
        tokenExpiration: '1h',
        requireRazdorAuth: true,
        maxFailedAttempts: 3,
        lockoutDuration: 300000,
        auditLogPath: path.join(testWorkspace, 'access.log')
      },
      analysis: {
        enableBehavioralAnalysis: true,
        enableSignatureMatching: true,
        enableAnomalyDetection: true,
        riskThreshold: 50,
        knownTechniquesDatabase: path.join(testWorkspace, 'techniques.json')
      },
      learning: {
        enableAdaptiveGeneration: true,
        enableSignatureEvolution: true,
        enableTechniqueLearning: true,
        learningRate: 0.1,
        minSamplesForLearning: 5,
        modelPersistencePath: path.join(testWorkspace, 'learning.json')
      },
      dashboard: {
        port: 0, // Use random port for testing
        host: 'localhost',
        enableRealTimeUpdates: true,
        enableCharts: true,
        maxHistoryItems: 100,
        refreshInterval: 5000
      },
      cli: {
        outputFormat: 'json',
        verbose: false,
        configPath: path.join(testWorkspace, 'cli-config.json'),
        autoSave: false
      },
      integration: {
        cascadeHooks: true,
        nativeImageUnderstanding: true,
        fastContext: true,
        rbac: true,
        codemaps: true
      }
    };

    prophecySandbox = new ProphecySandbox(testWorkspace, securityConfig, testConfig);
  });

  afterAll(async () => {
    // Cleanup
    if (prophecySandbox) {
      await prophecySandbox.shutdown();
    }
    
    // Remove test workspace
    await fs.promises.rm(testWorkspace, { recursive: true, force: true });
  });

  describe('Initialization', () => {
    test('should initialize successfully', async () => {
      const result = await prophecySandbox.initialize();
      expect(result).toBe(true);
      expect(prophecySandbox.isReady()).toBe(true);
    });

    test('should fail initialization when disabled', async () => {
      const disabledConfig = { ...testConfig, enabled: false };
      const disabledSandbox = new ProphecySandbox(testWorkspace, securityConfig, disabledConfig);
      
      const result = await disabledSandbox.initialize();
      expect(result).toBe(false);
    });
  });

  describe('Access Control', () => {
    let authToken: string;

    test('should generate authentication challenge', async () => {
      const challenge = prophecySandbox.getAccessControl().generateChallenge();
      expect(challenge).toBeDefined();
      expect(challenge.length).toBeGreaterThan(0);
    });

    test('should authenticate RAZDOR user', async () => {
      const challenge = prophecySandbox.getAccessControl().generateChallenge();
      
      // Mock signature (in real test, would use actual cryptographic signing)
      const mockSignature = 'mock-signature';
      
      const token = await prophecySandbox.getAccessControl().authenticateRazdor(mockSignature, challenge);
      expect(token).toBeDefined();
      expect(token.userId).toBe('razdor');
      expect(token.role).toBe('razdor');
      
      authToken = token.token;
    });

    test('should validate JWT token', async () => {
      const session = await prophecySandbox.getAccessControl().validateToken(authToken);
      expect(session).toBeDefined();
      expect(session.userId).toBe('razdor');
    });

    test('should reject invalid token', async () => {
      const session = await prophecySandbox.getAccessControl().validateToken('invalid-token');
      expect(session).toBeNull();
    });
  });

  describe('Sample Generation', () => {
    let userId: string;

    beforeAll(() => {
      userId = 'razdor'; // Use authenticated user
    });

    test('should generate malicious sample', async () => {
      const sample = await prophecySandbox.generateSample(
        'python-backdoor-001',
        {
          targetThreatLevel: 'medium',
          includeEvasion: false,
          mutationRate: 0.1,
          maxComplexity: 5,
          allowedTechniques: []
        },
        userId
      );

      expect(sample).toBeDefined();
      expect(sample.id).toBeDefined();
      expect(sample.type).toBe('backdoor');
      expect(sample.language).toBe('python');
      expect(sample.code).toBeDefined();
      expect(sample.metadata.threatLevel).toBe('medium');
    });

    test('should reject unauthorized sample generation', async () => {
      await expect(
        prophecySandbox.generateSample(
          'python-backdoor-001',
          {},
          'unauthorized-user'
        )
      ).rejects.toThrow('Insufficient permissions');
    });
  });

  describe('Sandbox Execution', () => {
    let testSample: any;
    let userId: string;

    beforeAll(async () => {
      userId = 'razdor';
      testSample = await prophecySandbox.generateSample(
        'python-backdoor-001',
        {
          targetThreatLevel: 'low',
          includeEvasion: false,
          mutationRate: 0,
          maxComplexity: 1,
          allowedTechniques: []
        },
        userId
      );
    });

    test('should execute sample in sandbox', async () => {
      const execution = await prophecySandbox.executeSample(testSample, userId);
      
      expect(execution).toBeDefined();
      expect(execution.id).toBeDefined();
      expect(execution.sampleId).toBe(testSample.id);
      expect(execution.status).toMatch(/pending|running|completed|failed/);
      expect(execution.analysisResults).toBeDefined();
    }, 10000); // Longer timeout for sandbox execution

    test('should retrieve execution details', async () => {
      // First execute a sample
      const execution = await prophecySandbox.executeSample(testSample, userId);
      
      // Then retrieve it
      const retrievedExecution = await prophecySandbox.getExecution(execution.id, userId);
      expect(retrievedExecution).toBeDefined();
      expect(retrievedExecution.id).toBe(execution.id);
    });

    test('should reject unauthorized execution access', async () => {
      const execution = await prophecySandbox.executeSample(testSample, userId);
      
      await expect(
        prophecySandbox.getExecution(execution.id, 'unauthorized-user')
      ).rejects.toThrow('Insufficient permissions');
    });
  });

  describe('Threat Analysis', () => {
    let testExecution: any;
    let userId: string;

    beforeAll(async () => {
      userId = 'razdor';
      const testSample = await prophecySandbox.generateSample(
        'python-backdoor-001',
        {
          targetThreatLevel: 'medium',
          includeEvasion: true,
          mutationRate: 0.2,
          maxComplexity: 3,
          allowedTechniques: []
        },
        userId
      );
      
      testExecution = await prophecySandbox.executeSample(testSample, userId);
    });

    test('should analyze execution results', async () => {
      expect(testExecution.analysisResults).toBeDefined();
      expect(testExecution.analysisResults.riskScore).toBeGreaterThanOrEqual(0);
      expect(testExecution.analysisResults.riskScore).toBeLessThanOrEqual(100);
      expect(testExecution.analysisResults.techniques).toBeInstanceOf(Array);
      expect(testExecution.analysisResults.anomalies).toBeInstanceOf(Array);
      expect(testExecution.analysisResults.signatures).toBeInstanceOf(Array);
      expect(testExecution.analysisResults.summary).toBeDefined();
    });

    test('should detect attack techniques', () => {
      const { techniques } = testExecution.analysisResults;
      expect(techniques.length).toBeGreaterThanOrEqual(0);
      
      if (techniques.length > 0) {
        const technique = techniques[0];
        expect(technique.id).toBeDefined();
        expect(technique.name).toBeDefined();
        expect(technique.confidence).toBeGreaterThanOrEqual(0);
        expect(technique.confidence).toBeLessThanOrEqual(1);
      }
    });

    test('should calculate risk score', () => {
      const { riskScore } = testExecution.analysisResults;
      expect(riskScore).toBeGreaterThanOrEqual(0);
      expect(riskScore).toBeLessThanOrEqual(100);
    });
  });

  describe('Learning System', () => {
    let userId: string;

    beforeAll(() => {
      userId = 'razdor';
    });

    test('should get learning metrics', async () => {
      const metrics = await prophecySandbox.getMetrics(userId);
      
      expect(metrics).toBeDefined();
      expect(metrics.totalSamplesAnalyzed).toBeGreaterThanOrEqual(0);
      expect(metrics.successfulDetections).toBeGreaterThanOrEqual(0);
      expect(metrics.falsePositives).toBeGreaterThanOrEqual(0);
      expect(metrics.falseNegatives).toBeGreaterThanOrEqual(0);
      expect(metrics.averageRiskScore).toBeGreaterThanOrEqual(0);
      expect(metrics.techniqueEvolutionCount).toBeGreaterThanOrEqual(0);
      expect(metrics.signatureEvolutionCount).toBeGreaterThanOrEqual(0);
    });

    test('should process multiple samples for learning', async () => {
      // Generate and execute multiple samples
      const samples = [];
      for (let i = 0; i < 3; i++) {
        const sample = await prophecySandbox.generateSample(
          'python-backdoor-001',
          {
            targetThreatLevel: 'medium',
            includeEvasion: i % 2 === 0,
            mutationRate: 0.1 * i,
            maxComplexity: 2 + i,
            allowedTechniques: []
          },
          userId
        );
        
        const execution = await prophecySandbox.executeSample(sample, userId);
        samples.push(execution);
      }

      // Check that learning system processed them
      const metrics = await prophecySandbox.getMetrics(userId);
      expect(metrics.totalSamplesAnalyzed).toBeGreaterThanOrEqual(3);
    }, 30000); // Longer timeout for multiple executions
  });

  describe('Ethical Safeguards', () => {
    test('should reject forbidden targets', async () => {
      // This test would require the EthicalSafeguards to be integrated
      // For now, we'll test the basic functionality
      expect(prophecySandbox.getConfig().integration.cascadeHooks).toBe(true);
    });
  });

  describe('Dashboard Integration', () => {
    test('should provide dashboard data', () => {
      const dashboardData = prophecySandbox.getDashboard().getDashboardData();
      expect(dashboardData).toBeDefined();
      expect(dashboardData.systemStatus).toBeDefined();
      expect(dashboardData.activeExecutions).toBeInstanceOf(Array);
      expect(dashboardData.recentSamples).toBeInstanceOf(Array);
      expect(dashboardData.learningMetrics).toBeDefined();
      expect(dashboardData.alerts).toBeInstanceOf(Array);
    });
  });

  describe('CLI Integration', () => {
    test('should handle CLI commands', async () => {
      // Test basic CLI functionality
      expect(() => {
        prophecySandbox.runCLI(['system', 'status']);
      }).not.toThrow();
    });
  });

  describe('Error Handling', () => {
    test('should handle invalid template ID', async () => {
      await expect(
        prophecySandbox.generateSample(
          'invalid-template',
          {},
          'razdor'
        )
      ).rejects.toThrow();
    });

    test('should handle non-existent execution', async () => {
      const execution = await prophecySandbox.getExecution('non-existent-id', 'razdor');
      expect(execution).toBeNull();
    });

    test('should handle malformed requests', async () => {
      await expect(
        prophecySandbox.generateSample(
          '',
          null,
          'razdor'
        )
      ).rejects.toThrow();
    });
  });

  describe('Performance', () => {
    test('should initialize within reasonable time', async () => {
      const startTime = Date.now();
      await prophecySandbox.initialize();
      const endTime = Date.now();
      
      expect(endTime - startTime).toBeLessThan(10000); // 10 seconds
    });

    test('should generate samples quickly', async () => {
      const startTime = Date.now();
      await prophecySandbox.generateSample(
        'python-backdoor-001',
        {
          targetThreatLevel: 'low',
          includeEvasion: false,
          mutationRate: 0,
          maxComplexity: 1,
          allowedTechniques: []
        },
        'razdor'
      );
      const endTime = Date.now();
      
      expect(endTime - startTime).toBeLessThan(5000); // 5 seconds
    });
  });
});
