import React, { useState, useEffect } from 'react';
import HotOpportunitiesPanel from './components/HotOpportunitiesPanel';
import MarketIntelligencePanel from './components/MarketIntelligencePanel';
import TradingPerformancePanel from './components/TradingPerformancePanel';
import TickerBar from './components/TickerBar';
import ErrorBoundary from './components/ErrorBoundary';
import { useHotPools, useTokenAnalysis } from './hooks/useHotPools';
import usePositions from './hooks/usePositions';
import './styles/App.css';
import './styles/panels.css';

// Force webpack recompilation with updated API and CSS - DEBUG STICKER VERSION
const App = () => {
  const [selectedPool, setSelectedPool] = useState(null);
  const [poolsKey, setPoolsKey] = useState(`pools-${Date.now()}`);
  const [tokenKey, setTokenKey] = useState(null);
  const poolLimit = 50;
  
  const { pools, loading: poolsLoading, error: poolsError, refetch } = useHotPools(poolLimit);
  const { analysis, loading: analysisLoading, error: analysisError, fetchTokenAnalysis, clearAnalysis } = useTokenAnalysis();
  const { positions } = usePositions(60000); // Para o ticker bar

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
    
    // Disabled automatic token analysis to prevent timeouts
    // User can manually request token analysis if needed
    // setTimeout(() => {
    //   if (pool.mainToken && pool.mainToken.address) {
    //     fetchTokenAnalysis(pool.mainToken.address);
    //   }
    // }, 100);
  };

  const handleRefresh = () => {
    setPoolsKey(`pools-${Date.now()}`);
    refetch();
  };

  // Disabled auto-select to prevent timeouts
  // useEffect(() => {
  //   if (pools && pools.length > 0 && !selectedPool && !poolsLoading) {
  //     handlePoolSelect(pools[0]);
  //   }
  // }, [pools, selectedPool, poolsLoading]);

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
            🚀 Solana Trading Intelligence Dashboard
          </div>
          <div className="stats">
            <div className="stat-item">
              🔥 {pools ? pools.length : 0} Hot Opportunities
            </div>
            <div className="stat-item">
              📊 Advanced Analytics
            </div>
            <div className="stat-item">
              ⚡ Real-time Intelligence
            </div>
            <div className="stat-item">
              🎯 Performance Tracking
            </div>
          </div>
        </div>
      </header>

      {/* Ticker Bar - Posições rolando */}
      <ErrorBoundary>
        <TickerBar positions={positions} />
      </ErrorBoundary>

      {/* Main Content - Revolutionary 3 Panel Layout */}
      <main className="main-content">
        <div className="opportunities-panel-wrapper" style={{ flex: '1', minWidth: '350px' }}>
          <ErrorBoundary>
            <HotOpportunitiesPanel
              pools={pools}
              loading={poolsLoading}
              error={poolsError}
              onPoolSelect={handlePoolSelect}
              selectedPool={selectedPool}
              onRefresh={handleRefresh}
            />
          </ErrorBoundary>
        </div>

        <div className="intelligence-panel-wrapper" style={{ flex: '1', minWidth: '400px' }}>
          <ErrorBoundary>
            <MarketIntelligencePanel
              selectedPool={selectedPool}
            />
          </ErrorBoundary>
        </div>

        <div className="performance-panel-wrapper" style={{ flex: '1', minWidth: '400px' }}>
          <ErrorBoundary>
            <TradingPerformancePanel />
          </ErrorBoundary>
        </div>
      </main>

      {/* Claude Code Sticker */}
      <div className="claude-sticker">
        🤖 <span className="claude-logo">Claude Code</span>
      </div>
    </div>
  );
};

export default App;