import React, { useState, useEffect } from 'react';
import TokenDetailPanelSimple from './TokenDetailPanelSimple';

// Simplified component without lazy loading to fix chunk error
const LazyTokenDetailPanel = ({ analysis, loading, error, tokenKey }) => {
  const [panelKey, setPanelKey] = useState(`token-${Date.now()}`);

  // Generate new key when token changes to force remount
  useEffect(() => {
    if (tokenKey) {
      setPanelKey(`token-${tokenKey}-${Date.now()}`);
    }
  }, [tokenKey]);

  return (
    <TokenDetailPanelSimple 
      key={panelKey}
      analysis={analysis} 
      loading={loading} 
      error={error} 
    />
  );
};

export default LazyTokenDetailPanel;