import React, { useState } from 'react';

const QueryInput: React.FC<{ onSubmit: (query: string) => void }> = ({ onSubmit }) => {
    const [query, setQuery] = useState('');

    const handleSubmit = (event: React.FormEvent) => {
        event.preventDefault();
        if (query.trim()) {
            onSubmit(query);
            setQuery('');
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask your question..."
                required
            />
            <button type="submit">Submit</button>
        </form>
    );
};

export default QueryInput;