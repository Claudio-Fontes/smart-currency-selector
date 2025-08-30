import React, { useState, useEffect } from 'react';
import HotPoolsPanel from './components/HotPoolsPanel';
import LazyTokenDetailPanel from './components/LazyTokenDetailPanel';
import IsolatedPanel from './components/IsolatedPanel';
import ErrorBoundary from './components/ErrorBoundary';
import { useHotPools, useTokenAnalysis } from './hooks/useHotPools';
import './styles/App.css';

const App = () => {
  const [selectedPool, setSelectedPool] = useState(null);
  const [poolsKey, setPoolsKey] = useState(`pools-${Date.now()}`);
  const [tokenKey, setTokenKey] = useState(null);
  const poolLimit = 30;
  
  const { pools, loading: poolsLoading, error: poolsError, refetch } = useHotPools(poolLimit);
  const { analysis, loading: analysisLoading, error: analysisError, fetchTokenAnalysis, clearAnalysis } = useTokenAnalysis();

  // Debug logging
  console.log('🏊 App state - pools:', pools?.length || 0, 'loading:', poolsLoading, 'error:', poolsError);

  const handlePoolSelect = (pool) => {
    console.log('📋 App: Pool selected:', pool);
    if (!pool) return;
    
    // Prevent unnecessary state updates
    const selectedAddr = selectedPool?.poolAddress || selectedPool?.address;
    const poolAddr = pool.poolAddress || pool.address;
    
    if (selectedAddr && poolAddr && selectedAddr === poolAddr) {
      console.log('📋 App: Same pool selected, skipping');
      return;
    }
    
    console.log('📋 App: Processing new pool selection');
    
    // Force remount of token panel with new key
    const newTokenKey = pool.mainToken?.address || `token-${Date.now()}`;
    setTokenKey(newTokenKey);
    
    clearAnalysis();
    setSelectedPool(pool);
    
    console.log('📋 App: Token address to analyze:', pool.mainToken?.address);
    
    // Small delay to prevent race conditions
    setTimeout(() => {
      if (pool.mainToken && pool.mainToken.address) {
        fetchTokenAnalysis(pool.mainToken.address);
      }
    }, 100);
  };

  const handleRefresh = () => {
    setPoolsKey(`pools-${Date.now()}`);
    refetch();
  };

  // Auto-select first pool
  useEffect(() => {
    if (pools && pools.length > 0 && !selectedPool && !poolsLoading) {
      handlePoolSelect(pools[0]);
    }
  }, [pools, selectedPool, poolsLoading]);

  const formatNumber = (num) => {
    if (!num || isNaN(num)) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            🔥 Solana Hot Pools Dashboard
          </div>
          <div className="stats">
            <div className="stat-item">
              📊 {pools ? pools.length : 0} Pools Loaded
            </div>
            <div className="stat-item">
              🏆 Top {poolLimit} Ranking
            </div>
            <div className="stat-item">
              ⚡ Real-time Data
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        <div className="pools-panel-wrapper" style={{ flex: '0 0 45%', minWidth: '450px' }}>
          <ErrorBoundary>
            <IsolatedPanel
              panelKey={poolsKey}
              loading={poolsLoading}
              error={poolsError}
            >
              <HotPoolsPanel
                pools={pools}
                loading={poolsLoading}
                error={poolsError}
                onPoolSelect={handlePoolSelect}
                selectedPool={selectedPool}
                onRefresh={handleRefresh}
              />
            </IsolatedPanel>
          </ErrorBoundary>
        </div>

        <div className="token-detail-wrapper" style={{ flex: '0 0 55%', minWidth: '500px' }}>
          <ErrorBoundary>
            <LazyTokenDetailPanel
              analysis={analysis}
              loading={analysisLoading}
              error={analysisError}
              tokenKey={tokenKey}
            />
          </ErrorBoundary>
        </div>
      </main>
    </div>
  );
};

export default App;