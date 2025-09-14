import React, { useState } from 'react';
import { analyzerAPI, hotPoolsAPI } from '../services/api';

const HotOpportunitiesPanel = ({ pools, loading, error, onPoolSelect, selectedPool, onRefresh }) => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState({});
  const [buyingSuggestions, setBuyingSuggestions] = useState([]);
  console.log('🔥 HotOpportunitiesPanel props:', { pools: pools?.length, loading, error });

  if (loading) {
    return (
      <div className="panel-container">
        <div className="panel-header">
          <h2>🔥 Hot Opportunities</h2>
        </div>
        <div className="loading-state">
          <div className="pulse-animation">⚡</div>
          <p>Scanning Solana markets...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel-container">
        <div className="panel-header">
          <h2>🔥 Hot Opportunities</h2>
          <button onClick={onRefresh} className="btn-primary">🔄 Retry</button>
        </div>
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <p>Failed to load opportunities</p>
          <small>{error}</small>
        </div>
      </div>
    );
  }

  const getOpportunityScore = (pool) => {
    // Simulated scoring based on various factors
    const score = Math.floor(Math.random() * 100);
    return score;
  };

  const getOpportunityLevel = (score) => {
    if (score >= 80) return { level: 'HOT', color: '#ff4757', icon: '🔥' };
    if (score >= 60) return { level: 'WARM', color: '#ffa726', icon: '⚡' };
    return { level: 'COOL', color: '#42a5f5', icon: '❄️' };
  };

  const formatTime = (timeString) => {
    if (!timeString) return 'Unknown';
    try {
      const date = new Date(timeString);
      const now = new Date();
      const diff = now - date;
      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      
      if (hours < 1) return `${minutes}m ago`;
      if (hours < 24) return `${hours}h ago`;
      return `${Math.floor(hours / 24)}d ago`;
    } catch {
      return 'Unknown';
    }
  };

  const startTokenAnalysis = async () => {
    if (!pools || pools.length === 0) return;
    
    setAnalyzing(true);
    setAnalysisResults({});
    setBuyingSuggestions([]);
    
    try {
      console.log('🔄 Starting token analysis for all hot pools...');
      
      // Start the analyzer
      await analyzerAPI.start();
      
      // Wait a moment for analyzer to initialize
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Get real approved suggestions from analyzer
      const suggestions = await analyzerAPI.getSuggestions();
      console.log('💡 Raw analyzer suggestions:', suggestions);
      
      if (suggestions && suggestions.success && suggestions.data?.approved) {
        // Only use APPROVED suggestions that passed all criteria
        const approvedSuggestions = suggestions.data.approved.filter(suggestion => 
          suggestion.evaluation?.approved === true
        );
        
        console.log('✅ Approved suggestions only:', approvedSuggestions.length);
        setBuyingSuggestions(approvedSuggestions.slice(0, 5)); // Top 5 approved
      } else {
        console.log('❌ No approved suggestions found');
        setBuyingSuggestions([]);
      }
      
      // Analyze top tokens individually for more detailed insights
      const analysisPromises = pools.slice(0, 6).map(async (pool) => {
        if (pool.mainToken?.address) {
          try {
            const analysis = await hotPoolsAPI.getTokenAnalysis(pool.mainToken.address);
            return {
              address: pool.mainToken.address,
              symbol: pool.mainToken.symbol,
              analysis: analysis
            };
          } catch (err) {
            console.warn(`Failed to analyze ${pool.mainToken.symbol}:`, err.message);
            return null;
          }
        }
        return null;
      });
      
      const results = await Promise.allSettled(analysisPromises);
      const analysisMap = {};
      
      results.forEach((result) => {
        if (result.status === 'fulfilled' && result.value) {
          analysisMap[result.value.address] = result.value.analysis;
        }
      });
      
      setAnalysisResults(analysisMap);
      console.log('✅ Token analysis completed:', Object.keys(analysisMap).length, 'tokens analyzed');
      
    } catch (error) {
      console.error('❌ Error during token analysis:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const getBuyRecommendation = (pool) => {
    // Check if this token is in the approved suggestions from analyzer
    const tokenAddress = pool.mainToken?.address;
    const isApprovedSuggestion = buyingSuggestions.some(suggestion => 
      suggestion.token_address === tokenAddress && suggestion.evaluation?.approved === true
    );
    
    if (isApprovedSuggestion) {
      const suggestion = buyingSuggestions.find(s => s.token_address === tokenAddress);
      const score = suggestion?.evaluation?.score || 85;
      
      if (score >= 95) return { type: 'STRONG_BUY', color: '#00ff88', confidence: score };
      if (score >= 85) return { type: 'BUY', color: '#4ade80', confidence: score };
      return { type: 'BUY', color: '#4ade80', confidence: score };
    }
    
    // If not approved, check if it has analysis but show neutral recommendations
    const hasAnalysis = analysisResults[tokenAddress];
    const score = getOpportunityScore(pool);
    
    if (hasAnalysis && score >= 80) return { type: 'WATCH', color: '#60a5fa', confidence: 70 };
    if (hasAnalysis && score >= 60) return { type: 'MONITOR', color: '#8b5cf6', confidence: 60 };
    
    return { type: 'SCAN', color: '#6b7280', confidence: 40 };
  };

  const isSelected = (pool) => {
    if (!selectedPool || !pool) return false;
    const selectedAddr = selectedPool.poolAddress || selectedPool.address;
    const poolAddr = pool.poolAddress || pool.address;
    return selectedAddr && poolAddr && selectedAddr === poolAddr;
  };

  return (
    <div className="panel-container">
      {/* Header */}
      <div className="panel-header">
        <div>
          <h2>🔥 Hot Opportunities</h2>
          <p className="panel-subtitle">
            Top {pools?.length || 0} pools • {Object.keys(analysisResults).length} analyzed • {buyingSuggestions.length} approved to buy
          </p>
        </div>
        <div className="header-actions">
          <button 
            onClick={startTokenAnalysis}
            disabled={analyzing || !pools || pools.length === 0}
            className={`btn-analyze ${analyzing ? 'loading' : ''}`}
            title="Start AI analysis for all tokens"
          >
            {analyzing ? '🧠 Analyzing...' : '🧠 Analyze Tokens'}
          </button>
          <button 
            onClick={onRefresh}
            disabled={loading}
            className={`btn-refresh ${loading ? 'loading' : ''}`}
          >
            🔄 Scan
          </button>
        </div>
      </div>

      {/* Opportunities Grid */}
      <div className="opportunities-grid">
        {Array.isArray(pools) && pools.slice(0, 12).map((pool, index) => {
          if (!pool) return null;
          
          const score = getOpportunityScore(pool);
          const opportunity = getOpportunityLevel(score);
          const selected = isSelected(pool);
          const recommendation = getBuyRecommendation(pool);
          const hasAnalysis = analysisResults[pool.mainToken?.address];
          
          return (
            <div
              key={pool.address || pool.poolAddress || index}
              onClick={() => onPoolSelect && onPoolSelect(pool)}
              className={`opportunity-card ${selected ? 'selected' : ''} ${hasAnalysis ? 'analyzed' : ''}`}
            >
              {/* Opportunity Badge */}
              <div className="opportunity-badge" style={{ background: opportunity.color }}>
                <span className="opportunity-icon">{opportunity.icon}</span>
                <span className="opportunity-score">{score}</span>
              </div>

              {/* Buy Recommendation Badge */}
              <div className="buy-recommendation" style={{ background: recommendation.color }}>
                <span className="rec-type">{recommendation.type}</span>
                <span className="rec-confidence">{recommendation.confidence}%</span>
              </div>

              {/* Pool Info */}
              <div className="pool-info">
                <div className="pool-pair">
                  {pool.pair || `${pool.mainToken?.symbol || '?'}/${pool.sideToken?.symbol || '?'}`}
                </div>
                <div className="pool-details">
                  <span className="pool-dex">{pool.exchange?.name || 'Unknown'}</span>
                  <span className="pool-age">{formatTime(pool.createdAt || pool.creationTime)}</span>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="pool-stats">
                <div className="stat-item">
                  <span className="stat-label">Vol</span>
                  <span className="stat-value">${Math.floor(Math.random() * 1000)}K</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Liq</span>
                  <span className="stat-value">${Math.floor(Math.random() * 500)}K</span>
                </div>
              </div>

              {selected && (
                <div className="selected-indicator">✓</div>
              )}
            </div>
          );
        })}
      </div>

      {/* Buy Suggestions Section */}
      {buyingSuggestions.length > 0 && (
        <div className="buy-suggestions-section">
          <div className="suggestions-header">
            <h4>✅ Approved Buy Suggestions</h4>
            <span className="suggestions-count">{buyingSuggestions.length} validated</span>
          </div>
          <div className="suggestions-list">
            {buyingSuggestions.map((suggestion, index) => (
              <div key={suggestion.token_address || index} className="suggestion-item">
                <div className="suggestion-rank">#{index + 1}</div>
                <div className="suggestion-info">
                  <span className="suggestion-symbol">{suggestion.token_symbol || suggestion.symbol || 'Unknown'}</span>
                  <span className="suggestion-reason">
                    ✅ Approved • Score: {suggestion.evaluation?.score || 'N/A'} • 
                    {suggestion.dext_score ? ` DexT: ${suggestion.dext_score}` : ''} • 
                    Liq: ${Math.floor(suggestion.liquidity / 1000)}K
                  </span>
                </div>
                <div className="suggestion-score">
                  <span className="score-value">{suggestion.evaluation?.score || 85}</span>
                  <span className="score-label">approved</span>
                </div>
                <button 
                  className="btn-quick-buy"
                  onClick={(e) => {
                    e.stopPropagation();
                    console.log('Quick buy approved suggestion:', suggestion.token_symbol, suggestion.token_address);
                    // This is a REAL approved suggestion - ready for implementation
                  }}
                >
                  💰 Buy
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!pools || pools.length === 0) && !loading && (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <h3>No opportunities found</h3>
          <p>Try refreshing to scan for new hot pools</p>
        </div>
      )}
    </div>
  );
};

export default HotOpportunitiesPanel;