import React, { Suspense, lazy, useState, useEffect } from 'react';
import IsolatedPanel from './IsolatedPanel';

// Lazy load the heavy component
const TokenDetailPanel = lazy(() => 
  new Promise(resolve => {
    // Add artificial delay to prevent race conditions
    setTimeout(() => {
      resolve(import('./TokenDetailPanel'));
    }, 100);
  })
);

const LazyTokenDetailPanel = ({ analysis, loading, error, tokenKey }) => {
  const [panelKey, setPanelKey] = useState(`token-${Date.now()}`);

  // Generate new key when token changes to force remount
  useEffect(() => {
    if (tokenKey) {
      setPanelKey(`token-${tokenKey}-${Date.now()}`);
    }
  }, [tokenKey]);

  const LoadingFallback = () => (
    <div className="isolated-panel-loading" style={{
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(20px)',
      borderRadius: '20px'
    }}>
      <div className="loading-spinner" style={{
        width: '40px',
        height: '40px',
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #667eea',
        borderRadius: '50%',
        margin: '0 auto 1rem'
      }}></div>
      <div style={{ color: '#666' }}>Loading Token Details...</div>
    </div>
  );

  return (
    <IsolatedPanel
      panelKey={panelKey}
      loading={loading}
      error={error}
    >
      <Suspense fallback={<LoadingFallback />}>
        <TokenDetailPanel 
          analysis={analysis} 
          loading={loading} 
          error={error} 
        />
      </Suspense>
    </IsolatedPanel>
  );
};

export default LazyTokenDetailPanel;