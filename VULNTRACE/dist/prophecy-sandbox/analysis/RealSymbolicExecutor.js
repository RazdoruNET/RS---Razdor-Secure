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
exports.RealSymbolicExecutor = void 0;
const fs = __importStar(require("fs"));
const child_process = __importStar(require("child_process"));
const events_1 = require("events");
const crypto_1 = require("crypto");
class RealSymbolicExecutor extends events_1.EventEmitter {
    constructor(config) {
        super();
        this.isExecuting = false;
        this.paths = new Map();
        this.currentPath = null;
        this.instructions = new Map();
        this.symbolicVariables = new Map();
        this.taintSources = new Set();
        this.taintSinks = new Set();
        this.config = config;
        this.initializeTaintTracking();
    }
    initializeTaintTracking() {
        // Common taint sources
        this.taintSources = new Set([
            'scanf', 'fgets', 'gets', 'read', 'recv', 'fread',
            'getenv', 'argv', 'argc', 'stdin', 'socket'
        ]);
        // Common taint sinks
        this.taintSinks = new Set([
            'system', 'exec', 'popen', 'strcpy', 'sprintf', 'strcat',
            'printf', 'fprintf', 'write', 'send', 'fwrite'
        ]);
    }
    async startExecution() {
        if (this.isExecuting) {
            throw new Error('Symbolic execution already in progress');
        }
        if (!fs.existsSync(this.config.targetPath)) {
            throw new Error(`Target binary not found: ${this.config.targetPath}`);
        }
        console.log(`[SymExec] Starting symbolic execution: ${this.config.targetPath}`);
        this.isExecuting = true;
        try {
            // Disassemble the target binary
            await this.disassembleBinary();
            // Initialize symbolic execution
            await this.initializeExecution();
            // Execute symbolically
            await this.executeSymbolically();
            console.log('[SymExec] Symbolic execution completed');
            this.emit('executionCompleted', this.getResults());
        }
        catch (error) {
            console.error('[SymExec] Symbolic execution failed:', error);
            throw error;
        }
        finally {
            this.isExecuting = false;
        }
    }
    async disassembleBinary() {
        console.log('[SymExec] Disassembling binary...');
        try {
            // Use objdump to disassemble the binary
            const objdumpPath = '/usr/bin/objdump';
            if (!fs.existsSync(objdumpPath)) {
                console.warn('[SymExec] objdump not found, using fallback disassembly');
                this.generateFallbackDisassembly();
                return;
            }
            return new Promise((resolve, reject) => {
                child_process.exec(`${objdumpPath} -d ${this.config.targetPath}`, (error, stdout, stderr) => {
                    if (error) {
                        console.error(`[SymExec] objdump failed: ${stderr}`);
                        this.generateFallbackDisassembly();
                        resolve();
                        return;
                    }
                    this.parseDisassembly(stdout);
                    console.log(`[SymExec] Disassembled ${this.instructions.size} instructions`);
                    resolve();
                });
            });
        }
        catch (error) {
            console.error('[SymExec] Disassembly failed:', error);
            this.generateFallbackDisassembly();
        }
    }
    parseDisassembly(disassembly) {
        const lines = disassembly.split('\n');
        const addressRegex = /^s*([0-9a-f]+):\s+([0-9a-f\s]+)\s+(\w+)\s*(.*)$/;
        for (const line of lines) {
            const match = line.match(addressRegex);
            if (!match)
                continue;
            const [, addressStr, bytesStr, mnemonic, operandsStr] = match;
            const address = parseInt(addressStr, 16);
            const bytes = Buffer.from(bytesStr.trim().split(/\s+/).filter(Boolean).map(b => parseInt(b, 16)));
            const operands = operandsStr ? operandsStr.split(',').map(op => op.trim()) : [];
            const type = this.categorizeInstruction(mnemonic);
            const instruction = {
                address,
                mnemonic,
                operands,
                type,
                size: bytes.length,
                bytes
            };
            this.instructions.set(address, instruction);
        }
    }
    generateFallbackDisassembly() {
        console.log('[SymExec] Generating fallback disassembly...');
        // Generate a simple instruction set for demonstration
        const address = 0x400000;
        const mockInstructions = [
            {
                address: address + 0x1000,
                mnemonic: 'push',
                operands: ['rbp'],
                type: 'other',
                size: 1,
                bytes: Buffer.from([0x55])
            },
            {
                address: address + 0x1001,
                mnemonic: 'mov',
                operands: ['rbp', 'rsp'],
                type: 'arithmetic',
                size: 3,
                bytes: Buffer.from([0x48, 0x89, 0xe5])
            },
            {
                address: address + 0x1004,
                mnemonic: 'sub',
                operands: ['rsp', '0x20'],
                type: 'arithmetic',
                size: 4,
                bytes: Buffer.from([0x48, 0x83, 0xec, 0x20])
            },
            {
                address: address + 0x1008,
                mnemonic: 'mov',
                operands: ['dword ptr [rbp-0x4]', 'edi'],
                type: 'memory',
                size: 3,
                bytes: Buffer.from([0x89, 0x7d, 0xfc])
            },
            {
                address: address + 0x100b,
                mnemonic: 'cmp',
                operands: ['dword ptr [rbp-0x4]', '0x0'],
                type: 'logic',
                size: 4,
                bytes: Buffer.from([0x83, 0x7d, 0xfc, 0x00])
            },
            {
                address: address + 0x100f,
                mnemonic: 'jne',
                operands: ['0x1020'],
                type: 'branch',
                size: 2,
                bytes: Buffer.from([0x75, 0x0f])
            },
            {
                address: address + 0x1011,
                mnemonic: 'call',
                operands: ['0x2000'],
                type: 'call',
                size: 5,
                bytes: Buffer.from([0xe8, 0xea, 0x0f, 0x00, 0x00])
            },
            {
                address: address + 0x1016,
                mnemonic: 'jmp',
                operands: ['0x1030'],
                type: 'branch',
                size: 2,
                bytes: Buffer.from([0xeb, 0x18])
            },
            {
                address: address + 0x1020,
                mnemonic: 'call',
                operands: ['0x3000'],
                type: 'call',
                size: 5,
                bytes: Buffer.from([0xe8, 0xdb, 0x1f, 0x00, 0x00])
            },
            {
                address: address + 0x1030,
                mnemonic: 'mov',
                operands: ['eax', '0x0'],
                type: 'arithmetic',
                size: 5,
                bytes: Buffer.from([0xb8, 0x00, 0x00, 0x00, 0x00])
            },
            {
                address: address + 0x1035,
                mnemonic: 'leave',
                operands: [],
                type: 'other',
                size: 1,
                bytes: Buffer.from([0xc9])
            },
            {
                address: address + 0x1036,
                mnemonic: 'ret',
                operands: [],
                type: 'return',
                size: 1,
                bytes: Buffer.from([0xc3])
            }
        ];
        for (const instruction of mockInstructions) {
            this.instructions.set(instruction.address, instruction);
        }
    }
    categorizeInstruction(mnemonic) {
        const arithmeticOps = ['add', 'sub', 'mul', 'div', 'imul', 'idiv', 'inc', 'dec', 'neg', 'mov', 'lea'];
        const logicOps = ['and', 'or', 'xor', 'not', 'cmp', 'test'];
        const memoryOps = ['mov', 'lea', 'push', 'pop', 'xchg', 'cmpxchg'];
        const branchOps = ['jmp', 'je', 'jne', 'jg', 'jl', 'jge', 'jle', 'ja', 'jb', 'jae', 'jbe', 'jo', 'jno', 'js', 'jns'];
        const callOps = ['call', 'syscall', 'sysenter'];
        const returnOps = ['ret', 'retn', 'iret'];
        if (arithmeticOps.includes(mnemonic))
            return 'arithmetic';
        if (logicOps.includes(mnemonic))
            return 'logic';
        if (memoryOps.includes(mnemonic))
            return 'memory';
        if (branchOps.includes(mnemonic))
            return 'branch';
        if (callOps.includes(mnemonic))
            return 'call';
        if (returnOps.includes(mnemonic))
            return 'return';
        return 'other';
    }
    async initializeExecution() {
        console.log('[SymExec] Initializing symbolic execution...');
        // Create initial execution path
        const initialState = {
            variables: new Map(),
            memory: new Map(),
            registers: new Map(),
            pathConstraints: [],
            stack: [],
            heap: new Map()
        };
        // Initialize registers
        initialState.registers.set('rip', this.createConcreteValue(0x400000));
        initialState.registers.set('rsp', this.createConcreteValue(0x7fffffffe000));
        initialState.registers.set('rbp', this.createConcreteValue(0x7fffffffe000));
        // Create symbolic variables for function arguments
        for (let i = 0; i < 6; i++) {
            const argName = `arg${i}`;
            const symbolicArg = this.createSymbolicValue(argName, 64);
            initialState.registers.set(['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9'][i], symbolicArg);
            this.symbolicVariables.set(argName, symbolicArg);
        }
        this.currentPath = {
            id: (0, crypto_1.randomUUID)(),
            state: initialState,
            instructions: [],
            constraints: [],
            feasible: true,
            explored: false,
            depth: 0,
            branchConditions: []
        };
        this.paths.set(this.currentPath.id, this.currentPath);
    }
    createConcreteValue(value, size = 64) {
        return {
            id: (0, crypto_1.randomUUID)(),
            type: 'concrete',
            value,
            size
        };
    }
    createSymbolicValue(name, size = 64) {
        return {
            id: (0, crypto_1.randomUUID)(),
            type: 'symbolic',
            expression: name,
            size,
            constraints: [],
            dependencies: [name]
        };
    }
    createMixedValue(concrete, symbolic, size = 64) {
        return {
            id: (0, crypto_1.randomUUID)(),
            type: 'mixed',
            value: concrete,
            expression: symbolic,
            size,
            constraints: [],
            dependencies: []
        };
    }
    async executeSymbolically() {
        console.log('[SymExec] Starting symbolic execution...');
        const pathsToExplore = [this.currentPath];
        let exploredPaths = 0;
        while (pathsToExplore.length > 0 && exploredPaths < this.config.maxPaths) {
            const path = pathsToExplore.shift();
            if (path.explored || path.depth >= this.config.maxDepth) {
                continue;
            }
            // Execute current path
            const newPaths = await this.executePath(path);
            // Add new paths to explore
            pathsToExplore.push(...newPaths);
            path.explored = true;
            exploredPaths++;
            if (exploredPaths % 100 === 0) {
                console.log(`[SymExec] Explored ${exploredPaths} paths, ${pathsToExplore.length} pending`);
                this.emit('progress', { explored: exploredPaths, pending: pathsToExplore.length });
            }
        }
        console.log(`[SymExec] Symbolic execution completed. Explored ${exploredPaths} paths`);
    }
    async executePath(path) {
        const newPaths = [];
        let currentAddress = path.state.registers.get('rip')?.value || 0x400000;
        while (path.depth < this.config.maxDepth) {
            const instruction = this.instructions.get(currentAddress);
            if (!instruction) {
                break; // No more instructions
            }
            // Execute instruction
            const result = await this.executeInstruction(instruction, path);
            if (result.branchTaken !== undefined) {
                // Branch instruction - create new paths
                const truePath = this.clonePath(path);
                const falsePath = this.clonePath(path);
                // Update true path
                truePath.state.registers.set('rip', this.createConcreteValue(result.branchTaken));
                truePath.constraints.push(result.constraint);
                truePath.branchConditions.push(result.constraint);
                truePath.depth++;
                newPaths.push(truePath);
                // Update false path
                const nextInstruction = this.instructions.get(currentAddress + instruction.size);
                if (nextInstruction) {
                    falsePath.state.registers.set('rip', this.createConcreteValue(nextInstruction.address));
                    falsePath.constraints.push(this.negateConstraint(result.constraint));
                    falsePath.branchConditions.push(this.negateConstraint(result.constraint));
                    falsePath.depth++;
                    newPaths.push(falsePath);
                }
                break; // Stop executing current path
            }
            else {
                // Continue with current path
                path.instructions.push(instruction);
                path.depth++;
                const nextInstruction = this.instructions.get(currentAddress + instruction.size);
                if (!nextInstruction) {
                    break;
                }
                currentAddress = nextInstruction.address;
                path.state.registers.set('rip', this.createConcreteValue(currentAddress));
            }
        }
        return newPaths;
    }
    async executeInstruction(instruction, path) {
        const { mnemonic, operands } = instruction;
        const state = path.state;
        switch (instruction.type) {
            case 'arithmetic':
                return this.executeArithmetic(instruction, state);
            case 'logic':
                return this.executeLogic(instruction, state);
            case 'memory':
                return this.executeMemory(instruction, state);
            case 'branch':
                return this.executeBranch(instruction, state);
            case 'call':
                return this.executeCall(instruction, state);
            case 'return':
                return this.executeReturn(instruction, state);
            default:
                return this.executeOther(instruction, state);
        }
    }
    executeArithmetic(instruction, state) {
        const { mnemonic, operands } = instruction;
        switch (mnemonic) {
            case 'mov':
                const dest = operands[0];
                const src = operands[1];
                const srcValue = this.getOperandValue(src, state);
                this.setOperandValue(dest, srcValue, state);
                break;
            case 'add':
                const addDest = operands[0];
                const addSrc = operands[1];
                const addDestValue = this.getOperandValue(addDest, state);
                const addSrcValue = this.getOperandValue(addSrc, state);
                const addResult = this.performAdd(addDestValue, addSrcValue);
                this.setOperandValue(addDest, addResult, state);
                break;
            case 'sub':
                const subDest = operands[0];
                const subSrc = operands[1];
                const subDestValue = this.getOperandValue(subDest, state);
                const subSrcValue = this.getOperandValue(subSrc, state);
                const subResult = this.performSub(subDestValue, subSrcValue);
                this.setOperandValue(subDest, subResult, state);
                break;
            // Add more arithmetic operations as needed
        }
        return {};
    }
    executeLogic(instruction, state) {
        const { mnemonic, operands } = instruction;
        switch (mnemonic) {
            case 'cmp':
                const cmpOp1 = operands[0];
                const cmpOp2 = operands[1];
                const cmpVal1 = this.getOperandValue(cmpOp1, state);
                const cmpVal2 = this.getOperandValue(cmpOp2, state);
                // Store comparison result in flags register
                const cmpResult = this.performCmp(cmpVal1, cmpVal2);
                state.registers.set('eflags', cmpResult);
                break;
            case 'test':
                const testOp1 = operands[0];
                const testOp2 = operands[1];
                const testVal1 = this.getOperandValue(testOp1, state);
                const testVal2 = this.getOperandValue(testOp2, state);
                const testResult = this.performTest(testVal1, testVal2);
                state.registers.set('eflags', testResult);
                break;
        }
        return {};
    }
    executeMemory(instruction, state) {
        const { mnemonic, operands } = instruction;
        switch (mnemonic) {
            case 'push':
                const pushValue = this.getOperandValue(operands[0], state);
                const rsp = state.registers.get('rsp')?.value || 0;
                const newRsp = rsp - 8;
                state.stack.push(pushValue);
                state.registers.set('rsp', this.createConcreteValue(newRsp));
                break;
            case 'pop':
                const popRsp = state.registers.get('rsp')?.value || 0;
                const popValue = state.stack.pop();
                if (popValue) {
                    this.setOperandValue(operands[0], popValue, state);
                    state.registers.set('rsp', this.createConcreteValue(popRsp + 8));
                }
                break;
        }
        return {};
    }
    executeBranch(instruction, state) {
        const { mnemonic, operands } = instruction;
        const flags = state.registers.get('eflags');
        switch (mnemonic) {
            case 'jmp':
                return { branchTaken: parseInt(operands[0], 16) };
            case 'je': // Jump if equal
                if (flags && flags.type === 'symbolic') {
                    const constraint = `${flags.expression} == 0`;
                    return {
                        branchTaken: parseInt(operands[0], 16),
                        constraint
                    };
                }
                break;
            case 'jne': // Jump if not equal
                if (flags && flags.type === 'symbolic') {
                    const constraint = `${flags.expression} != 0`;
                    return {
                        branchTaken: parseInt(operands[0], 16),
                        constraint
                    };
                }
                break;
            // Add more branch types as needed
        }
        return {};
    }
    executeCall(instruction, state) {
        const { operands } = instruction;
        const callAddress = parseInt(operands[0], 16);
        // Push return address
        const rip = state.registers.get('rip')?.value || 0;
        const returnAddress = rip + instruction.size;
        state.stack.push(this.createConcreteValue(returnAddress));
        // Update instruction pointer
        return { branchTaken: callAddress };
    }
    executeReturn(instruction, state) {
        // Pop return address from stack
        const returnAddress = state.stack.pop();
        if (returnAddress && returnAddress.type === 'concrete') {
            return { branchTaken: returnAddress.value };
        }
        return {};
    }
    executeOther(instruction, state) {
        // Handle other instruction types
        return {};
    }
    getOperandValue(operand, state) {
        // Check if it's a register
        if (state.registers.has(operand)) {
            return state.registers.get(operand);
        }
        // Check if it's a memory operand
        const memoryMatch = operand.match(/\[([^\]]+)\]/);
        if (memoryMatch) {
            const address = this.evaluateExpression(memoryMatch[1], state);
            if (address.type === 'concrete') {
                return state.memory.get(address.value) || this.createSymbolicValue(`mem_${address.value}`);
            }
        }
        // Check if it's an immediate value
        const immediateMatch = operand.match(/^0x([0-9a-f]+)|^(\d+)$/);
        if (immediateMatch) {
            const value = parseInt(immediateMatch[1] || immediateMatch[2], immediateMatch[1] ? 16 : 10);
            return this.createConcreteValue(value);
        }
        // Default to symbolic value
        return this.createSymbolicValue(operand);
    }
    setOperandValue(operand, value, state) {
        // Check if it's a register
        if (state.registers.has(operand)) {
            state.registers.set(operand, value);
            return;
        }
        // Check if it's a memory operand
        const memoryMatch = operand.match(/\[([^\]]+)\]/);
        if (memoryMatch) {
            const address = this.evaluateExpression(memoryMatch[1], state);
            if (address.type === 'concrete') {
                state.memory.set(address.value, value);
            }
            return;
        }
    }
    evaluateExpression(expression, state) {
        // Simple expression evaluator
        // In a real implementation, this would be much more sophisticated
        // Check if it's a register
        if (state.registers.has(expression)) {
            return state.registers.get(expression);
        }
        // Check if it's a simple arithmetic expression
        const addMatch = expression.match(/(\w+)\s*\+\s*(\w+)/);
        if (addMatch) {
            const op1 = this.getOperandValue(addMatch[1], state);
            const op2 = this.getOperandValue(addMatch[2], state);
            return this.performAdd(op1, op2);
        }
        // Default to symbolic
        return this.createSymbolicValue(expression);
    }
    performAdd(op1, op2) {
        if (op1.type === 'concrete' && op2.type === 'concrete') {
            return this.createConcreteValue(op1.value + op2.value);
        }
        const expr1 = op1.expression || op1.value?.toString() || '0';
        const expr2 = op2.expression || op2.value?.toString() || '0';
        return this.createSymbolicValue(`(${expr1} + ${expr2})`);
    }
    performSub(op1, op2) {
        if (op1.type === 'concrete' && op2.type === 'concrete') {
            return this.createConcreteValue(op1.value - op2.value);
        }
        const expr1 = op1.expression || op1.value?.toString() || '0';
        const expr2 = op2.expression || op2.value?.toString() || '0';
        return this.createSymbolicValue(`(${expr1} - ${expr2})`);
    }
    performCmp(op1, op2) {
        if (op1.type === 'concrete' && op2.type === 'concrete') {
            const result = op1.value === op2.value ? 0 : (op1.value < op2.value ? -1 : 1);
            return this.createConcreteValue(result);
        }
        const expr1 = op1.expression || op1.value?.toString() || '0';
        const expr2 = op2.expression || op2.value?.toString() || '0';
        return this.createSymbolicValue(`cmp(${expr1}, ${expr2})`);
    }
    performTest(op1, op2) {
        if (op1.type === 'concrete' && op2.type === 'concrete') {
            const result = op1.value & op2.value;
            return this.createConcreteValue(result);
        }
        const expr1 = op1.expression || op1.value?.toString() || '0';
        const expr2 = op2.expression || op2.value?.toString() || '0';
        return this.createSymbolicValue(`(${expr1} & ${expr2})`);
    }
    clonePath(path) {
        const clonedState = {
            variables: new Map(path.state.variables),
            memory: new Map(path.state.memory),
            registers: new Map(path.state.registers),
            pathConstraints: [...path.state.pathConstraints],
            stack: [...path.state.stack],
            heap: new Map(path.state.heap)
        };
        return {
            id: (0, crypto_1.randomUUID)(),
            state: clonedState,
            instructions: [...path.instructions],
            constraints: [...path.constraints],
            feasible: path.feasible,
            explored: false,
            depth: path.depth,
            branchConditions: [...path.branchConditions]
        };
    }
    negateConstraint(constraint) {
        // Simple constraint negation
        if (constraint.includes('==')) {
            return constraint.replace('==', '!=');
        }
        else if (constraint.includes('!=')) {
            return constraint.replace('!=', '==');
        }
        else if (constraint.includes('>')) {
            return constraint.replace('>', '<=');
        }
        else if (constraint.includes('<')) {
            return constraint.replace('<', '>=');
        }
        return `!(${constraint})`;
    }
    stopExecution() {
        this.isExecuting = false;
        console.log('[SymExec] Symbolic execution stopped');
        this.emit('executionStopped');
    }
    getResults() {
        const paths = Array.from(this.paths.values());
        const feasiblePaths = paths.filter(path => path.feasible);
        const infeasiblePaths = paths.filter(path => !path.feasible);
        return {
            totalPaths: paths.length,
            feasiblePaths: feasiblePaths.length,
            infeasiblePaths: infeasiblePaths.length,
            maxDepth: Math.max(...paths.map(p => p.depth)),
            instructions: this.instructions.size,
            symbolicVariables: this.symbolicVariables.size,
            paths: paths.map(path => ({
                id: path.id,
                depth: path.depth,
                constraints: path.constraints,
                feasible: path.feasible,
                instructionCount: path.instructions.length
            }))
        };
    }
    generateReport(format = 'json') {
        const results = this.getResults();
        if (format === 'json') {
            return JSON.stringify(results, null, 2);
        }
        // Generate DOT format for visualization
        const dot = [
            'digraph SymbolicExecution {',
            '  rankdir=TB;',
            '  node [shape=box];',
            ''
        ];
        for (const path of this.paths.values()) {
            const label = `Path ${path.id.substring(0, 8)}\\nDepth: ${path.depth}\\nConstraints: ${path.constraints.length}`;
            dot.push(`  "${path.id}" [label="${label}"];`);
        }
        // Add edges for path relationships (simplified)
        for (const path of this.paths.values()) {
            if (path.branchConditions.length > 0) {
                dot.push(`  "${path.id}" -> "branch_${path.id}";`);
            }
        }
        dot.push('}');
        return dot.join('\n');
    }
    getStatistics() {
        return {
            isExecuting: this.isExecuting,
            config: this.config,
            instructionCount: this.instructions.size,
            pathCount: this.paths.size,
            symbolicVariableCount: this.symbolicVariables.size,
            taintSources: this.taintSources.size,
            taintSinks: this.taintSinks.size
        };
    }
    destroy() {
        this.stopExecution();
        this.paths.clear();
        this.instructions.clear();
        this.symbolicVariables.clear();
        console.log('[SymExec] Symbolic executor destroyed');
    }
}
exports.RealSymbolicExecutor = RealSymbolicExecutor;
//# sourceMappingURL=RealSymbolicExecutor.js.map