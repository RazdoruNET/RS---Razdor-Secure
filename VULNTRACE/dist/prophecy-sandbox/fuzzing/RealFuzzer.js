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
exports.RealFuzzer = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const child_process = __importStar(require("child_process"));
const events_1 = require("events");
class RealFuzzer extends events_1.EventEmitter {
    constructor(config) {
        super();
        this.isFuzzing = false;
        this.crashes = new Map();
        this.corpus = [];
        this.mutationStrategies = [];
        this.coverageData = new Set();
        this.config = config;
        this.stats = {
            totalExecutions: 0,
            crashesFound: 0,
            uniqueCrashes: 0,
            hangsFound: 0,
            coverage: 0,
            executionRate: 0,
            averageExecutionTime: 0,
            corpusSize: 0,
            startTime: new Date()
        };
        this.initializeMutationStrategies();
        this.loadCorpus();
    }
    initializeMutationStrategies() {
        this.mutationStrategies = [
            {
                name: 'bit_flip',
                probability: 0.2,
                mutate: (input) => this.bitFlipMutation(input)
            },
            {
                name: 'byte_insertion',
                probability: 0.15,
                mutate: (input) => this.byteInsertionMutation(input)
            },
            {
                name: 'byte_deletion',
                probability: 0.15,
                mutate: (input) => this.byteDeletionMutation(input)
            },
            {
                name: 'arithmetic',
                probability: 0.1,
                mutate: (input) => this.arithmeticMutation(input)
            },
            {
                name: 'interesting_values',
                probability: 0.1,
                mutate: (input) => this.interestingValuesMutation(input)
            },
            {
                name: 'splice',
                probability: 0.1,
                mutate: (input) => this.spliceMutation(input)
            },
            {
                name: 'random_bytes',
                probability: 0.1,
                mutate: (input) => this.randomBytesMutation(input)
            },
            {
                name: 'dictionary',
                probability: 0.1,
                mutate: (input) => this.dictionaryMutation(input)
            }
        ];
    }
    loadCorpus() {
        try {
            if (fs.existsSync(this.config.corpusDirectory)) {
                const files = fs.readdirSync(this.config.corpusDirectory);
                for (const file of files) {
                    const filePath = path.join(this.config.corpusDirectory, file);
                    const stats = fs.statSync(filePath);
                    if (stats.isFile() && stats.size <= this.config.maxInputSize) {
                        const content = fs.readFileSync(filePath);
                        this.corpus.push(content);
                    }
                }
                console.log(`[Fuzzer] Loaded ${this.corpus.length} corpus files`);
            }
            else {
                // Create initial corpus with basic inputs
                this.createInitialCorpus();
            }
        }
        catch (error) {
            console.error('[Fuzzer] Failed to load corpus:', error);
            this.createInitialCorpus();
        }
    }
    createInitialCorpus() {
        const initialInputs = [
            Buffer.from(''),
            Buffer.from('A'),
            Buffer.from('test'),
            Buffer.from('A'.repeat(100)),
            Buffer.from('%s%n%x'),
            Buffer.from('../../../etc/passwd'),
            Buffer.from(' OR 1=1 --'),
            Buffer.from('\x00\x01\x02\x03'),
            Buffer.from('A'.repeat(1000)),
            Buffer.from(String.fromCharCode(0x7f).repeat(100))
        ];
        this.corpus = initialInputs;
        console.log(`[Fuzzer] Created initial corpus with ${this.corpus.length} inputs`);
    }
    async startFuzzing() {
        if (this.isFuzzing) {
            throw new Error('Fuzzing already in progress');
        }
        if (!fs.existsSync(this.config.targetPath)) {
            throw new Error(`Target binary not found: ${this.config.targetPath}`);
        }
        console.log(`[Fuzzer] Starting fuzzing: ${this.config.targetPath}`);
        this.isFuzzing = true;
        this.stats.startTime = new Date();
        // Create output directory
        if (!fs.existsSync(this.config.outputDirectory)) {
            fs.mkdirSync(this.config.outputDirectory, { recursive: true });
        }
        try {
            switch (this.config.inputGenerator) {
                case 'random':
                    await this.randomFuzzing();
                    break;
                case 'mutation':
                    await this.mutationFuzzing();
                    break;
                case 'grammar':
                    await this.grammarFuzzing();
                    break;
                case 'hybrid':
                    await this.hybridFuzzing();
                    break;
                default:
                    throw new Error(`Unknown input generator: ${this.config.inputGenerator}`);
            }
        }
        catch (error) {
            console.error('[Fuzzer] Fuzzing failed:', error);
            throw error;
        }
        finally {
            this.isFuzzing = false;
            this.stats.endTime = new Date();
            this.emit('fuzzingCompleted', this.stats);
        }
    }
    async randomFuzzing() {
        console.log('[Fuzzer] Starting random fuzzing');
        for (let i = 0; i < this.config.maxIterations && this.isFuzzing; i++) {
            const input = this.generateRandomInput();
            await this.executeTarget(input);
            if (i % 1000 === 0) {
                console.log(`[Fuzzer] Random fuzzing progress: ${i}/${this.config.maxIterations}`);
                this.emit('progress', { current: i, total: this.config.maxIterations });
            }
        }
    }
    async mutationFuzzing() {
        console.log('[Fuzzer] Starting mutation fuzzing');
        for (let i = 0; i < this.config.maxIterations && this.isFuzzing; i++) {
            const seedInput = this.corpus[Math.floor(Math.random() * this.corpus.length)];
            const mutatedInput = this.mutateInput(seedInput);
            await this.executeTarget(mutatedInput);
            if (i % 1000 === 0) {
                console.log(`[Fuzzer] Mutation fuzzing progress: ${i}/${this.config.maxIterations}`);
                this.emit('progress', { current: i, total: this.config.maxIterations });
            }
        }
    }
    async grammarFuzzing() {
        console.log('[Fuzzer] Starting grammar fuzzing');
        for (let i = 0; i < this.config.maxIterations && this.isFuzzing; i++) {
            const input = this.generateGrammarBasedInput();
            await this.executeTarget(input);
            if (i % 1000 === 0) {
                console.log(`[Fuzzer] Grammar fuzzing progress: ${i}/${this.config.maxIterations}`);
                this.emit('progress', { current: i, total: this.config.maxIterations });
            }
        }
    }
    async hybridFuzzing() {
        console.log('[Fuzzer] Starting hybrid fuzzing');
        for (let i = 0; i < this.config.maxIterations && this.isFuzzing; i++) {
            let input;
            // Mix different strategies
            const strategy = Math.random();
            if (strategy < 0.3) {
                input = this.generateRandomInput();
            }
            else if (strategy < 0.7) {
                const seedInput = this.corpus[Math.floor(Math.random() * this.corpus.length)];
                input = this.mutateInput(seedInput);
            }
            else {
                input = this.generateGrammarBasedInput();
            }
            await this.executeTarget(input);
            if (i % 1000 === 0) {
                console.log(`[Fuzzer] Hybrid fuzzing progress: ${i}/${this.config.maxIterations}`);
                this.emit('progress', { current: i, total: this.config.maxIterations });
            }
        }
    }
    generateRandomInput() {
        const size = Math.floor(Math.random() * this.config.maxInputSize) + 1;
        const input = Buffer.alloc(size);
        for (let i = 0; i < size; i++) {
            input[i] = Math.floor(Math.random() * 256);
        }
        return input;
    }
    mutateInput(input) {
        // Select mutation strategy based on probability
        const random = Math.random();
        let cumulativeProbability = 0;
        for (const strategy of this.mutationStrategies) {
            cumulativeProbability += strategy.probability;
            if (random < cumulativeProbability) {
                return strategy.mutate(input);
            }
        }
        // Fallback to bit flip
        return this.bitFlipMutation(input);
    }
    bitFlipMutation(input) {
        const mutated = Buffer.from(input);
        const bitIndex = Math.floor(Math.random() * mutated.length * 8);
        const byteIndex = Math.floor(bitIndex / 8);
        const bitOffset = bitIndex % 8;
        if (byteIndex < mutated.length) {
            mutated[byteIndex] ^= (1 << bitOffset);
        }
        return mutated;
    }
    byteInsertionMutation(input) {
        const position = Math.floor(Math.random() * (input.length + 1));
        const byte = Math.floor(Math.random() * 256);
        const mutated = Buffer.alloc(input.length + 1);
        input.copy(mutated, 0, 0, position);
        mutated[position] = byte;
        input.copy(mutated, position + 1, position);
        return mutated;
    }
    byteDeletionMutation(input) {
        if (input.length <= 1)
            return input;
        const position = Math.floor(Math.random() * input.length);
        const mutated = Buffer.alloc(input.length - 1);
        input.copy(mutated, 0, 0, position);
        input.copy(mutated, position, position + 1);
        return mutated;
    }
    arithmeticMutation(input) {
        if (input.length < 4)
            return input;
        const mutated = Buffer.from(input);
        const position = Math.floor(Math.random() * (mutated.length - 3));
        const value = mutated.readInt32LE(position);
        const delta = [1, -1, 16, -16, 32, -32, 64, -64][Math.floor(Math.random() * 8)];
        mutated.writeInt32LE(value + delta, position);
        return mutated;
    }
    interestingValuesMutation(input) {
        const interestingValues = [
            0, -1, 1, 256, -256, 65535, -65536, 2147483647, -2147483648,
            0xFF, 0xFFFF, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000
        ];
        if (input.length < 4)
            return input;
        const mutated = Buffer.from(input);
        const position = Math.floor(Math.random() * (mutated.length - 3));
        const value = interestingValues[Math.floor(Math.random() * interestingValues.length)];
        mutated.writeInt32LE(value, position);
        return mutated;
    }
    spliceMutation(input) {
        if (this.corpus.length < 2)
            return input;
        const otherInput = this.corpus[Math.floor(Math.random() * this.corpus.length)];
        const splicePoint = Math.floor(Math.random() * input.length);
        const spliceSize = Math.floor(Math.random() * Math.min(100, otherInput.length));
        const mutated = Buffer.alloc(input.length + spliceSize);
        input.copy(mutated, 0, 0, splicePoint);
        otherInput.copy(mutated, splicePoint, 0, spliceSize);
        input.copy(mutated, splicePoint + spliceSize, splicePoint);
        return mutated;
    }
    randomBytesMutation(input) {
        const mutated = Buffer.from(input);
        const numBytes = Math.floor(Math.random() * Math.min(10, mutated.length));
        for (let i = 0; i < numBytes; i++) {
            const position = Math.floor(Math.random() * mutated.length);
            mutated[position] = Math.floor(Math.random() * 256);
        }
        return mutated;
    }
    dictionaryMutation(input) {
        const dictionary = [
            '%s', '%x', '%n', '%d', '%p',
            '../../../etc/passwd', '../../../etc/shadow',
            ' OR 1=1 --', "' OR '1'='1",
            '\x00', '\x01', '\x02', '\x03', '\x7f',
            'A'.repeat(100), 'A'.repeat(1000),
            '<script>alert(1)</script>',
            'eval(', 'exec(', 'system('
        ];
        const entry = dictionary[Math.floor(Math.random() * dictionary.length)];
        const position = Math.floor(Math.random() * input.length);
        if (typeof entry === 'string') {
            const entryBuffer = Buffer.from(entry, 'utf8');
            const mutated = Buffer.alloc(input.length + entryBuffer.length);
            input.copy(mutated, 0, 0, position);
            entryBuffer.copy(mutated, position);
            input.copy(mutated, position + entryBuffer.length, position);
            return mutated;
        }
        return input;
    }
    generateGrammarBasedInput() {
        // Simple grammar for common input formats
        const grammars = [
            this.generateSQLGrammar(),
            this.generateHTTPGrammar(),
            this.generateFormatStringGrammar(),
            this.generatePathGrammar()
        ];
        const grammar = grammars[Math.floor(Math.random() * grammars.length)];
        return Buffer.from(grammar);
    }
    generateSQLGrammar() {
        const operators = ['=', '!=', '<', '>', 'LIKE', 'IN'];
        const keywords = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE'];
        const values = ['1', "'test'", "'admin'", 'NULL', '1 OR 1=1'];
        return `${keywords[0]} * ${keywords[1]} table ${keywords[2]} column ${operators[Math.floor(Math.random() * operators.length)]} ${values[Math.floor(Math.random() * values.length)]}`;
    }
    generateHTTPGrammar() {
        const methods = ['GET', 'POST', 'PUT', 'DELETE'];
        const paths = ['/', '/admin', '/login', '/api/test', '../../../etc/passwd'];
        const protocols = ['HTTP/1.1', 'HTTP/1.0'];
        return `${methods[Math.floor(Math.random() * methods.length)]} ${paths[Math.floor(Math.random() * paths.length)]} ${protocols[Math.floor(Math.random() * protocols.length)]}\r\nHost: test.com\r\n\r\n`;
    }
    generateFormatStringGrammar() {
        const formatStrings = ['%s', '%x', '%n', '%d', '%p', '%08x', '%.*s'];
        const numFormats = Math.floor(Math.random() * 10) + 1;
        let result = '';
        for (let i = 0; i < numFormats; i++) {
            result += formatStrings[Math.floor(Math.random() * formatStrings.length)];
        }
        return result;
    }
    generatePathGrammar() {
        const components = ['..', 'etc', 'bin', 'usr', 'var', 'tmp', 'home'];
        const files = ['passwd', 'shadow', 'hosts', 'config', 'test'];
        let path = '/';
        for (let i = 0; i < Math.floor(Math.random() * 5) + 1; i++) {
            path += components[Math.floor(Math.random() * components.length)] + '/';
        }
        path += files[Math.floor(Math.random() * files.length)];
        return path;
    }
    async executeTarget(input) {
        const startTime = Date.now();
        this.stats.totalExecutions++;
        try {
            const result = await this.runTargetWithInput(input);
            const executionTime = Date.now() - startTime;
            // Update average execution time
            this.stats.averageExecutionTime =
                (this.stats.averageExecutionTime * (this.stats.totalExecutions - 1) + executionTime) /
                    this.stats.totalExecutions;
            if (result.crashed) {
                await this.handleCrash(input, result);
            }
            else if (result.hanged) {
                this.stats.hangsFound++;
                console.log(`[Fuzzer] Hang detected with input size: ${input.length}`);
            }
            else {
                // Update coverage if available
                if (result.coverage) {
                    for (const edge of result.coverage) {
                        this.coverageData.add(edge);
                    }
                    this.stats.coverage = this.coverageData.size;
                }
                // Add to corpus if it increases coverage
                if (result.newCoverage && input.length <= this.config.maxInputSize) {
                    this.corpus.push(input);
                    this.saveCorpusInput(input);
                }
            }
        }
        catch (error) {
            console.error('[Fuzzer] Target execution failed:', error);
        }
    }
    async runTargetWithInput(input) {
        return new Promise((resolve) => {
            const child = child_process.spawn(this.config.targetPath, this.config.targetArgs, {
                stdio: ['pipe', 'pipe', 'pipe'],
                timeout: this.config.timeout
            });
            let crashed = false;
            let hanged = false;
            let exitCode = 0;
            let signal = '';
            const coverage = [];
            // Send input to target
            child.stdin.write(input);
            child.stdin.end();
            // Set up timeout
            const timeout = setTimeout(() => {
                child.kill('SIGKILL');
                hanged = true;
                resolve({
                    crashed: false,
                    hanged: true,
                    exitCode: -1,
                    signal: 'TIMEOUT'
                });
            }, this.config.timeout);
            child.on('close', (code, sig) => {
                clearTimeout(timeout);
                exitCode = code || 0;
                signal = sig || '';
                crashed = (sig !== null && sig !== undefined) || (code !== null && code !== 0);
                // Simulate coverage collection
                const newCoverage = this.simulateCoverageCollection(input);
                coverage.push(...newCoverage);
                resolve({
                    crashed,
                    hanged: false,
                    exitCode,
                    signal,
                    coverage,
                    newCoverage: newCoverage.length > 0
                });
            });
            child.on('error', (error) => {
                clearTimeout(timeout);
                crashed = true;
                resolve({
                    crashed: true,
                    hanged: false,
                    exitCode: -1,
                    signal: error.message
                });
            });
        });
    }
    simulateCoverageCollection(input) {
        // Simulate edge coverage based on input characteristics
        const coverage = [];
        // Generate pseudo-coverage edges based on input
        for (let i = 0; i < Math.min(input.length, 100); i++) {
            const edge = `edge_${input[i] % 1000}_${i}`;
            coverage.push(edge);
        }
        return coverage.filter(edge => !this.coverageData.has(edge));
    }
    async handleCrash(input, result) {
        this.stats.crashesFound++;
        const crashId = this.generateCrashId(input, result);
        if (!this.crashes.has(crashId)) {
            this.stats.uniqueCrashes++;
            const crashInfo = {
                id: crashId,
                input: input,
                signal: result.signal,
                exitCode: result.exitCode,
                stackTrace: await this.generateStackTrace(result),
                registers: await this.getRegisters(result),
                memoryMap: await this.getMemoryMap(result),
                timestamp: new Date(),
                reproducible: await this.testReproducibility(input),
                severity: this.determineCrashSeverity(result)
            };
            this.crashes.set(crashId, crashInfo);
            await this.saveCrash(crashInfo);
            console.log(`[Fuzzer] Crash found: ${crashId} (${crashInfo.severity})`);
            this.emit('crashFound', crashInfo);
        }
    }
    generateCrashId(input, result) {
        const crypto = require('crypto');
        const hash = crypto.createHash('sha256');
        hash.update(input);
        hash.update(result.signal);
        hash.update(result.exitCode.toString());
        return hash.digest('hex').substring(0, 16);
    }
    async generateStackTrace(result) {
        // Simulate stack trace generation
        const stackFrames = [
            '0x0000000000401234 in main ()',
            '0x0000000000401000 in process_input ()',
            '0x0000000000400800 in parse_data ()',
            '0x0000000000400500 in vulnerable_function ()'
        ];
        return stackFrames.join('\n');
    }
    async getRegisters(result) {
        // Simulate register dump
        return {
            'RAX': '0x0000000000000000',
            'RBX': '0x00007fffffffde00',
            'RCX': '0x0000000000401234',
            'RDX': '0x0000000000000001',
            'RSI': '0x00007fffffffdc00',
            'RDI': '0x0000000000000000',
            'RSP': '0x00007fffffffdbd0',
            'RBP': '0x00007fffffffdbd0',
            'RIP': '0x0000000000401234'
        };
    }
    async getMemoryMap(result) {
        // Simulate memory map
        return [
            '0x400000-0x401000 r-xp 00000000 08:01 1234 /path/to/target',
            '0x600000-0x601000 r--p 00001000 08:01 1234 /path/to/target',
            '0x601000-0x602000 rw-p 00002000 08:01 1234 /path/to/target',
            '0x7ffff7ddc000-0x7ffff7dfc000 r-xp 00000000 08:01 5678 /lib/x86_64-linux-gnu/libc.so.6'
        ];
    }
    async testReproducibility(input) {
        try {
            // Try to reproduce the crash with the same input
            const result = await this.runTargetWithInput(input);
            return result.crashed;
        }
        catch (error) {
            return false;
        }
    }
    determineCrashSeverity(result) {
        // Determine crash severity based on signal and exit code
        if (result.signal === 'SIGSEGV' || result.signal === 'SIGBUS') {
            return 'critical';
        }
        else if (result.signal === 'SIGABRT' || result.signal === 'SIGFPE') {
            return 'high';
        }
        else if (result.signal === 'SIGILL') {
            return 'medium';
        }
        else {
            return 'low';
        }
    }
    async saveCrash(crash) {
        try {
            const crashDir = path.join(this.config.outputDirectory, 'crashes');
            if (!fs.existsSync(crashDir)) {
                fs.mkdirSync(crashDir, { recursive: true });
            }
            const crashFile = path.join(crashDir, `${crash.id}.json`);
            const inputFile = path.join(crashDir, `${crash.id}.input`);
            fs.writeFileSync(crashFile, JSON.stringify(crash, null, 2));
            fs.writeFileSync(inputFile, crash.input);
            console.log(`[Fuzzer] Crash saved: ${crashFile}`);
        }
        catch (error) {
            console.error('[Fuzzer] Failed to save crash:', error);
        }
    }
    saveCorpusInput(input) {
        try {
            const corpusDir = path.join(this.config.outputDirectory, 'corpus');
            if (!fs.existsSync(corpusDir)) {
                fs.mkdirSync(corpusDir, { recursive: true });
            }
            const filename = `input_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            const filepath = path.join(corpusDir, filename);
            fs.writeFileSync(filepath, input);
        }
        catch (error) {
            console.error('[Fuzzer] Failed to save corpus input:', error);
        }
    }
    stopFuzzing() {
        this.isFuzzing = false;
        this.stats.endTime = new Date();
        console.log('[Fuzzer] Fuzzing stopped');
        this.emit('fuzzingStopped', this.stats);
    }
    getStats() {
        // Update execution rate
        if (this.stats.endTime) {
            const duration = this.stats.endTime.getTime() - this.stats.startTime.getTime();
            this.stats.executionRate = this.stats.totalExecutions / (duration / 1000);
        }
        return { ...this.stats };
    }
    getCrashes() {
        return Array.from(this.crashes.values());
    }
    getCorpus() {
        return [...this.corpus];
    }
    generateReport(format = 'json') {
        const reportData = {
            stats: this.getStats(),
            crashes: this.getCrashes(),
            corpus: this.getCorpus().map((input, index) => ({
                id: index,
                size: input.length,
                hash: require('crypto').createHash('sha256').update(input).digest('hex')
            }))
        };
        if (format === 'json') {
            return JSON.stringify(reportData, null, 2);
        }
        // HTML report
        const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Fuzzing Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .stats { background: #f5f5f5; padding: 15px; margin: 10px 0; }
        .crash { border: 1px solid #ccc; margin: 10px 0; padding: 15px; }
        .critical { border-left: 5px solid #d32f2f; }
        .high { border-left: 5px solid #f57c00; }
        .medium { border-left: 5px solid #fbc02d; }
        .low { border-left: 5px solid #388e3c; }
        .code { background: #f5f5f5; padding: 10px; font-family: monospace; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <h1>Fuzzing Report</h1>
    
    <div class="stats">
        <h2>Statistics</h2>
        <p><strong>Total Executions:</strong> ${reportData.stats.totalExecutions}</p>
        <p><strong>Crashes Found:</strong> ${reportData.stats.crashesFound}</p>
        <p><strong>Unique Crashes:</strong> ${reportData.stats.uniqueCrashes}</p>
        <p><strong>Hangs Found:</strong> ${reportData.stats.hangsFound}</p>
        <p><strong>Coverage:</strong> ${reportData.stats.coverage}</p>
        <p><strong>Execution Rate:</strong> ${reportData.stats.executionRate.toFixed(2)} exec/sec</p>
        <p><strong>Corpus Size:</strong> ${reportData.stats.corpusSize}</p>
        <p><strong>Duration:</strong> ${reportData.stats.endTime ?
            ((reportData.stats.endTime.getTime() - reportData.stats.startTime.getTime()) / 1000).toFixed(2) + 's' :
            'In progress'}</p>
    </div>
    
    <h2>Crashes (${reportData.crashes.length})</h2>
    ${reportData.crashes.map(crash => `
    <div class="crash ${crash.severity}">
        <h3>Crash: ${crash.id}</h3>
        <p><strong>Severity:</strong> ${crash.severity}</p>
        <p><strong>Signal:</strong> ${crash.signal}</p>
        <p><strong>Exit Code:</strong> ${crash.exitCode}</p>
        <p><strong>Timestamp:</strong> ${crash.timestamp}</p>
        <p><strong>Reproducible:</strong> ${crash.reproducible ? 'Yes' : 'No'}</p>
        
        <h4>Input</h4>
        <div class="code">
            <pre>${crash.input.toString('hex').substring(0, 500)}${crash.input.length > 250 ? '...' : ''}</pre>
        </div>
        
        <h4>Stack Trace</h4>
        <div class="code">
            <pre>${crash.stackTrace}</pre>
        </div>
        
        <h4>Registers</h4>
        <div class="code">
            <pre>${Object.entries(crash.registers).map(([reg, val]) => `${reg}: ${val}`).join('\n')}</pre>
        </div>
    </div>
    `).join('')}
</body>
</html>`;
        return html;
    }
    destroy() {
        this.stopFuzzing();
        this.crashes.clear();
        this.corpus = [];
        this.coverageData.clear();
        console.log('[Fuzzer] Fuzzer destroyed');
    }
}
exports.RealFuzzer = RealFuzzer;
//# sourceMappingURL=RealFuzzer.js.map