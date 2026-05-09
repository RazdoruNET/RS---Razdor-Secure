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
exports.SecureInputHandler = void 0;
const readline = __importStar(require("readline"));
class SecureInputHandler {
    static async promptUser(question) {
        return new Promise((resolve, reject) => {
            // Use readline instead of raw stdin manipulation
            const rl = readline.createInterface({
                input: process.stdin,
                output: process.stdout
            });
            let isResolved = false;
            const cleanup = () => {
                if (!isResolved) {
                    isResolved = true;
                    rl.close();
                }
            };
            const timeout = setTimeout(() => {
                cleanup();
                reject(new Error('User input timeout'));
            }, this.TIMEOUT);
            try {
                rl.question(question, (answer) => {
                    clearTimeout(timeout);
                    cleanup();
                    // Validate input
                    if (answer.length > this.MAX_INPUT_LENGTH) {
                        reject(new Error('Input too long'));
                        return;
                    }
                    // Sanitize input
                    const sanitized = answer
                        .replace(/[\x00-\x1F\x7F]/g, '') // Remove control characters
                        .trim();
                    if (sanitized.length === 0) {
                        reject(new Error('Empty input not allowed'));
                        return;
                    }
                    resolve(sanitized);
                });
            }
            catch (error) {
                clearTimeout(timeout);
                cleanup();
                reject(error);
            }
        });
    }
    static async confirmAction(message) {
        try {
            const answer = await this.promptUser(`${message} (y/N): `);
            return ['y', 'yes', 'Y', 'YES'].includes(answer.toLowerCase());
        }
        catch (error) {
            return false; // Default to safe option
        }
    }
}
exports.SecureInputHandler = SecureInputHandler;
SecureInputHandler.MAX_INPUT_LENGTH = 1000;
SecureInputHandler.TIMEOUT = 30000;
//# sourceMappingURL=SecureInputHandler.js.map