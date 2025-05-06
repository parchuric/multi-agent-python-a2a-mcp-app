export interface Agent {
  handleQuery(query: string): Promise<string>;
  getName(): string;
  getDescription(): string;
}

