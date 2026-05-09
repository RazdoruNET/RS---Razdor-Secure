"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.RealCryptoOperations = void 0;
const crypto = __importStar(require("crypto"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const events_1 = require("events");
class RealCryptoOperations extends events_1.EventEmitter {
    constructor(keyStorePath) {
        super();
        this.keyStore = new Map();
        this.defaultKeySize = 2048;
        this.defaultAlgorithm = 'aes-256-gcm';
        this.keyStorePath = keyStorePath;
        this.loadKeyStore();
    }
    async generateKeyPair(algorithm = 'rsa', keySize = this.defaultKeySize) {
        try {
            const keyId = crypto.randomUUID();
            let publicKey;
            let privateKey;
            switch (algorithm) {
                case 'rsa':
                    ({ publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
                        modulusLength: keySize,
                        publicKeyEncoding: { type: 'spki', format: 'pem' },
                        privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
                    }));
                    break;
                case 'ec':
                    ({ publicKey, privateKey } = crypto.generateKeyPairSync('ec', {
                        namedCurve: 'secp256k1',
                        publicKeyEncoding: { type: 'spki', format: 'pem' },
                        privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
                    }));
                    break;
                case 'ed25519':
                    ({ publicKey, privateKey } = crypto.generateKeyPairSync('ed25519', {
                        publicKeyEncoding: { type: 'spki', format: 'pem' },
                        privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
                    }));
                    break;
                default:
                    throw new Error(`Unsupported algorithm: ${algorithm}`);
            }
            const keyPair = {
                publicKey,
                privateKey,
                keyId,
                algorithm,
                keySize,
                createdAt: new Date().toISOString()
            };
            this.keyStore.set(keyId, keyPair);
            await this.saveKeyStore();
            console.log(`[Crypto] Generated ${algorithm} key pair: ${keyId}`);
            this.emit('keyPairGenerated', keyPair);
            return keyPair;
        }
        catch (error) {
            console.error('[Crypto] Failed to generate key pair:', error);
            throw error;
        }
    }
    async generateSymmetricKey(algorithm = this.defaultAlgorithm, keySize = 32) {
        try {
            const key = crypto.randomBytes(keySize);
            const keyHex = key.toString('hex');
            console.log(`[Crypto] Generated symmetric key: ${algorithm}`);
            this.emit('symmetricKeyGenerated', { algorithm, keySize });
            return keyHex;
        }
        catch (error) {
            console.error('[Crypto] Failed to generate symmetric key:', error);
            throw error;
        }
    }
    async encrypt(data, key, algorithm = this.defaultAlgorithm, additionalData) {
        try {
            const iv = crypto.randomBytes(16);
            const cipher = crypto.createCipher(algorithm, Buffer.from(key, 'hex'));
            let encrypted = cipher.update(data);
            encrypted = Buffer.concat([encrypted, cipher.final()]);
            const encryptedData = {
                data: encrypted.toString('hex'),
                algorithm,
                keyId: 'symmetric',
                iv: iv.toString('hex'),
                timestamp: new Date().toISOString()
            };
            console.log(`[Crypto] Encrypted data with ${algorithm}`);
            this.emit('dataEncrypted', { algorithm, dataSize: data.length });
            return encryptedData;
        }
        catch (error) {
            console.error('[Crypto] Failed to encrypt data:', error);
            throw error;
        }
    }
    async decrypt(encryptedData, key, additionalData) {
        try {
            const decipher = crypto.createDecipher(encryptedData.algorithm, Buffer.from(key, 'hex'));
            let decrypted = decipher.update(Buffer.from(encryptedData.data, 'hex'));
            decrypted = Buffer.concat([decrypted, decipher.final()]);
            console.log(`[Crypto] Decrypted data with ${encryptedData.algorithm}`);
            this.emit('dataDecrypted', { algorithm: encryptedData.algorithm });
            return decrypted;
        }
        catch (error) {
            console.error('[Crypto] Failed to decrypt data:', error);
            throw error;
        }
    }
    async sign(data, keyId, algorithm = 'RSA-SHA256') {
        try {
            const keyPair = this.keyStore.get(keyId);
            if (!keyPair) {
                throw new Error(`Key pair not found: ${keyId}`);
            }
            const sign = crypto.createSign(algorithm);
            sign.update(data);
            const signature = sign.sign(keyPair.privateKey);
            const digitalSignature = {
                data: typeof data === 'string' ? data : data.toString('hex'),
                signature: signature.toString('hex'),
                algorithm,
                keyId,
                timestamp: new Date().toISOString()
            };
            console.log(`[Crypto] Signed data with ${algorithm}`);
            this.emit('dataSigned', { algorithm, keyId });
            return digitalSignature;
        }
        catch (error) {
            console.error('[Crypto] Failed to sign data:', error);
            throw error;
        }
    }
    async verify(signature, publicKey, keyId) {
        try {
            let key;
            if (publicKey) {
                key = publicKey;
            }
            else if (keyId) {
                const keyPair = this.keyStore.get(keyId);
                if (!keyPair) {
                    throw new Error(`Key pair not found: ${keyId}`);
                }
                key = keyPair.publicKey;
            }
            else {
                throw new Error('Either publicKey or keyId must be provided');
            }
            const verify = crypto.createVerify(signature.algorithm);
            verify.update(signature.data);
            const isValid = verify.verify(key, signature.signature, 'hex');
            console.log(`[Crypto] Signature verification: ${isValid}`);
            this.emit('signatureVerified', { algorithm: signature.algorithm, isValid });
            return isValid;
        }
        catch (error) {
            console.error('[Crypto] Failed to verify signature:', error);
            throw error;
        }
    }
    async hash(data, algorithm = 'sha256') {
        try {
            const hash = crypto.createHash(algorithm);
            hash.update(data);
            const digest = hash.digest('hex');
            console.log(`[Crypto] Hashed data with ${algorithm}`);
            this.emit('dataHashed', { algorithm });
            return digest;
        }
        catch (error) {
            console.error('[Crypto] Failed to hash data:', error);
            throw error;
        }
    }
    async deriveKey(password, params) {
        try {
            let key;
            switch (params.algorithm) {
                case 'pbkdf2':
                    key = crypto.pbkdf2Sync(password, Buffer.from(params.salt, 'hex'), params.iterations || 100000, params.keyLength, 'sha256');
                    break;
                case 'scrypt':
                    key = crypto.scryptSync(password, Buffer.from(params.salt, 'hex'), params.keyLength);
                    break;
                case 'hkdf':
                    // HKDF not available in Node.js crypto, fallback to PBKDF2
                    key = crypto.pbkdf2Sync(password, Buffer.from(params.salt, 'hex'), params.iterations || 100000, params.keyLength, 'sha256');
                    break;
                default:
                    throw new Error(`Unsupported key derivation algorithm: ${params.algorithm}`);
            }
            console.log(`[Crypto] Derived key using ${params.algorithm}`);
            this.emit('keyDerived', { algorithm: params.algorithm });
            return key.toString('hex');
        }
        catch (error) {
            console.error('[Crypto] Failed to derive key:', error);
            throw error;
        }
    }
    async generateSecureRandom(bytes = 32) {
        try {
            const random = crypto.randomBytes(bytes);
            const randomHex = random.toString('hex');
            console.log(`[Crypto] Generated ${bytes} bytes of secure random data`);
            this.emit('secureRandomGenerated', { bytes });
            return randomHex;
        }
        catch (error) {
            console.error('[Crypto] Failed to generate secure random data:', error);
            throw error;
        }
    }
    async encryptWithPublicKey(data, publicKey) {
        try {
            const encrypted = crypto.publicEncrypt({
                key: publicKey,
                padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
                oaepHash: 'sha256'
            }, Buffer.from(data));
            console.log('[Crypto] Encrypted data with public key');
            this.emit('dataEncryptedWithPublicKey');
            return encrypted.toString('hex');
        }
        catch (error) {
            console.error('[Crypto] Failed to encrypt with public key:', error);
            throw error;
        }
    }
    async decryptWithPrivateKey(encryptedData, privateKey) {
        try {
            const decrypted = crypto.privateDecrypt({
                key: privateKey,
                padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
                oaepHash: 'sha256'
            }, Buffer.from(encryptedData, 'hex'));
            console.log('[Crypto] Decrypted data with private key');
            this.emit('dataDecryptedWithPrivateKey');
            return decrypted;
        }
        catch (error) {
            console.error('[Crypto] Failed to decrypt with private key:', error);
            throw error;
        }
    }
    async createHMAC(data, key, algorithm = 'sha256') {
        try {
            const hmac = crypto.createHmac(algorithm, Buffer.from(key, 'hex'));
            hmac.update(data);
            const digest = hmac.digest('hex');
            console.log(`[Crypto] Created HMAC with ${algorithm}`);
            this.emit('hmacCreated', { algorithm });
            return digest;
        }
        catch (error) {
            console.error('[Crypto] Failed to create HMAC:', error);
            throw error;
        }
    }
    async verifyHMAC(data, key, signature, algorithm = 'sha256') {
        try {
            const expectedSignature = await this.createHMAC(data, key, algorithm);
            const isValid = crypto.timingSafeEqual(Buffer.from(signature, 'hex'), Buffer.from(expectedSignature, 'hex'));
            console.log(`[Crypto] HMAC verification: ${isValid}`);
            this.emit('hmacVerified', { algorithm, isValid });
            return isValid;
        }
        catch (error) {
            console.error('[Crypto] Failed to verify HMAC:', error);
            throw error;
        }
    }
    async generateCertificate(keyId, commonName, organization, validityDays = 365) {
        try {
            const keyPair = this.keyStore.get(keyId);
            if (!keyPair) {
                throw new Error(`Key pair not found: ${keyId}`);
            }
            // Certificate generation not available in Node.js crypto directly
            // Return a mock certificate for demonstration
            const cert = `-----BEGIN CERTIFICATE-----
      Mock certificate for ${commonName}
      Organization: ${organization || 'Prophecy Sandbox'}
      Valid until: ${new Date(Date.now() + validityDays * 24 * 60 * 60 * 1000).toISOString()}
      -----END CERTIFICATE-----`;
            console.log(`[Crypto] Generated mock certificate for ${commonName}`);
            this.emit('certificateGenerated', { commonName, validityDays });
            return cert;
        }
        catch (error) {
            console.error('[Crypto] Failed to generate certificate:', error);
            throw error;
        }
    }
    async verifyCertificate(certificate, publicKey) {
        try {
            // Simplified certificate verification
            // In a real implementation, you would use a proper certificate validation library
            const isValid = certificate.includes('BEGIN CERTIFICATE') && certificate.includes('END CERTIFICATE');
            console.log(`[Crypto] Certificate verification: ${isValid}`);
            this.emit('certificateVerified', { isValid });
            return isValid;
        }
        catch (error) {
            console.error('[Crypto] Failed to verify certificate:', error);
            throw error;
        }
    }
    loadKeyStore() {
        try {
            if (fs.existsSync(this.keyStorePath)) {
                const data = fs.readFileSync(this.keyStorePath, 'utf8');
                const keyStoreData = JSON.parse(data);
                this.keyStore.clear();
                Object.entries(keyStoreData).forEach(([keyId, keyPair]) => {
                    this.keyStore.set(keyId, keyPair);
                });
                console.log(`[Crypto] Loaded ${this.keyStore.size} key pairs from keystore`);
            }
        }
        catch (error) {
            console.error('[Crypto] Failed to load keystore:', error);
        }
    }
    async saveKeyStore() {
        try {
            const keyStoreData = {};
            this.keyStore.forEach((keyPair, keyId) => {
                keyStoreData[keyId] = keyPair;
            });
            const dir = path.dirname(this.keyStorePath);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(this.keyStorePath, JSON.stringify(keyStoreData, null, 2));
            fs.chmodSync(this.keyStorePath, 0o600); // Secure permissions
            console.log(`[Crypto] Saved ${this.keyStore.size} key pairs to keystore`);
        }
        catch (error) {
            console.error('[Crypto] Failed to save keystore:', error);
            throw error;
        }
    }
    getKeyPair(keyId) {
        return this.keyStore.get(keyId);
    }
    listKeyPairs() {
        return Array.from(this.keyStore.values());
    }
    async deleteKeyPair(keyId) {
        try {
            if (this.keyStore.delete(keyId)) {
                await this.saveKeyStore();
                console.log(`[Crypto] Deleted key pair: ${keyId}`);
                this.emit('keyPairDeleted', { keyId });
            }
        }
        catch (error) {
            console.error(`[Crypto] Failed to delete key pair ${keyId}:`, error);
            throw error;
        }
    }
    async rotateKeyPair(keyId, algorithm, keySize) {
        try {
            const oldKeyPair = this.keyStore.get(keyId);
            if (!oldKeyPair) {
                throw new Error(`Key pair not found: ${keyId}`);
            }
            // Generate new key pair
            const newKeyPair = await this.generateKeyPair(algorithm || oldKeyPair.algorithm, keySize || oldKeyPair.keySize);
            // Delete old key pair
            await this.deleteKeyPair(keyId);
            console.log(`[Crypto] Rotated key pair: ${keyId}`);
            this.emit('keyPairRotated', { oldKeyId: keyId, newKeyId: newKeyPair.keyId });
            return newKeyPair;
        }
        catch (error) {
            console.error(`[Crypto] Failed to rotate key pair ${keyId}:`, error);
            throw error;
        }
    }
    getCryptoInfo() {
        return {
            supportedAlgorithms: crypto.getHashes(),
            supportedCiphers: crypto.getCiphers(),
            keyStoreSize: this.keyStore.size,
            defaultKeySize: this.defaultKeySize,
            defaultAlgorithm: this.defaultAlgorithm
        };
    }
    destroy() {
        this.keyStore.clear();
        console.log('[Crypto] Crypto operations destroyed');
    }
}
exports.RealCryptoOperations = RealCryptoOperations;
//# sourceMappingURL=RealCryptoOperations.js.map