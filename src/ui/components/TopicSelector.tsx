import React from 'react';

const topics = [
    { value: 'weather', label: 'Weather' },
    { value: 'sports', label: 'Sports' },
    { value: 'news', label: 'Breaking News' },
    { value: 'stocks', label: 'Stock Market' },
    { value: 'health', label: 'Fitness/Healthcare' },
];

const TopicSelector: React.FC<{ onSelect: (topic: string) => void }> = ({ onSelect }) => {
    const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        onSelect(event.target.value);
    };

    return (
        <div>
            <label htmlFor="topic-selector">Select a Topic:</label>
            <select id="topic-selector" onChange={handleChange}>
                {topics.map(topic => (
                    <option key={topic.value} value={topic.value}>
                        {topic.label}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default TopicSelector;