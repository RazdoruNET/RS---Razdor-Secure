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
exports.RealGeneticAlgorithm = void 0;
const crypto = __importStar(require("crypto"));
class RealGeneticAlgorithm {
    constructor(config) {
        this.population = [];
        this.generation = 0;
        this.fitnessHistory = [];
        this.config = config;
    }
    async evolvePopulation(initialTemplate, targetCharacteristics) {
        console.log(`Starting genetic evolution with population size: ${this.config.populationSize}`);
        // Initialize population
        await this.initializePopulation(initialTemplate);
        // Evolution loop
        while (this.generation < this.config.maxGenerations && !this.shouldTerminate()) {
            console.log(`Generation ${this.generation + 1}/${this.config.maxGenerations}`);
            // Evaluate fitness
            await this.evaluatePopulation(targetCharacteristics);
            // Selection
            const selected = this.selection();
            // Crossover and mutation
            await this.createNextGeneration(selected);
            this.generation++;
        }
        // Return best individual
        const best = this.getBestIndividual();
        console.log(`Evolution completed. Best fitness: ${best.fitness}`);
        return best.template;
    }
    async mutateTemplate(template, mutationRate) {
        const individual = {
            id: crypto.randomUUID(),
            template,
            fitness: 0,
            generation: 0,
            parentIds: [],
            mutations: []
        };
        const mutated = await this.applyMutations(individual, mutationRate);
        return mutated.template;
    }
    async initializePopulation(initialTemplate) {
        this.population = [];
        for (let i = 0; i < this.config.populationSize; i++) {
            const individual = {
                id: crypto.randomUUID(),
                template: await this.createVariant(initialTemplate, i),
                fitness: 0,
                generation: 0,
                parentIds: [],
                mutations: []
            };
            this.population.push(individual);
        }
    }
    async createVariant(template, index) {
        const variant = JSON.parse(JSON.stringify(template));
        // Apply different initial mutations based on index
        switch (index % 4) {
            case 0:
                // Obfuscation variant
                variant.template = this.applyObfuscation(variant.template);
                break;
            case 1:
                // Encryption variant
                variant.template = this.applyEncryption(variant.template);
                break;
            case 2:
                // Structure variant
                variant.template = this.applyStructureMutation(variant.template);
                break;
            case 3:
                // Evasion variant
                variant.evasionTechniques = this.addRandomEvasion(variant.evasionTechniques);
                break;
        }
        return variant;
    }
    async evaluatePopulation(targetCharacteristics) {
        for (const individual of this.population) {
            individual.fitness = await this.calculateFitness(individual.template, targetCharacteristics);
        }
        // Sort by fitness
        this.population.sort((a, b) => b.fitness - a.fitness);
        // Track fitness history
        const avgFitness = this.population.reduce((sum, ind) => sum + ind.fitness, 0) / this.population.length;
        this.fitnessHistory.push(avgFitness);
    }
    async calculateFitness(template, targetCharacteristics) {
        const fitness = {
            stealth: this.calculateStealth(template),
            complexity: this.calculateComplexity(template),
            evasion: this.calculateEvasionScore(template),
            novelty: this.calculateNovelty(template)
        };
        // Weighted fitness calculation
        const weights = {
            stealth: 0.3,
            complexity: 0.2,
            evasion: 0.3,
            novelty: 0.2
        };
        fitness.score =
            fitness.stealth * weights.stealth +
                fitness.complexity * weights.complexity +
                fitness.evasion * weights.evasion +
                fitness.novelty * weights.novelty;
        return fitness.score;
    }
    calculateStealth(template) {
        let score = 0;
        // Check for anti-debug techniques
        const antiDebugPatterns = [/sys\.gettrace/, /ptrace/, /isDebuggerPresent/];
        for (const pattern of antiDebugPatterns) {
            if (pattern.test(template.template)) {
                score += 0.2;
            }
        }
        // Check for obfuscation
        const obfuscationIndicators = [
            template.template.includes('base64'),
            template.template.includes('eval'),
            template.template.match(/[a-zA-Z_][a-zA-Z0-9_]{20,}/) // Long variable names
        ];
        score += obfuscationIndicators.filter(Boolean).length * 0.1;
        // Check evasion techniques
        score += template.evasionTechniques.length * 0.15;
        return Math.min(score, 1.0);
    }
    calculateComplexity(template) {
        // Cyclomatic complexity approximation
        const complexityIndicators = [
            (template.template.match(/if\s*\(.*\)/g) || []).length,
            (template.template.match(/for\s*\(.*\)/g) || []).length,
            (template.template.match(/while\s*\(.*\)/g) || []).length,
            (template.template.match(/function\s+\w+/g) || []).length,
            (template.template.match(/class\s+\w+/g) || []).length
        ];
        const totalComplexity = complexityIndicators.reduce((sum, count) => sum + count, 0);
        // Normalize to 0-1 scale (higher complexity = higher score up to a point)
        return Math.min(totalComplexity / 20, 1.0);
    }
    calculateEvasionScore(template) {
        let score = 0;
        for (const technique of template.evasionTechniques) {
            switch (technique.category) {
                case 'anti-debug':
                    score += 0.3;
                    break;
                case 'polymorphism':
                    score += 0.25;
                    break;
                case 'encryption':
                    score += 0.2;
                    break;
                case 'obfuscation':
                    score += 0.15;
                    break;
                case 'anti-vm':
                    score += 0.1;
                    break;
            }
        }
        return Math.min(score, 1.0);
    }
    calculateNovelty(template) {
        // Calculate novelty based on unique patterns
        const uniquePatterns = new Set();
        // Extract function names, variable names, and string literals
        const functionNames = template.template.match(/function\s+(\w+)/g) || [];
        const variableNames = template.template.match(/(?:var|let|const)\s+(\w+)/g) || [];
        const stringLiterals = template.template.match(/['"]([^'"]+)['"]/g) || [];
        functionNames.forEach(name => uniquePatterns.add(name));
        variableNames.forEach(name => uniquePatterns.add(name));
        stringLiterals.forEach(str => uniquePatterns.add(str));
        // Higher novelty for more unique patterns (up to a point)
        return Math.min(uniquePatterns.size / 50, 1.0);
    }
    selection() {
        const eliteCount = Math.floor(this.population.length * this.config.elitismRate);
        const selected = [];
        // Elitism - keep best individuals
        for (let i = 0; i < eliteCount; i++) {
            selected.push(this.population[i]);
        }
        // Tournament selection for remaining spots
        while (selected.length < this.population.length) {
            const tournament = this.tournamentSelection(3);
            selected.push(tournament);
        }
        return selected;
    }
    tournamentSelection(tournamentSize) {
        const tournament = [];
        for (let i = 0; i < tournamentSize; i++) {
            const randomIndex = Math.floor(Math.random() * this.population.length);
            tournament.push(this.population[randomIndex]);
        }
        return tournament.reduce((best, current) => current.fitness > best.fitness ? current : best);
    }
    async createNextGeneration(selected) {
        const newPopulation = [];
        // Keep elite individuals
        const eliteCount = Math.floor(selected.length * this.config.elitismRate);
        for (let i = 0; i < eliteCount; i++) {
            newPopulation.push(selected[i]);
        }
        // Create offspring through crossover and mutation
        while (newPopulation.length < this.config.populationSize) {
            const parent1 = this.selectParent(selected);
            const parent2 = this.selectParent(selected);
            let offspring;
            if (Math.random() < this.config.crossoverRate) {
                offspring = await this.crossover(parent1, parent2);
            }
            else {
                offspring = { ...parent1, id: crypto.randomUUID() };
            }
            if (Math.random() < this.config.mutationRate) {
                offspring = await this.applyMutations(offspring, this.config.mutationRate);
            }
            offspring.generation = this.generation + 1;
            offspring.parentIds = [parent1.id, parent2.id];
            newPopulation.push(offspring);
        }
        this.population = newPopulation;
    }
    selectParent(selected) {
        // Roulette wheel selection
        const totalFitness = selected.reduce((sum, ind) => sum + ind.fitness, 0);
        let random = Math.random() * totalFitness;
        for (const individual of selected) {
            random -= individual.fitness;
            if (random <= 0) {
                return individual;
            }
        }
        return selected[selected.length - 1];
    }
    async crossover(parent1, parent2) {
        const child = {
            id: crypto.randomUUID(),
            template: JSON.parse(JSON.stringify(parent1.template)),
            fitness: 0,
            generation: this.generation + 1,
            parentIds: [parent1.id, parent2.id],
            mutations: []
        };
        // Single-point crossover on template code
        const code1 = parent1.template.template;
        const code2 = parent2.template.template;
        const crossoverPoint = Math.floor(Math.random() * Math.min(code1.length, code2.length));
        child.template.template = code1.substring(0, crossoverPoint) + code2.substring(crossoverPoint);
        // Crossover evasion techniques
        const allTechniques = [...parent1.template.evasionTechniques, ...parent2.template.evasionTechniques];
        const shuffled = allTechniques.sort(() => Math.random() - 0.5);
        child.template.evasionTechniques = shuffled.slice(0, Math.floor(shuffled.length / 2));
        return child;
    }
    async applyMutations(individual, mutationRate) {
        const mutated = { ...individual };
        const mutationCount = Math.floor(mutationRate * 10) + 1;
        for (let i = 0; i < mutationCount; i++) {
            const mutationType = this.selectMutationType();
            const mutation = await this.applyMutation(mutated.template, mutationType);
            if (mutation) {
                mutated.mutations.push(mutation);
            }
        }
        return mutated;
    }
    selectMutationType() {
        const types = ['insert', 'delete', 'replace', 'reorder', 'obfuscate', 'encrypt'];
        return types[Math.floor(Math.random() * types.length)];
    }
    async applyMutation(template, mutationType) {
        const original = template.template;
        let mutated = original;
        let position = 0;
        let description = '';
        switch (mutationType) {
            case 'obfuscate':
                mutated = this.applyObfuscation(original);
                description = 'Applied code obfuscation';
                break;
            case 'encrypt':
                mutated = this.applyEncryption(original);
                description = 'Applied string encryption';
                break;
            case 'insert':
                const insertion = this.generateInsertion();
                position = Math.floor(Math.random() * original.length);
                mutated = original.substring(0, position) + insertion + original.substring(position);
                description = `Inserted code at position ${position}`;
                break;
            case 'delete':
                if (original.length > 100) {
                    position = Math.floor(Math.random() * (original.length - 50)) + 25;
                    const deleteLength = Math.floor(Math.random() * 20) + 5;
                    mutated = original.substring(0, position) + original.substring(position + deleteLength);
                    description = `Deleted ${deleteLength} characters at position ${position}`;
                }
                break;
            case 'replace':
                position = Math.floor(Math.random() * original.length);
                const replacement = this.generateReplacement();
                mutated = original.substring(0, position) + replacement + original.substring(position + 1);
                description = `Replaced character at position ${position}`;
                break;
            case 'reorder':
                mutated = this.reorderCodeBlocks(original);
                description = 'Reordered code blocks';
                break;
        }
        if (mutated !== original) {
            template.template = mutated;
            return {
                type: mutationType,
                position,
                original: original.substring(Math.max(0, position - 10), position + 10),
                mutated: mutated.substring(Math.max(0, position - 10), position + 10),
                description
            };
        }
        return null;
    }
    applyObfuscation(code) {
        let obfuscated = code;
        // Replace variable names with random ones
        const variables = obfuscated.match(/\b[a-zA-Z_][a-zA-Z0-9_]*\b/g) || [];
        const uniqueVars = [...new Set(variables)];
        for (const variable of uniqueVars) {
            if (!this.isReservedWord(variable)) {
                const randomName = this.generateRandomName();
                const regex = new RegExp(`\\b${variable}\\b`, 'g');
                obfuscated = obfuscated.replace(regex, randomName);
            }
        }
        // Add junk code
        const junkCode = this.generateJunkCode();
        obfuscated = junkCode + obfuscated;
        return obfuscated;
    }
    applyEncryption(code) {
        // Simple string encryption using base64
        const strings = code.match(/['"]([^'"]+)['"]/g) || [];
        let encrypted = code;
        for (const str of strings) {
            const content = str.slice(1, -1);
            const encryptedContent = Buffer.from(content).toString('base64');
            const replacement = `Buffer.from('${encryptedContent}', 'base64').toString()`;
            encrypted = encrypted.replace(str, replacement);
        }
        return encrypted;
    }
    applyStructureMutation(code) {
        // Add nested functions or restructure code
        const functions = code.match(/function\s+(\w+)\s*\([^)]*\)\s*{/g) || [];
        if (functions.length > 0) {
            // Wrap first function in IIFE
            const firstFunction = functions[0];
            const iifeWrapper = `(function() {\n'use strict';\n${firstFunction}`;
            const mutated = code.replace(firstFunction, iifeWrapper);
            // Add closing brace and self-execution
            return mutated + '\n})();';
        }
        return code;
    }
    generateInsertion() {
        const insertions = [
            '// Random comment\n',
            'var dummy = 0;\n',
            'if (false) { /* dead code */ }\n',
            'try { /* error handling */ } catch(e) {}\n',
            '// Debug: ' + Math.random() + '\n'
        ];
        return insertions[Math.floor(Math.random() * insertions.length)];
    }
    generateReplacement() {
        const replacements = ['_', 'x', '1', ' ', '\t', '\n'];
        return replacements[Math.floor(Math.random() * replacements.length)];
    }
    reorderCodeBlocks(code) {
        // Simple block reordering - split by functions and reorder
        const functions = code.split(/function\s+\w+/);
        if (functions.length > 2) {
            const shuffled = functions.slice(1).sort(() => Math.random() - 0.5);
            return functions[0] + 'function ' + shuffled.join('function ');
        }
        return code;
    }
    generateJunkCode() {
        const junk = [
            '// Junk code for obfuscation\nvar _0x1234 = function() { return null; };\n',
            '// Anti-analysis\nif (typeof window !== \'undefined\') debugger;\n',
            '// Random initialization\nvar _0x5678 = Math.random();\n'
        ];
        return junk[Math.floor(Math.random() * junk.length)];
    }
    generateRandomName() {
        const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
        let name = '_';
        for (let i = 0; i < 8; i++) {
            name += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return name + Math.floor(Math.random() * 1000);
    }
    isReservedWord(word) {
        const reserved = [
            'function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'return',
            'class', 'extends', 'new', 'this', 'super', 'try', 'catch', 'finally',
            'throw', 'break', 'continue', 'switch', 'case', 'default', 'do', 'in',
            'typeof', 'instanceof', 'void', 'delete', 'with', 'yield', 'async', 'await'
        ];
        return reserved.includes(word);
    }
    addRandomEvasion(techniques) {
        const newTechniques = [...techniques];
        const possibleTechniques = [
            {
                id: 'random-evasion-' + Math.random(),
                name: 'Random Evasion',
                description: 'Randomly generated evasion technique',
                implementation: '// Random evasion implementation',
                category: 'polymorphism'
            }
        ];
        if (Math.random() < 0.5) {
            newTechniques.push(possibleTechniques[0]);
        }
        return newTechniques;
    }
    shouldTerminate() {
        if (this.generation === 0)
            return false;
        // Check if fitness improvement is stagnating
        if (this.fitnessHistory.length >= 5) {
            const recent = this.fitnessHistory.slice(-5);
            const improvement = recent[4] - recent[0];
            if (improvement < 0.01)
                return true; // Less than 1% improvement in 5 generations
        }
        // Check if we've reached threshold
        const bestFitness = this.population[0].fitness;
        if (bestFitness >= this.config.fitnessThreshold)
            return true;
        return false;
    }
    getBestIndividual() {
        return this.population.reduce((best, current) => current.fitness > best.fitness ? current : best);
    }
    // Public API methods
    getPopulation() {
        return [...this.population];
    }
    getFitnessHistory() {
        return [...this.fitnessHistory];
    }
    getGeneration() {
        return this.generation;
    }
    getStats() {
        const averageFitness = this.population.reduce((sum, ind) => sum + ind.fitness, 0) / this.population.length;
        const bestFitness = this.population[0].fitness;
        let convergenceRate = 0;
        if (this.fitnessHistory.length >= 2) {
            const recent = this.fitnessHistory.slice(-2);
            convergenceRate = (recent[1] - recent[0]) / recent[0];
        }
        return {
            populationSize: this.population.length,
            averageFitness,
            bestFitness,
            generation: this.generation,
            convergenceRate
        };
    }
}
exports.RealGeneticAlgorithm = RealGeneticAlgorithm;
//# sourceMappingURL=RealGeneticAlgorithm.js.map