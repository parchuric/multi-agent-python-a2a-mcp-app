import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Main from './pages/Main';

const App: React.FC = () => {
    return (
        <Router>
            <Switch>
                <Route path="/" component={Main} />
            </Switch>
        </Router>
    );
};

export default App;