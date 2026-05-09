import { MaliciousSample } from '../security/types';
export interface CodeTemplate {
    id: string;
    name: string;
    type: 'virus' | 'trojan' | 'rootkit' | 'exploit' | 'backdoor';
    language: 'python' | 'javascript' | 'cpp' | 'powershell' | 'bash';
    template: string;
    variables: TemplateVariable[];
    evasionTechniques: EvasionTechnique[];
}
export interface TemplateVariable {
    name: string;
    type: 'string' | 'number' | 'boolean' | 'array';
    defaultValue: any;
    description: string;
}
export interface EvasionTechnique {
    id: string;
    name: string;
    description: string;
    implementation: string;
    category: 'anti-debug' | 'polymorphism' | 'encryption' | 'obfuscation' | 'anti-vm';
}
export interface GenerationConfig {
    targetThreatLevel: 'low' | 'medium' | 'high' | 'critical';
    includeEvasion: boolean;
    mutationRate: number;
    maxComplexity: number;
    allowedTechniques: string[];
}
export declare class MaliciousCodeConstructor {
    private templates;
    private geneticAlgorithm;
    private geneticConfig;
    constructor();
    private initializeTemplates;
    generateSample(templateId: string, config: GenerationConfig, customVariables?: Record<string, any>): Promise<MaliciousSample>;
    private resolveVariables;
    private generateVariableValue;
    private applyEvasionTechniques;
    private injectEvasionCode;
    private calculateThreatLevel;
    getAvailableTemplates(): CodeTemplate[];
    getTemplate(id: string): CodeTemplate | undefined;
    addTemplate(template: CodeTemplate): void;
    evolveTemplate(templateId: string, targetCharacteristics: string[]): Promise<CodeTemplate>;
}
//# sourceMappingURL=MaliciousCodeConstructor.d.ts.map