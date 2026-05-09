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
exports.EthicalUsageManager = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const os = __importStar(require("os"));
class EthicalUsageManager {
    constructor(config) {
        this.warningAccepted = false;
        this.config = config;
        this.loadWarningStatus();
    }
    async showEthicalWarning() {
        if (this.warningAccepted && this.config.ethicalWarningAccepted) {
            return true;
        }
        const warning = {
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
    async promptUser(question) {
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
            const onData = (key) => {
                const keyStr = typeof key === 'string' ? key : key.toString();
                if (keyStr === '\r' || keyStr === '\n' || keyStr === '\u0003') {
                    cleanup();
                    resolve(input.trim());
                }
                else if (keyStr === '\u007F') {
                    input = input.slice(0, -1);
                }
                else if (keyStr >= ' ' && keyStr <= '~') {
                    input += keyStr;
                }
            };
            const onError = (error) => {
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
    acceptWarning(warning) {
        warning.acceptedAt = new Date().toISOString();
        this.warningAccepted = true;
        this.config.ethicalWarningAccepted = true;
        this.saveWarningStatus(warning);
    }
    loadWarningStatus() {
        try {
            if (fs.existsSync(EthicalUsageManager.WARNING_FILE)) {
                const data = fs.readFileSync(EthicalUsageManager.WARNING_FILE, 'utf8');
                const warning = JSON.parse(data);
                this.warningAccepted = !!warning.acceptedAt;
            }
        }
        catch (error) {
            // File doesn't exist or is corrupted - require warning
            this.warningAccepted = false;
        }
    }
    saveWarningStatus(warning) {
        try {
            const dir = path.dirname(EthicalUsageManager.WARNING_FILE);
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
            fs.writeFileSync(EthicalUsageManager.WARNING_FILE, JSON.stringify(warning, null, 2));
        }
        catch (error) {
            console.warn('Не удалось сохранить статус предупреждения:', error);
        }
    }
    validateUsage(context) {
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
    getEthicalGuidelines() {
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
exports.EthicalUsageManager = EthicalUsageManager;
EthicalUsageManager.WARNING_FILE = path.join(os.homedir(), '.sql-scanner-ethical-usage.json');
EthicalUsageManager.WARNING_MESSAGE = `Этот модуль создан для проверки ваших собственных серверов и сайтов. Он не должен использоваться для самотестирования чужих систем.`;
//# sourceMappingURL=EthicalUsageManager.js.map