declare module 'glob' {
  function glob(pattern: string, options?: any): Promise<string[]>;
  function glob(pattern: string, callback: (err: Error | null, matches: string[]) => void): void;
  export = glob;
}
