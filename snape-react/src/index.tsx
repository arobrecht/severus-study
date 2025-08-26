import React from 'react';
import ReactDOM from 'react-dom/client';
import Experiment from './Experiment';

document.addEventListener('DOMContentLoaded', function (event) {
    // we inject our react webapp into an HTML element with id 'root'
    const root = ReactDOM.createRoot(
        document.getElementById('root') as HTMLElement
    );
    // the socketPath is set as a window property by the flask app.
    root.render(
        <React.StrictMode>
            <Experiment socketPath={(window as any).socketPath as string} feedbackMode={(window as any).feedbackMode as any} isBaseline={(window as any).isBaseline as any}/>
        </React.StrictMode>
    );
});

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
