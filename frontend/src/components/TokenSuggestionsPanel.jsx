import React, { useState, useEffect } from 'react';
import { analyzerAPI } from '../services/api';

const TokenSuggestionsPanel = () => {
  const [status, setStatus] = useState(null);
  const [suggestions, setSuggestions] = useState({ approved: [], rejected: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('approved');
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchData();
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const fetchData = async () => {
    try {
      const [statusResponse, suggestionsResponse] = await Promise.all([
        analyzerAPI.getStatus(),
        analyzerAPI.getSuggestions()
      ]);

      if (statusResponse.success) {
        setStatus(statusResponse.data);
      }

      if (suggestionsResponse.success) {
        setSuggestions(suggestionsResponse.data);
      }

      setError(null);
    } catch (err) {
      setError('Failed to fetch analyzer data');
      console.error('Error fetching analyzer data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartStop = async () => {
    try {
      if (status?.is_running) {
        await analyzerAPI.stop();
      } else {
        await analyzerAPI.start();
      }
      await fetchData();
    } catch (err) {
      setError('Failed to toggle analyzer');
      console.error('Error toggling analyzer:', err);
    }
  };

  const formatCurrency = (value) => {
    if (!value || value === 0) return '$0';
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  const formatPercent = (value) => {
    if (!value) return '0%';
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const formatTimeAgo = (isoString) => {
    if (!isoString) return 'Unknown';
    
    try {
      const date = new Date(isoString);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch {
      return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="suggestions-panel">
        <div className="loading">
          <div className="loading-spinner"></div>
          Loading analyzer...
        </div>
      </div>
    );
  }

  return (
    <div className="suggestions-panel">
      {/* Header */}
      <div className="panel-header">
        <div className="title-section">
          <h2 className="panel-title">🤖 AI Token Analyzer</h2>
          <div className="analyzer-status">
            <span className={`status-indicator ${status?.is_running ? 'running' : 'stopped'}`}>
              {status?.is_running ? '🟢 Running' : '🔴 Stopped'}
            </span>
            {status?.current_analysis && (
              <span className="current-analysis">
                📊 Analyzing...
              </span>
            )}
          </div>
        </div>
        
        <div className="header-controls">
          <button 
            className={`toggle-btn ${status?.is_running ? 'stop' : 'start'}`}
            onClick={handleStartStop}
          >
            {status?.is_running ? '⏹️ Stop' : '▶️ Start'}
          </button>
          <button 
            className={`auto-refresh-btn ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            title="Auto refresh every 30 seconds"
          >
            🔄
          </button>
        </div>
      </div>

      {/* Stats Summary */}
      {status && (
        <div className="stats-summary">
          <div className="stat-item">
            <span className="stat-label">Approved</span>
            <span className="stat-value approved">{status.approved_count}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Rejected</span>
            <span className="stat-value rejected">{status.rejected_count}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Max Market Cap</span>
            <span className="stat-value">{formatCurrency(status.criteria?.max_market_cap)}</span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
          <button onClick={fetchData} className="retry-btn">🔄 Retry</button>
        </div>
      )}

      {/* Tabs */}
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'approved' ? 'active' : ''}`}
          onClick={() => setActiveTab('approved')}
        >
          ✅ Approved ({suggestions.approved.length})
        </button>
        <button 
          className={`tab ${activeTab === 'rejected' ? 'active' : ''}`}
          onClick={() => setActiveTab('rejected')}
        >
          ❌ Rejected ({suggestions.rejected.length})
        </button>
      </div>

      {/* Content */}
      <div className="tab-content">
        {activeTab === 'approved' && (
          <div className="approved-tokens">
            {suggestions.approved.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <div className="empty-message">
                  {status?.is_running ? 'Analyzing tokens...' : 'No approved tokens yet. Start the analyzer to begin.'}
                </div>
              </div>
            ) : (
              suggestions.approved.map((token, index) => (
                <div key={token.token_address || index} className="token-card approved-card">
                  <div className="token-header">
                    <div className="token-info">
                      <div className="token-name">{token.symbol}</div>
                      <div className="token-address">{token.token_address?.slice(0, 8)}...</div>
                    </div>
                    <div className="opportunity-score">
                      <div className="score-value">{token.evaluation?.score?.toFixed(0) || 0}</div>
                      <div className="score-label">Score</div>
                    </div>
                  </div>

                  <div className="token-metrics">
                    <div className="metric">
                      <span className="metric-label">Market Cap</span>
                      <span className="metric-value">{formatCurrency(token.market_cap)}</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Liquidity</span>
                      <span className="metric-value">{formatCurrency(token.liquidity)}</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">Volume 24h</span>
                      <span className="metric-value">{formatCurrency(token.volume_24h)}</span>
                    </div>
                    <div className="metric">
                      <span className="metric-label">DextScore</span>
                      <span className="metric-value">{token.dext_score}/100</span>
                    </div>
                  </div>

                  <div className="price-info">
                    <div className="price-change">
                      <span className="label">1h:</span>
                      <span className={`change ${token.price_change_1h >= 0 ? 'positive' : 'negative'}`}>
                        {formatPercent(token.price_change_1h)}
                      </span>
                    </div>
                    <div className="price-change">
                      <span className="label">24h:</span>
                      <span className={`change ${token.price_change_24h >= 0 ? 'positive' : 'negative'}`}>
                        {formatPercent(token.price_change_24h)}
                      </span>
                    </div>
                  </div>

                  {token.evaluation?.warnings?.length > 0 && (
                    <div className="warnings">
                      <div className="warnings-title">⚠️ Warnings:</div>
                      {token.evaluation.warnings.map((warning, idx) => (
                        <div key={idx} className="warning-item">{warning}</div>
                      ))}
                    </div>
                  )}

                  <div className="analyzed-time">
                    📅 Analyzed {formatTimeAgo(token.analyzed_at)}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'rejected' && (
          <div className="rejected-tokens">
            {suggestions.rejected.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">✨</div>
                <div className="empty-message">No rejected tokens yet</div>
              </div>
            ) : (
              suggestions.rejected.map((token, index) => (
                <div key={token.token_address || index} className="token-card rejected-card">
                  <div className="token-header">
                    <div className="token-info">
                      <div className="token-name">{token.symbol}</div>
                      <div className="token-address">{token.token_address?.slice(0, 8)}...</div>
                    </div>
                    <div className="pool-rank">
                      Rank #{token.pool_rank}
                    </div>
                  </div>

                  <div className="rejection-reasons">
                    <div className="reasons-title">❌ Rejection Reasons:</div>
                    {token.rejection_reasons.map((reason, idx) => (
                      <div key={idx} className="reason-item">{reason}</div>
                    ))}
                  </div>

                  <div className="analyzed-time">
                    📅 Analyzed {formatTimeAgo(token.analyzed_at)}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TokenSuggestionsPanel;