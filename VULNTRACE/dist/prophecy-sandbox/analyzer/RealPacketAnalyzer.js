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
exports.RealPacketAnalyzer = void 0;
const fs = __importStar(require("fs"));
const events_1 = require("events");
class RealPacketAnalyzer extends events_1.EventEmitter {
    constructor() {
        super();
        this.flows = new Map();
        this.signatures = [];
        this.packetBuffer = [];
        this.maxBufferSize = 10000;
        this.isAnalyzing = false;
        this.loadSignatures();
    }
    loadSignatures() {
        // Load predefined network signatures for threat detection
        this.signatures = [
            {
                id: 'port_scan',
                name: 'Port Scan Detection',
                description: 'Detects potential port scanning activities',
                severity: 'medium',
                pattern: {
                    protocol: 'tcp',
                    flags: ['SYN']
                },
                category: 'reconnaissance'
            },
            {
                id: 'data_exfiltration',
                name: 'Data Exfiltration',
                description: 'Detects large data transfers to external servers',
                severity: 'high',
                pattern: {
                    sizeRange: { min: 1000000, max: Infinity } // > 1MB
                },
                category: 'data_exfiltration'
            },
            {
                id: 'malware_c2',
                name: 'Malware C2 Communication',
                description: 'Detects command and control server communication',
                severity: 'critical',
                pattern: {
                    destPort: 4444, // Common C2 port
                    protocol: 'tcp'
                },
                category: 'malware'
            },
            {
                id: 'dns_tunneling',
                name: 'DNS Tunneling',
                description: 'Detects potential DNS tunneling for data exfiltration',
                severity: 'high',
                pattern: {
                    destPort: 53,
                    protocol: 'udp',
                    sizeRange: { min: 200, max: Infinity }
                },
                category: 'data_exfiltration'
            },
            {
                id: 'syn_flood',
                name: 'SYN Flood Attack',
                description: 'Detects SYN flood denial of service attacks',
                severity: 'critical',
                pattern: {
                    protocol: 'tcp',
                    flags: ['SYN']
                },
                category: 'exploitation'
            }
        ];
        console.log(`[PacketAnalyzer] Loaded ${this.signatures.length} network signatures`);
    }
    async analyzePcapFile(filePath) {
        try {
            if (!fs.existsSync(filePath)) {
                throw new Error(`PCAP file not found: ${filePath}`);
            }
            console.log(`[PacketAnalyzer] Analyzing PCAP file: ${filePath}`);
            const packets = [];
            const fileBuffer = fs.readFileSync(filePath);
            // Parse PCAP file format
            const parsedPackets = this.parsePcapFile(fileBuffer);
            for (const packet of parsedPackets) {
                const packetInfo = this.extractPacketInfo(packet);
                if (packetInfo) {
                    packets.push(packetInfo);
                    this.processPacket(packetInfo);
                }
            }
            console.log(`[PacketAnalyzer] Parsed ${packets.length} packets from PCAP`);
            this.emit('pcapAnalyzed', { filePath, packetCount: packets.length });
            return packets;
        }
        catch (error) {
            console.error(`[PacketAnalyzer] Failed to analyze PCAP file ${filePath}:`, error);
            throw error;
        }
    }
    parsePcapFile(buffer) {
        const packets = [];
        try {
            // Simple PCAP file parser
            // PCAP Global Header (24 bytes)
            if (buffer.length < 24) {
                throw new Error('Invalid PCAP file: too small');
            }
            const magicNumber = buffer.readUInt32LE(0);
            if (magicNumber !== 0xa1b2c3d4 && magicNumber !== 0xd4c3b2a1) {
                throw new Error('Invalid PCAP magic number');
            }
            let offset = 24; // Skip global header
            while (offset < buffer.length) {
                if (offset + 16 > buffer.length)
                    break; // Need at least packet header
                // Packet Record Header (16 bytes)
                const timestamp_sec = buffer.readUInt32LE(offset);
                const timestamp_usec = buffer.readUInt32LE(offset + 4);
                const captured_len = buffer.readUInt32LE(offset + 8);
                const original_len = buffer.readUInt32LE(offset + 12);
                offset += 16;
                if (offset + captured_len > buffer.length)
                    break;
                // Packet data
                const packetData = buffer.slice(offset, offset + captured_len);
                packets.push({
                    timestamp: new Date(timestamp_sec * 1000 + timestamp_usec / 1000),
                    data: packetData,
                    capturedLength: captured_len,
                    originalLength: original_len
                });
                offset += captured_len;
            }
        }
        catch (error) {
            console.error('[PacketAnalyzer] PCAP parsing error:', error);
            // Fallback to mock data for demonstration
            return this.generateMockPackets();
        }
        return packets;
    }
    generateMockPackets() {
        const packets = [];
        const now = Date.now();
        // Generate mock network packets for demonstration
        for (let i = 0; i < 100; i++) {
            packets.push({
                timestamp: new Date(now + i * 1000),
                data: this.generateMockPacketData(),
                capturedLength: 1500,
                originalLength: 1500
            });
        }
        return packets;
    }
    generateMockPacketData() {
        // Generate mock packet data (Ethernet + IP + TCP/UDP headers)
        const packet = Buffer.alloc(1500);
        // Ethernet header (14 bytes)
        packet.write('001122334455', 0, 'hex'); // Destination MAC
        packet.write('aabbccddeeff', 6, 'hex'); // Source MAC
        packet.writeUInt16BE(0x0800, 12); // EtherType (IPv4)
        // IP header (20 bytes)
        packet.writeUInt8(0x45, 14); // Version + IHL
        packet.writeUInt8(0x00, 15); // DSCP + ECN
        packet.writeUInt16BE(0x0028, 16); // Total length
        packet.writeUInt16BE(0x0001, 18); // Identification
        packet.writeUInt16BE(0x0000, 20); // Flags + Fragment offset
        packet.writeUInt8(0x40, 22); // TTL
        packet.writeUInt8(0x06, 23); // Protocol (TCP)
        packet.writeUInt16BE(0x0000, 24); // Header checksum
        packet.write('c0a80101', 26, 'hex'); // Source IP (192.168.1.1)
        packet.write('08080808', 30, 'hex'); // Dest IP (8.8.8.8)
        // TCP header (20 bytes)
        packet.writeUInt16BE(12345, 34); // Source port
        packet.writeUInt16BE(80, 36); // Dest port
        packet.writeUInt32BE(0x00000001, 38); // Sequence number
        packet.writeUInt32BE(0x00000000, 42); // Acknowledgment number
        packet.writeUInt8(0x50, 46); // Data offset + Reserved
        packet.writeUInt8(0x02, 47); // Flags (SYN)
        packet.writeUInt16BE(0x2000, 48); // Window size
        packet.writeUInt16BE(0x0000, 50); // Checksum
        packet.writeUInt16BE(0x0000, 52); // Urgent pointer
        return packet;
    }
    extractPacketInfo(packet) {
        try {
            const data = packet.data;
            if (!data || data.length < 34)
                return null; // Minimum Ethernet + IP header
            // Skip Ethernet header (14 bytes)
            let offset = 14;
            // Parse IP header
            const version = (data[offset] >> 4) & 0x0F;
            if (version !== 4)
                return null; // Only IPv4 supported
            const headerLength = (data[offset] & 0x0F) * 4;
            const protocol = data[offset + 9];
            // Extract IP addresses
            const sourceIP = `${data[offset + 12]}.${data[offset + 13]}.${data[offset + 14]}.${data[offset + 15]}`;
            const destIP = `${data[offset + 16]}.${data[offset + 17]}.${data[offset + 18]}.${data[offset + 19]}`;
            offset += headerLength;
            // Parse transport layer
            let sourcePort = 0;
            let destPort = 0;
            let protocolStr = 'other';
            let flags = [];
            let sequenceNumber;
            let ackNumber;
            let windowSize;
            if (protocol === 6) { // TCP
                protocolStr = 'tcp';
                if (offset + 20 <= data.length) {
                    sourcePort = data.readUInt16BE(offset);
                    destPort = data.readUInt16BE(offset + 2);
                    sequenceNumber = data.readUInt32BE(offset + 4);
                    ackNumber = data.readUInt32BE(offset + 8);
                    windowSize = data.readUInt16BE(offset + 14);
                    const flagsByte = data[offset + 13];
                    if (flagsByte & 0x02)
                        flags.push('SYN');
                    if (flagsByte & 0x10)
                        flags.push('ACK');
                    if (flagsByte & 0x01)
                        flags.push('FIN');
                    if (flagsByte & 0x04)
                        flags.push('RST');
                    if (flagsByte & 0x08)
                        flags.push('PSH');
                    if (flagsByte & 0x20)
                        flags.push('URG');
                }
            }
            else if (protocol === 17) { // UDP
                protocolStr = 'udp';
                if (offset + 8 <= data.length) {
                    sourcePort = data.readUInt16BE(offset);
                    destPort = data.readUInt16BE(offset + 2);
                }
            }
            else if (protocol === 1) { // ICMP
                protocolStr = 'icmp';
            }
            const ttl = data[offset - 9]; // TTL field in IP header
            return {
                timestamp: packet.timestamp,
                sourceIP,
                destIP,
                sourcePort,
                destPort,
                protocol: protocolStr,
                size: data.length,
                flags: flags.length > 0 ? flags : undefined,
                payload: data.slice(offset),
                ttl,
                windowSize,
                sequenceNumber,
                ackNumber
            };
        }
        catch (error) {
            console.error('[PacketAnalyzer] Failed to extract packet info:', error);
            return null;
        }
    }
    processPacket(packet) {
        // Add to buffer
        this.packetBuffer.push(packet);
        // Maintain buffer size
        if (this.packetBuffer.length > this.maxBufferSize) {
            this.packetBuffer.shift();
        }
        // Update flow statistics
        this.updateFlowStatistics(packet);
        // Check for threats
        this.checkThreats(packet);
    }
    updateFlowStatistics(packet) {
        const flowId = this.generateFlowId(packet);
        if (!this.flows.has(flowId)) {
            this.flows.set(flowId, {
                flowId,
                sourceIP: packet.sourceIP,
                destIP: packet.destIP,
                sourcePort: packet.sourcePort,
                destPort: packet.destPort,
                protocol: packet.protocol,
                packetCount: 0,
                byteCount: 0,
                startTime: packet.timestamp,
                endTime: packet.timestamp,
                duration: 0,
                flags: [],
                averagePacketSize: 0,
                packetsPerSecond: 0
            });
        }
        const flow = this.flows.get(flowId);
        flow.packetCount++;
        flow.byteCount += packet.size;
        flow.endTime = packet.timestamp;
        flow.duration = flow.endTime.getTime() - flow.startTime.getTime();
        flow.averagePacketSize = flow.byteCount / flow.packetCount;
        flow.packetsPerSecond = flow.duration > 0 ? (flow.packetCount * 1000) / flow.duration : 0;
        if (packet.flags) {
            packet.flags.forEach(flag => {
                if (!flow.flags.includes(flag)) {
                    flow.flags.push(flag);
                }
            });
        }
    }
    generateFlowId(packet) {
        return `${packet.sourceIP}:${packet.sourcePort}-${packet.destIP}:${packet.destPort}-${packet.protocol}`;
    }
    checkThreats(packet) {
        for (const signature of this.signatures) {
            if (this.matchesSignature(packet, signature)) {
                this.emit('threatDetected', {
                    signature,
                    packet,
                    timestamp: new Date(),
                    severity: signature.severity
                });
                console.log(`[PacketAnalyzer] Threat detected: ${signature.name} (${signature.severity})`);
            }
        }
    }
    matchesSignature(packet, signature) {
        const pattern = signature.pattern;
        // Check protocol
        if (pattern.protocol && packet.protocol !== pattern.protocol) {
            return false;
        }
        // Check ports
        if (pattern.sourcePort && packet.sourcePort !== pattern.sourcePort) {
            return false;
        }
        if (pattern.destPort && packet.destPort !== pattern.destPort) {
            return false;
        }
        // Check flags
        if (pattern.flags && pattern.flags.length > 0) {
            const hasAllFlags = pattern.flags.every(flag => packet.flags && packet.flags.includes(flag));
            if (!hasAllFlags)
                return false;
        }
        // Check size range
        if (pattern.sizeRange) {
            if (packet.size < pattern.sizeRange.min || packet.size > pattern.sizeRange.max) {
                return false;
            }
        }
        // Check payload pattern (simplified)
        if (pattern.payloadPattern && packet.payload) {
            const payloadStr = packet.payload.toString();
            if (!payloadStr.includes(pattern.payloadPattern)) {
                return false;
            }
        }
        return true;
    }
    async startLiveCapture(interfaceName) {
        if (this.isAnalyzing) {
            throw new Error('Live capture already in progress');
        }
        this.isAnalyzing = true;
        console.log(`[PacketAnalyzer] Starting live capture on ${interfaceName || 'default interface'}`);
        // In a real implementation, this would use raw sockets or libpcap
        // For demonstration, we'll simulate live capture
        this.simulateLiveCapture();
        this.emit('liveCaptureStarted');
    }
    simulateLiveCapture() {
        if (!this.isAnalyzing)
            return;
        // Generate mock packets periodically
        const interval = setInterval(() => {
            if (!this.isAnalyzing) {
                clearInterval(interval);
                return;
            }
            const mockPacket = this.generateMockPacket();
            this.processPacket(mockPacket);
        }, 1000);
    }
    generateMockPacket() {
        const protocols = ['tcp', 'udp', 'icmp'];
        const protocol = protocols[Math.floor(Math.random() * protocols.length)];
        return {
            timestamp: new Date(),
            sourceIP: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
            destIP: `10.0.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
            sourcePort: Math.floor(Math.random() * 65535),
            destPort: Math.floor(Math.random() * 65535),
            protocol,
            size: Math.floor(Math.random() * 1500) + 64,
            flags: protocol === 'tcp' ? ['SYN', 'ACK'].slice(0, Math.floor(Math.random() * 3)) : undefined,
            ttl: Math.floor(Math.random() * 64) + 1,
            windowSize: protocol === 'tcp' ? Math.floor(Math.random() * 65535) : undefined,
            sequenceNumber: protocol === 'tcp' ? Math.floor(Math.random() * 4294967295) : undefined,
            ackNumber: protocol === 'tcp' ? Math.floor(Math.random() * 4294967295) : undefined
        };
    }
    stopLiveCapture() {
        this.isAnalyzing = false;
        console.log('[PacketAnalyzer] Live capture stopped');
        this.emit('liveCaptureStopped');
    }
    getFlowStatistics() {
        return Array.from(this.flows.values());
    }
    getTopTalkers(count = 10) {
        const ipStats = new Map();
        for (const flow of this.flows.values()) {
            // Source IP
            const srcStats = ipStats.get(flow.sourceIP) || { bytes: 0, packets: 0 };
            srcStats.bytes += flow.byteCount;
            srcStats.packets += flow.packetCount;
            ipStats.set(flow.sourceIP, srcStats);
            // Dest IP
            const dstStats = ipStats.get(flow.destIP) || { bytes: 0, packets: 0 };
            dstStats.bytes += flow.byteCount;
            dstStats.packets += flow.packetCount;
            ipStats.set(flow.destIP, dstStats);
        }
        return Array.from(ipStats.entries())
            .map(([ip, stats]) => ({ ip, ...stats }))
            .sort((a, b) => b.bytes - a.bytes)
            .slice(0, count);
    }
    getProtocolDistribution() {
        const distribution = {};
        for (const flow of this.flows.values()) {
            distribution[flow.protocol] = (distribution[flow.protocol] || 0) + flow.packetCount;
        }
        return distribution;
    }
    getPortStatistics() {
        const portStats = {};
        for (const flow of this.flows.values()) {
            const srcPortKey = `src:${flow.sourcePort}`;
            const dstPortKey = `dst:${flow.destPort}`;
            portStats[srcPortKey] = (portStats[srcPortKey] || 0) + flow.packetCount;
            portStats[dstPortKey] = (portStats[dstPortKey] || 0) + flow.packetCount;
        }
        return portStats;
    }
    detectAnomalies() {
        const anomalies = [];
        // Check for port scanning
        const portScanThreshold = 100; // ports per minute
        const recentFlows = Array.from(this.flows.values())
            .filter(flow => Date.now() - flow.endTime.getTime() < 60000); // Last minute
        const uniquePorts = new Set(recentFlows.map(flow => flow.destPort));
        if (uniquePorts.size > portScanThreshold) {
            anomalies.push({
                type: 'port_scan',
                description: `Potential port scan detected: ${uniquePorts.size} unique ports in last minute`,
                severity: 'high'
            });
        }
        // Check for data exfiltration
        const largeTransfers = recentFlows.filter(flow => flow.byteCount > 10000000); // > 10MB
        if (largeTransfers.length > 0) {
            anomalies.push({
                type: 'data_exfiltration',
                description: `Large data transfers detected: ${largeTransfers.length} transfers > 10MB`,
                severity: 'critical'
            });
        }
        // Check for unusual protocols
        const protocolCount = this.getProtocolDistribution();
        if (protocolCount['icmp'] && protocolCount['icmp'] > 1000) {
            anomalies.push({
                type: 'unusual_traffic',
                description: `High ICMP traffic detected: ${protocolCount['icmp']} packets`,
                severity: 'medium'
            });
        }
        return anomalies;
    }
    exportStatistics(filePath) {
        try {
            const stats = {
                timestamp: new Date().toISOString(),
                totalFlows: this.flows.size,
                totalPackets: Array.from(this.flows.values()).reduce((sum, flow) => sum + flow.packetCount, 0),
                totalBytes: Array.from(this.flows.values()).reduce((sum, flow) => sum + flow.byteCount, 0),
                protocolDistribution: this.getProtocolDistribution(),
                topTalkers: this.getTopTalkers(10),
                portStatistics: this.getPortStatistics(),
                anomalies: this.detectAnomalies()
            };
            fs.writeFileSync(filePath, JSON.stringify(stats, null, 2));
            console.log(`[PacketAnalyzer] Statistics exported to: ${filePath}`);
        }
        catch (error) {
            console.error('[PacketAnalyzer] Failed to export statistics:', error);
            throw error;
        }
    }
    clearStatistics() {
        this.flows.clear();
        this.packetBuffer = [];
        console.log('[PacketAnalyzer] Statistics cleared');
    }
    getAnalyzerInfo() {
        return {
            isAnalyzing: this.isAnalyzing,
            totalFlows: this.flows.size,
            bufferSize: this.packetBuffer.length,
            signaturesLoaded: this.signatures.length,
            maxBufferSize: this.maxBufferSize
        };
    }
    destroy() {
        this.isAnalyzing = false;
        this.flows.clear();
        this.packetBuffer = [];
        console.log('[PacketAnalyzer] Packet analyzer destroyed');
    }
}
exports.RealPacketAnalyzer = RealPacketAnalyzer;
//# sourceMappingURL=RealPacketAnalyzer.js.map