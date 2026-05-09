import * as readline from 'readline';

export class SecureInputHandler {
  private static readonly MAX_INPUT_LENGTH = 1000;
  private static readonly TIMEOUT = 30000;

  static async promptUser(question: string): Promise<string> {
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
      } catch (error) {
        clearTimeout(timeout);
        cleanup();
        reject(error);
      }
    });
  }

  static async confirmAction(message: string): Promise<boolean> {
    try {
      const answer = await this.promptUser(`${message} (y/N): `);
      return ['y', 'yes', 'Y', 'YES'].includes(answer.toLowerCase());
    } catch (error) {
      return false; // Default to safe option
    }
  }
}
