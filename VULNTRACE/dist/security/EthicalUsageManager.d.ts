import { SecurityConfig, SecurityContext } from './types';
export declare class EthicalUsageManager {
    private static readonly WARNING_FILE;
    private static readonly WARNING_MESSAGE;
    private config;
    private warningAccepted;
    constructor(config: SecurityConfig);
    showEthicalWarning(): Promise<boolean>;
    private promptUser;
    private acceptWarning;
    private loadWarningStatus;
    private saveWarningStatus;
    validateUsage(context: SecurityContext): boolean;
    getEthicalGuidelines(): string[];
}
//# sourceMappingURL=EthicalUsageManager.d.ts.map