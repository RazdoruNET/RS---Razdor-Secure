import * as fs from 'fs';
import * as path from 'path';

export class SecurePathValidator {
  private static readonly ALLOWED_EXTENSIONS = ['.sql', '.js', '.ts', '.json', '.md'];
  private static readonly MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  static validatePath(filePath: string, workspaceRoot: string): {
    isValid: boolean;
    error?: string;
    realPath?: string;
  } {
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
    } catch (error) {
      return { isValid: false, error: `Path validation failed: ${(error as Error).message}` };
    }
  }

  static sanitizePath(filePath: string): string {
    // Remove dangerous characters
    return filePath
      .replace(/\.\./g, '')
      .replace(/[<>:"|?*]/g, '')
      .trim();
  }
}
