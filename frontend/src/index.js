import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

// Get container with better error handling
const container = document.getElementById('root');

if (!container) {
  console.error('Root container not found');
} else {
  // Clear any existing content safely
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }

  // Use React 17 render method - no concurrent features
  try {
    ReactDOM.render(<App />, container);
  } catch (error) {
    console.error('Failed to render React app:', error);
  }
}