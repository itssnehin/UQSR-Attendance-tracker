import React from 'react';
import ReactDOM from 'react-dom/client';
// import './index.css'; // Temporarily disabled
import App from './App';
import AppProvider from './context/AppProvider';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <AppProvider>
      <App />
    </AppProvider>
  </React.StrictMode>
);