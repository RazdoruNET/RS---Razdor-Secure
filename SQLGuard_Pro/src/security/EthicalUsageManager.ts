import { SecurityConfig, EthicalUsageWarning, SecurityContext } from './types';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export class EthicalUsageManager {
  private static readonly WARNING_FILE = path.join(os.homedir(), '.sql-scanner-ethical-usage.json');
  private static readonly WARNING_MESSAGE = `Этот модуль создан для проверки ваших собственных серверов и сайтов. Он не должен использоваться для самотестирования чужих систем.`;
  
  private config: SecurityConfig;
  private warningAccepted: boolean = false;

  constructor(config: SecurityConfig) {
    this.config = config;
    this.loadWarningStatus();
  }

  async showEthicalWarning(): Promise<boolean> {
    if (this.warningAccepted && this.config.ethicalWarningAccepted) {
      return true;
    }

    const warning: EthicalUsageWarning = {
      id: 'ethical-usage-warning',
      title: 'Этические нормы использования',
      message: EthicalUsageManager.WARNING_MESSAGE,
      version: '1.0.0'
    };

    console.log('\n' + '='.repeat(60));
    console.log('⚠️  ВНИМАНИЕ: Этические нормы использования');
    console.log('='.repeat(60));
    console.log(warning.message);
    console.log('\nДопустимые сценарии использования:');
    console.log('• Разработка');
    console.log('• Внутренний аудит');
    console.log('• Локальная отладка');
    console.log('• Проверка собственных SQL-модулей');
    console.log('• Анализ корпоративных репозиториев внутри доверенного контура');
    console.log('\nИспользование для анализа сторонних ресурсов СТРОГО ЗАПРЕЩЕНО.');
    console.log('='.repeat(60));

    const answer = await this.promptUser('\nВы подтверждаете, что понимаете и принимаете эти условия? (y/N): ');
    
    if (answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes') {
      this.acceptWarning(warning);
      return true;
    }

    console.log('Использование модуля отменено.');
    return false;
  }

  private async promptUser(question: string): Promise<string> {
    process.stdout.write(question);
    
    return new Promise((resolve, reject) => {
      process.stdin.setRawMode(true);
      process.stdin.resume();
      process.stdin.setEncoding('utf8');
      
      let input = '';
      let isResolved = false;
      
      const cleanup = () => {
        if (!isResolved) {
          isResolved = true;
          process.stdin.setRawMode(false);
          process.stdin.pause();
          process.stdin.removeAllListeners('data');
          process.stdin.removeAllListeners('error');
        }
      };
      
      const onData = (key: Buffer | string) => {
        const keyStr = typeof key === 'string' ? key : key.toString();
        
        if (keyStr === '\r' || keyStr === '\n' || keyStr === '\u0003') {
          cleanup();
          resolve(input.trim());
        } else if (keyStr === '\u007F') {
          input = input.slice(0, -1);
        } else if (keyStr >= ' ' && keyStr <= '~') {
          input += keyStr;
        }
      };
      
      const onError = (error: Error) => {
        cleanup();
        reject(error);
      };
      
      process.stdin.on('data', onData);
      process.stdin.on('error', onError);
      
      // Add timeout
      const timeout = setTimeout(() => {
        cleanup();
        reject(new Error('User input timeout'));
      }, 30000);
    });
  }

  private acceptWarning(warning: EthicalUsageWarning): void {
    warning.acceptedAt = new Date().toISOString();
    this.warningAccepted = true;
    this.config.ethicalWarningAccepted = true;
    this.saveWarningStatus(warning);
  }

  private loadWarningStatus(): void {
    try {
      if (fs.existsSync(EthicalUsageManager.WARNING_FILE)) {
        const data = fs.readFileSync(EthicalUsageManager.WARNING_FILE, 'utf8');
        const warning = JSON.parse(data) as EthicalUsageWarning;
        this.warningAccepted = !!warning.acceptedAt;
      }
    } catch (error) {
      // File doesn't exist or is corrupted - require warning
      this.warningAccepted = false;
    }
  }

  private saveWarningStatus(warning: EthicalUsageWarning): void {
    try {
      const dir = path.dirname(EthicalUsageManager.WARNING_FILE);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(EthicalUsageManager.WARNING_FILE, JSON.stringify(warning, null, 2));
    } catch (error) {
      console.warn('Не удалось сохранить статус предупреждения:', error);
    }
  }

  validateUsage(context: SecurityContext): boolean {
    if (!this.warningAccepted) {
      return false;
    }

    if (!context.isTrusted) {
      console.error('Ошибка: Анализ вне доверенного рабочего пространства запрещен.');
      return false;
    }

    if (this.config.requireConfirmation && !context.hasUserConsent) {
      console.error('Ошибка: Требуется подтверждение пользователя для анализа.');
      return false;
    }

    return true;
  }

  getEthicalGuidelines(): string[] {
    return [
      'Инструмент предназначен исключительно для самотестирования собственных проектов',
      'Использование для анализа сторонних ресурсов строго запрещено',
      'Модуль функционирует в локальном изолированном контуре',
      'Все механизмы GPT-анализа поддерживают offline-режим',
      'Пользователь обязан подтверждать запуск анализа',
      'SQL-код не покидает контур разработки',
      'Режим "только чтение" активен по умолчанию',
      'Отсутствуют автоматические изменения анализируемого кода'
    ];
  }
}
