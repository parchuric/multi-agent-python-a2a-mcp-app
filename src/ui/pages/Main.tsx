import React, { useState } from 'react';
import QueryInput from '../components/QueryInput';
import ResponseDisplay from '../components/ResponseDisplay';
import TopicSelector from '../components/TopicSelector';

const Main: React.FC = () => {
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState('');
    const [topic, setTopic] = useState('weather');

    const handleQuerySubmit = async () => {
        // Logic to send the query to the appropriate agent based on the selected topic
        // and update the response state with the result.
        // This is a placeholder for the actual implementation.
        const fetchedResponse = await fetchResponseFromAgent(query, topic);
        setResponse(fetchedResponse);
    };

    const fetchResponseFromAgent = async (query: string, topic: string) => {
        // Placeholder function to simulate fetching response from the agent
        return `Response for ${topic} query: ${query}`;
    };

    return (
        <div>
            <h1>Multi-Agent Application</h1>
            <TopicSelector selectedTopic={topic} onTopicChange={setTopic} />
            <QueryInput query={query} onQueryChange={setQuery} onSubmit={handleQuerySubmit} />
            <ResponseDisplay response={response} />
        </div>
    );
};

export default Main;