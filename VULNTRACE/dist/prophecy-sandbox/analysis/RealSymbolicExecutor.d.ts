import { EventEmitter } from 'events';
export interface SymbolicState {
    variables: Map<string, SymbolicValue>;
    memory: Map<number, SymbolicValue>;
    registers: Map<string, SymbolicValue>;
    pathConstraints: string[];
    stack: SymbolicValue[];
    heap: Map<number, SymbolicValue>;
}
export interface SymbolicValue {
    id: string;
    type: 'concrete' | 'symbolic' | 'mixed';
    value?: any;
    expression?: string;
    constraints?: string[];
    dependencies?: string[];
    size: number;
}
export interface ExecutionPath {
    id: string;
    state: SymbolicState;
    instructions: Instruction[];
    constraints: string[];
    feasible: boolean;
    explored: boolean;
    depth: number;
    branchConditions: string[];
}
export interface Instruction {
    address: number;
    mnemonic: string;
    operands: string[];
    type: 'arithmetic' | 'logic' | 'memory' | 'branch' | 'call' | 'return' | 'other';
    size: number;
    bytes: Buffer;
}
export interface AnalysisConfig {
    targetPath: string;
    maxDepth: number;
    maxPaths: number;
    timeout: number;
    concreteExecution: boolean;
    taintAnalysis: boolean;
    constraintSolver: 'z3' | 'stp' | 'cvc4';
    memoryModel: 'flat' | 'segmented';
    callingConvention: 'cdecl' | 'stdcall' | 'fastcall';
}
export declare class RealSymbolicExecutor extends EventEmitter {
    private config;
    private isExecuting;
    private paths;
    private currentPath;
    private instructions;
    private symbolicVariables;
    private taintSources;
    private taintSinks;
    constructor(config: AnalysisConfig);
    private initializeTaintTracking;
    startExecution(): Promise<void>;
    private disassembleBinary;
    private parseDisassembly;
    private generateFallbackDisassembly;
    private categorizeInstruction;
    private initializeExecution;
    private createConcreteValue;
    private createSymbolicValue;
    private createMixedValue;
    private executeSymbolically;
    private executePath;
    private executeInstruction;
    private executeArithmetic;
    private executeLogic;
    private executeMemory;
    private executeBranch;
    private executeCall;
    private executeReturn;
    private executeOther;
    private getOperandValue;
    private setOperandValue;
    private evaluateExpression;
    private performAdd;
    private performSub;
    private performCmp;
    private performTest;
    private clonePath;
    private negateConstraint;
    stopExecution(): void;
    getResults(): any;
    generateReport(format?: 'json' | 'dot'): string;
    getStatistics(): any;
    destroy(): void;
}
//# sourceMappingURL=RealSymbolicExecutor.d.ts.map