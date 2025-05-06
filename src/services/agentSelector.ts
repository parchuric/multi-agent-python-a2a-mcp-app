export const selectAgent = (query: string): string => {
    const lowerCaseQuery = query.toLowerCase();

    if (lowerCaseQuery.includes("weather")) {
        return "WeatherAgent";
    } else if (lowerCaseQuery.includes("sports")) {
        return "SportsAgent";
    } else if (lowerCaseQuery.includes("news") || lowerCaseQuery.includes("breaking")) {
        return "NewsAgent";
    } else if (lowerCaseQuery.includes("stock") || lowerCaseQuery.includes("market")) {
        return "StocksAgent";
    } else if (lowerCaseQuery.includes("fitness") || lowerCaseQuery.includes("health")) {
        return "HealthAgent";
    } else {
        throw new Error("No suitable agent found for the query.");
    }
};