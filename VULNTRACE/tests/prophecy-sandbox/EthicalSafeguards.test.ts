import { EthicalSafeguards, EthicalConfig } from '../../src/prophecy-sandbox/EthicalSafeguards';
import { AccessControlSystem, AccessControlConfig } from '../../src/prophecy-sandbox/access-control/AccessControlSystem';
import * as fs from 'fs';
import * as path from 'path';

describe('EthicalSafeguards Tests', () => {
  let ethicalSafeguards: EthicalSafeguards;
  let accessControl: AccessControlSystem;
  let testConfig: EthicalConfig;
  let testWorkspace: string;

  beforeAll(async () => {
    // Setup test workspace
    testWorkspace = path.join(__dirname, 'test-ethical-workspace');
    await fs.promises.mkdir(testWorkspace, { recursive: true });

    // Setup access control for testing
    const accessConfig: AccessControlConfig = {
      jwtSecret: 'test-secret',
      tokenExpiration: '1h',
      requireRazdorAuth: true,
      maxFailedAttempts: 3,
      lockoutDuration: 300000,
      auditLogPath: path.join(testWorkspace, 'access.log')
    };

    accessControl = new AccessControlSystem(accessConfig);

    // Setup ethical safeguards config
    testConfig = {
      enableMoralCompass: true,
      requireLicenseActivation: true,
      allowedTargets: ['localhost', 'test', 'demo'],
      forbiddenTargets: ['bank', 'hospital', 'government', 'school'],
      maxComplexityLevel: 8,
      requireExplicitConsent: true,
      auditAllActions: true,
      autoBlockSuspicious: true
    };

    ethicalSafeguards = new EthicalSafeguards(testConfig, accessControl);
  });

  afterAll(async () => {
    // Cleanup
    await ethicalSafeguards.reset();
    await fs.promises.rm(testWorkspace, { recursive: true, force: true });
  });

  describe('License Validation', () => {
    test('should reject requests without license', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'test-user',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test backdoor generation',
          complexityLevel: 3,
          userId: 'test-user'
        }
      );

      expect(result.allowed).toBe(false);
      expect(result.violations.some(v => v.type === 'license_invalid')).toBe(true);
    });

    test('should accept requests with valid license', async () => {
      // Activate license first
      const licenseActivated = await ethicalSafeguards.activateLicense(
        'test-license-key-12345',
        'Test Organization'
      );
      expect(licenseActivated).toBe(true);

      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test backdoor generation',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(true);
      expect(result.violations.some(v => v.type === 'license_invalid')).toBe(false);
    });

    test('should reject invalid license keys', async () => {
      const licenseActivated = await ethicalSafeguards.activateLicense(
        'short',
        'Test Organization'
      );
      expect(licenseActivated).toBe(false);
    });
  });

  describe('Target Restrictions', () => {
    beforeAll(async () => {
      // Activate license for these tests
      await ethicalSafeguards.activateLicense('test-license-key-12345', 'Test Org');
    });

    test('should allow allowed targets', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test for localhost',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(true);
      expect(result.violations.some(v => v.type === 'target_restriction')).toBe(false);
    });

    test('should reject forbidden targets', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'bank',
          description: 'Test targeting bank',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(false);
      expect(result.violations.some(v => v.type === 'target_restriction')).toBe(true);
      expect(result.violations.some(v => v.description.includes('bank'))).toBe(true);
    });

    test('should reject targets not in allowed list when list is specified', async () => {
      const strictConfig = { ...testConfig, allowedTargets: ['localhost'] };
      const strictSafeguards = new EthicalSafeguards(strictConfig, accessControl);

      const result = await strictSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'unknown-target',
          description: 'Test unknown target',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(false);
      expect(result.violations.some(v => v.type === 'target_restriction')).toBe(true);
    });
  });

  describe('Complexity Limits', () => {
    test('should allow complexity within limits', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test within complexity limit',
          complexityLevel: 5,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(true);
      expect(result.violations.some(v => v.type === 'complexity_limit')).toBe(false);
    });

    test('should warn about excessive complexity', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test excessive complexity',
          complexityLevel: 10,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(true); // Should be allowed but with warning
      expect(result.violations.some(v => v.type === 'complexity_limit')).toBe(true);
      expect(result.violations.find(v => v.type === 'complexity_limit')?.action).toBe('warned');
    });
  });

  describe('Moral Compass', () => {
    test('should reject financial crime targets', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'trojan',
          target: 'financial institution',
          description: 'Code for financial fraud',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(false);
      expect(result.violations.some(v => v.type === 'moral_compass')).toBe(true);
    });

    test('should reject civilian infrastructure targets', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'virus',
          target: 'hospital system',
          description: 'Test targeting hospital',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(false);
      expect(result.violations.some(v => v.type === 'moral_compass')).toBe(true);
    });

    test('should reject zero-day exploit requests', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'exploit',
          target: 'test',
          description: 'Generate zero-day exploit for unknown vulnerability',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(false);
      expect(result.violations.some(v => v.type === 'moral_compass')).toBe(true);
    });

    test('should warn about non-research purposes', async () => {
      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Generate code for production deployment',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(true); // Should be allowed but with warning
      expect(result.violations.some(v => v.type === 'moral_compass')).toBe(true);
      expect(result.violations.find(v => v.type === 'moral_compass')?.action).toBe('warned');
    });
  });

  describe('Consent Management', () => {
    test('should reject requests without consent when required', async () => {
      const strictConfig = { ...testConfig, requireExplicitConsent: true };
      const strictSafeguards = new EthicalSafeguards(strictConfig, accessControl);

      const result = await strictSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test without consent',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(false);
      expect(result.violations.some(v => v.type === 'consent_missing')).toBe(true);
    });

    test('should allow requests with valid consent', async () => {
      // Grant consent first
      await ethicalSafeguards.grantExplicitConsent(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test with consent',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test with consent',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(true);
      expect(result.violations.some(v => v.type === 'consent_missing')).toBe(false);
    });

    test('should expire consent after 24 hours', async () => {
      // Grant consent
      await ethicalSafeguards.grantExplicitConsent(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test consent expiry',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      // Manually expire consent (in real test, would wait 24 hours)
      const consentRecords = (ethicalSafeguards as any).consentRecords;
      const consentKey = 'razdor-backdoor-localhost';
      const consent = consentRecords.get(consentKey);
      if (consent) {
        consent.timestamp = new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(); // 25 hours ago
      }

      const result = await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test expired consent',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(false);
      expect(result.violations.some(v => v.type === 'consent_missing')).toBe(true);
    });
  });

  describe('Audit and Logging', () => {
    test('should log all validation attempts', async () => {
      const auditLogPath = path.join(testWorkspace, 'ethical-audit.log');
      
      // Perform validation
      await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test audit logging',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      // Check if log file was created
      expect(fs.existsSync(auditLogPath)).toBe(true);
      
      // Check log content
      const logContent = await fs.promises.readFile(auditLogPath, 'utf8');
      expect(logContent).toContain('razdor');
      expect(logContent).toContain('backdoor');
    });

    test('should track ethical violations', async () => {
      // Generate a violation
      await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'bank',
          description: 'Test violation tracking',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      const violations = ethicalSafeguards.getEthicalViolations();
      expect(violations.length).toBeGreaterThan(0);
      expect(violations.some(v => v.type === 'target_restriction')).toBe(true);
    });
  });

  describe('Configuration', () => {
    test('should respect disabled moral compass', async () => {
      const disabledConfig = { ...testConfig, enableMoralCompass: false };
      const disabledSafeguards = new EthicalSafeguards(disabledConfig, accessControl);

      const result = await disabledSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'financial institution',
          description: 'Test with disabled moral compass',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(true); // Should be allowed when moral compass is disabled
      expect(result.violations.some(v => v.type === 'moral_compass')).toBe(false);
    });

    test('should respect disabled license requirement', async () => {
      const noLicenseConfig = { ...testConfig, requireLicenseActivation: false };
      const noLicenseSafeguards = new EthicalSafeguards(noLicenseConfig, accessControl);

      const result = await noLicenseSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'localhost',
          description: 'Test without license requirement',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(result.allowed).toBe(true);
      expect(result.violations.some(v => v.type === 'license_invalid')).toBe(false);
    });
  });

  describe('Integration with Access Control', () => {
    test('should create security violations for blocked requests', async () => {
      // Mock access control to capture violations
      let violationCreated = false;
      accessControl.createSecurityViolation = async () => {
        violationCreated = true;
      };

      await ethicalSafeguards.validateGenerationRequest(
        'razdor',
        {
          type: 'backdoor',
          target: 'bank',
          description: 'Test security violation creation',
          complexityLevel: 3,
          userId: 'razdor'
        }
      );

      expect(violationCreated).toBe(true);
    });
  });
});
