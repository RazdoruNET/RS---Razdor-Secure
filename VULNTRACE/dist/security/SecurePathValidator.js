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
exports.SecurePathValidator = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class SecurePathValidator {
    static validatePath(filePath, workspaceRoot) {
        try {
            // 1. Basic input validation
            if (!filePath || typeof filePath !== 'string') {
                return { isValid: false, error: 'Invalid file path' };
            }
            // 2. Resolve all symlinks and get real path
            const realPath = fs.realpathSync(filePath);
            const realWorkspace = fs.realpathSync(workspaceRoot);
            // 3. Check if real path is within workspace
            const relative = path.relative(realWorkspace, realPath);
            if (relative.startsWith('..') || path.isAbsolute(relative)) {
                return { isValid: false, error: 'Path traversal attempt detected' };
            }
            // 4. Check file extension
            const ext = path.extname(realPath).toLowerCase();
            if (!this.ALLOWED_EXTENSIONS.includes(ext)) {
                return { isValid: false, error: `File type ${ext} not allowed` };
            }
            // 5. Check file size
            const stats = fs.statSync(realPath);
            if (stats.size > this.MAX_FILE_SIZE) {
                return { isValid: false, error: 'File too large' };
            }
            // 6. Check if it's actually a file
            if (!stats.isFile()) {
                return { isValid: false, error: 'Path is not a file' };
            }
            return { isValid: true, realPath };
        }
        catch (error) {
            return { isValid: false, error: `Path validation failed: ${error.message}` };
        }
    }
    static sanitizePath(filePath) {
        // Remove dangerous characters
        return filePath
            .replace(/\.\./g, '')
            .replace(/[<>:"|?*]/g, '')
            .trim();
    }
}
exports.SecurePathValidator = SecurePathValidator;
SecurePathValidator.ALLOWED_EXTENSIONS = ['.sql', '.js', '.ts', '.json', '.md'];
SecurePathValidator.MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
//# sourceMappingURL=SecurePathValidator.js.map