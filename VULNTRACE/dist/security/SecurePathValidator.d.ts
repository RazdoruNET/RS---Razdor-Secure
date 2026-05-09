export declare class SecurePathValidator {
    private static readonly ALLOWED_EXTENSIONS;
    private static readonly MAX_FILE_SIZE;
    static validatePath(filePath: string, workspaceRoot: string): {
        isValid: boolean;
        error?: string;
        realPath?: string;
    };
    static sanitizePath(filePath: string): string;
}
//# sourceMappingURL=SecurePathValidator.d.ts.map