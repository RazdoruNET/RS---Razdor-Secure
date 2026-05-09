declare module 'pcap-parser' {
  interface PcapHeader {
    magicNumber: number;
    versionMajor: number;
    versionMinor: number;
    gmtOffset: number;
    timestampAccuracy: number;
    snapshotLength: number;
    linkLayerType: number;
  }

  interface PcapPacket {
    header: {
      ts_sec: number;
      ts_usec: number;
      incl_len: number;
      orig_len: number;
    };
    data: Buffer;
  }

  class PcapParser {
    constructor(filePath: string);
    on(event: 'packet', callback: (packet: PcapPacket) => void): void;
    on(event: 'header', callback: (header: PcapHeader) => void): void;
    on(event: 'complete', callback: () => void): void;
    on(event: 'error', callback: (error: Error) => void): void;
    parse(): void;
  }

  export = PcapParser;
}
