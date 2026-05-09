import { EventEmitter } from 'events';
export interface CryptoKeyPair {
    publicKey: string;
    privateKey: string;
    keyId: string;
    algorithm: string;
    keySize: number;
    createdAt: string;
}
export interface EncryptedData {
    data: string;
    algorithm: string;
    keyId: string;
    iv: string;
    tag?: string;
    timestamp: string;
}
export interface DigitalSignature {
    data: string;
    signature: string;
    algorithm: string;
    keyId: string;
    timestamp: string;
}
export interface KeyDerivationParams {
    algorithm: 'pbkdf2' | 'scrypt' | 'hkdf';
    iterations?: number;
    salt: string;
    keyLength: number;
    info?: string;
}
export declare class RealCryptoOperations extends EventEmitter {
    private keyStore;
    private keyStorePath;
    private defaultKeySize;
    private defaultAlgorithm;
    constructor(keyStorePath: string);
    generateKeyPair(algorithm?: 'rsa' | 'ec' | 'ed25519', keySize?: number): Promise<CryptoKeyPair>;
    generateSymmetricKey(algorithm?: string, keySize?: number): Promise<string>;
    encrypt(data: string | Buffer, key: string, algorithm?: string, additionalData?: string): Promise<EncryptedData>;
    decrypt(encryptedData: EncryptedData, key: string, additionalData?: string): Promise<Buffer>;
    sign(data: string | Buffer, keyId: string, algorithm?: string): Promise<DigitalSignature>;
    verify(signature: DigitalSignature, publicKey?: string, keyId?: string): Promise<boolean>;
    hash(data: string | Buffer, algorithm?: string): Promise<string>;
    deriveKey(password: string, params: KeyDerivationParams): Promise<string>;
    generateSecureRandom(bytes?: number): Promise<string>;
    encryptWithPublicKey(data: string | Buffer, publicKey: string): Promise<string>;
    decryptWithPrivateKey(encryptedData: string, privateKey: string): Promise<Buffer>;
    createHMAC(data: string | Buffer, key: string, algorithm?: string): Promise<string>;
    verifyHMAC(data: string | Buffer, key: string, signature: string, algorithm?: string): Promise<boolean>;
    generateCertificate(keyId: string, commonName: string, organization?: string, validityDays?: number): Promise<string>;
    verifyCertificate(certificate: string, publicKey?: string): Promise<boolean>;
    private loadKeyStore;
    private saveKeyStore;
    getKeyPair(keyId: string): CryptoKeyPair | undefined;
    listKeyPairs(): CryptoKeyPair[];
    deleteKeyPair(keyId: string): Promise<void>;
    rotateKeyPair(keyId: string, algorithm?: 'rsa' | 'ec' | 'ed25519', keySize?: number): Promise<CryptoKeyPair>;
    getCryptoInfo(): any;
    destroy(): void;
}
//# sourceMappingURL=RealCryptoOperations.d.ts.map