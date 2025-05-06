export interface UserQuery {
    queryText: string;
    topic: 'weather' | 'sports' | 'breaking news' | 'stock market' | 'fitness/healthcare';
    timestamp: Date;
    userId?: string;
}