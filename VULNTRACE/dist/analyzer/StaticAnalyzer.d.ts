import { SQLQuery, Vulnerability, AnalysisContext, AppConfig } from '../types';
export declare class StaticAnalyzer {
    private config;
    private rules;
    constructor(config: AppConfig);
    analyze(queries: SQLQuery[], context: AnalysisContext): Promise<Vulnerability[]>;
    private analyzeQuery;
    private shouldApplyRule;
    private filterIgnoredRules;
    private initializeRules;
}
//# sourceMappingURL=StaticAnalyzer.d.ts.map