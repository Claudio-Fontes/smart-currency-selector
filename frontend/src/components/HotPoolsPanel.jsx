import React from 'react';
import { useAnalyzer } from '../hooks/useAnalyzer';

const HotPoolsPanel = ({ pools, loading, error, onPoolSelect, selectedPool, onRefresh }) => {
  const { status: analyzerStatus, getTokenStatus, startAnalyzer } = useAnalyzer();
  if (loading) {
    return (
      <div className="hot-pools-panel">
        <div className="loading">
          <div className="loading-spinner"></div>
          Loading hot pools...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="hot-pools-panel">
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
        <button className="refresh-btn" onClick={onRefresh}>
          🔄 Try Again
        </button>
      </div>
    );
  }

  const handlePoolClick = (pool) => {
    console.log('🖱️ Pool clicked:', pool);
    if (onPoolSelect) {
      onPoolSelect(pool);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'N/A';
    }
  };

  const formatAddress = (address) => {
    if (!address || address.length < 8) return address || 'N/A';
    return `${address.slice(0, 4)}...${address.slice(-4)}`;
  };

  const isSelected = (pool) => {
    if (!selectedPool || !pool) return false;
    
    const selectedAddr = selectedPool.poolAddress || selectedPool.address;
    const poolAddr = pool.poolAddress || pool.address;
    
    return selectedAddr && poolAddr && selectedAddr === poolAddr;
  };

  return (
    <div className="hot-pools-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">🔥 Hot Pools</h2>
          {analyzerStatus && (
            <div className="analyzer-status-mini">
              <span className={`status-dot ${analyzerStatus.is_running ? 'running' : 'stopped'}`}></span>
              <span className="status-text">
                AI: {analyzerStatus.is_running ? 'ON' : 'OFF'}
              </span>
              {!analyzerStatus.is_running && (
                <button className="start-analyzer-btn" onClick={startAnalyzer} title="Start AI Analyzer">
                  ▶️
                </button>
              )}
            </div>
          )}
        </div>
        <button className="refresh-btn" onClick={onRefresh} disabled={loading}>
          🔄 Refresh
        </button>
      </div>

      <div className="pools-list">
        {Array.isArray(pools) && pools.map((pool, index) => {
          if (!pool) return null;
          
          const uniqueKey = `pool-${pool.address || pool.poolAddress || pool.id || index}`;
          const tokenAddress = pool.mainToken?.address;
          const tokenStatus = getTokenStatus(tokenAddress);
          
          return (
            <div
              key={uniqueKey}
              className={`pool-item ${isSelected(pool) ? 'selected' : ''} ${tokenStatus ? `analysis-${tokenStatus.status}` : ''}`}
              onClick={() => handlePoolClick(pool)}
            >
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <div className="pool-rank">
                  {pool.rank || index + 1}
                </div>
                
                <div className="pool-info">
                  <div className="pool-main">
                    <div className="pool-pair">
                      {pool.pair || `${pool.mainToken?.symbol || '?'}/${pool.sideToken?.symbol || '?'}`}
                      {tokenStatus && (
                        <span className={`analysis-badge ${tokenStatus.status}`}>
                          {tokenStatus.status === 'approved' ? (
                            <span title={`Score: ${tokenStatus.score?.toFixed(0) || 0}/100`}>
                              ✅ {tokenStatus.score?.toFixed(0) || 0}
                            </span>
                          ) : (
                            <span title={tokenStatus.reasons?.join('; ')}>
                              ❌ Rejected
                            </span>
                          )}
                        </span>
                      )}
                    </div>
                    <div className="pool-details">
                      <span>🏪 {pool.exchange?.name || 'Unknown DEX'}</span>
                      <span>🏊 {formatAddress(pool.poolAddress || pool.address)}</span>
                    </div>
                  </div>
                  
                  <div className="pool-meta">
                    <div>📅 {formatDate(pool.createdAt || pool.creationTime)}</div>
                    {pool.fee > 0 && <div>💳 {pool.fee}%</div>}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {(!pools || pools.length === 0) && !loading && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
          No hot pools found
        </div>
      )}
    </div>
  );
};

export default HotPoolsPanel;