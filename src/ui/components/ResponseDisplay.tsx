import React from 'react';

interface ResponseDisplayProps {
    response: string | null;
}

const ResponseDisplay: React.FC<ResponseDisplayProps> = ({ response }) => {
    return (
        <div className="response-display">
            {response ? (
                <p>{response}</p>
            ) : (
                <p>No response available. Please submit a query.</p>
            )}
        </div>
    );
};

export default ResponseDisplay;