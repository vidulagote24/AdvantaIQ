import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import { CurrencyProvider } from './context/CurrencyContext';
import { WorkflowProvider } from './context/WorkflowContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <CurrencyProvider>
      <WorkflowProvider>
        <App />
      </WorkflowProvider>
    </CurrencyProvider>
  </React.StrictMode>,
);