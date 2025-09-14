import React, { useState, useEffect } from 'react';
import { marketIntelligenceAPI } from '../services/api';

const MarketIntelligencePanel = ({ selectedPool }) => {
  const [marketData, setMarketData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [dataProgress, setDataProgress] = useState({
    basic: false,
    enhanced: false,
    metrics: false
  });

  // Progressive loading - start with fast data, then enhance in background
  const fetchMarketDataProgressive = async (tokenAddress) => {
    try {
      setLoading(true);
      setError(null);
      setLoadingStage('Loading basic data...');
      setDataProgress({ basic: false, enhanced: false, metrics: false });
      
      console.log('🚀 Starting progressive loading for:', tokenAddress);
      
      // Stage 1: Get fast basic data first (should load in 2-5 seconds)
      try {
        const fastResponse = await marketIntelligenceAPI.getMarketIntelligenceFast(tokenAddress);
        if (fastResponse.success && fastResponse.data) {
          console.log('⚡ Fast data loaded successfully');
          setMarketData(fastResponse.data);
          setDataProgress(prev => ({ ...prev, basic: true }));
          setLastUpdate(new Date());
          setLoadingStage('Enhancing data...');
        }
      } catch (fastError) {
        console.error('❌ Fast loading failed:', fastError);
        throw new Error('Unable to load basic market data');
      }
      
      // Stage 2 & 3: Load enhanced data and metrics in background (parallel)
      Promise.allSettled([
        // Enhanced data (social info, security score, etc)
        marketIntelligenceAPI.getMarketIntelligenceEnhanced(tokenAddress).then(enhancedResponse => {
          if (enhancedResponse.success && enhancedResponse.data) {
            console.log('🎯 Enhanced data loaded');
            setMarketData(prevData => ({
              ...prevData,
              marketCap: enhancedResponse.data.marketCap || prevData.marketCap,
              holders: enhancedResponse.data.holders || prevData.holders,
              fdv: enhancedResponse.data.fdv || prevData.fdv,
              socialInfo: enhancedResponse.data.socialInfo || prevData.socialInfo,
              security: enhancedResponse.data.security || prevData.security
            }));
            setDataProgress(prev => ({ ...prev, enhanced: true }));
          }
        }).catch(err => console.log('⚠️ Enhanced data failed:', err.message)),
        
        // Metrics data (volume, liquidity, etc)
        marketIntelligenceAPI.getMarketIntelligenceMetrics(tokenAddress).then(metricsResponse => {
          if (metricsResponse.success && metricsResponse.data) {
            console.log('📈 Metrics data loaded');
            setMarketData(prevData => ({
              ...prevData,
              volume24h: metricsResponse.data.volume24h || prevData.volume24h,
              liquidity: metricsResponse.data.liquidity || prevData.liquidity,
              poolInfo: metricsResponse.data.poolInfo || prevData.poolInfo,
              trends: { ...prevData.trends, ...metricsResponse.data.trends }
            }));
            setDataProgress(prev => ({ ...prev, metrics: true }));
          }
        }).catch(err => console.log('⚠️ Metrics data failed:', err.message))
      ]).finally(() => {
        setLoadingStage('');
        console.log('✅ Progressive loading completed');
      });
      
    } catch (err) {
      console.error('❌ Progressive loading failed:', err);
      setError(err.message);
      setMarketData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPool?.mainToken?.address) {
      fetchMarketDataProgressive(selectedPool.mainToken.address);
      
      // Auto-refresh every 45 seconds (longer due to progressive loading)
      const interval = setInterval(() => {
        fetchMarketDataProgressive(selectedPool.mainToken.address);
      }, 45000);
      
      return () => clearInterval(interval);
    } else {
      setMarketData(null);
      setError(null);
      setDataProgress({ basic: false, enhanced: false, metrics: false });
    }
  }, [selectedPool]);

  const formatNumber = (num, type = 'default') => {
    if (!num) return '0';
    
    switch (type) {
      case 'currency':
        if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `$${(num / 1000).toFixed(1)}K`;
        return `$${num.toLocaleString()}`;
      case 'percentage':
        return `${num >= 0 ? '+' : ''}${num}%`;
      default:
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toLocaleString();
    }
  };

  const MiniChart = ({ data, color }) => (
    <div className="mini-chart">
      <svg width="100" height="40" className="chart-svg">
        {data.map((point, i) => {
          const x = (i / (data.length - 1)) * 95 + 2.5;
          const y = 35 - (point.price / Math.max(...data.map(p => p.price))) * 30;
          return i > 0 ? (
            <line
              key={i}
              x1={(i - 1) / (data.length - 1) * 95 + 2.5}
              y1={35 - (data[i - 1].price / Math.max(...data.map(p => p.price))) * 30}
              x2={x}
              y2={y}
              stroke={color}
              strokeWidth="2"
            />
          ) : null;
        })}
      </svg>
    </div>
  );

  const VolumeChart = ({ data }) => (
    <div className="volume-chart">
      {data.map((bar, i) => (
        <div
          key={i}
          className="volume-bar"
          style={{
            height: `${(bar.volume / Math.max(...data.map(d => d.volume))) * 100}%`
          }}
        />
      ))}
    </div>
  );

  if (!selectedPool) {
    return (
      <div className="panel-container">
        <div className="panel-header">
          <h2>📊 Market Intelligence</h2>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🎯</div>
          <h3>Select a Pool</h3>
          <p>Choose a pool from Hot Opportunities to see real-time market analysis</p>
        </div>
      </div>
    );
  }

  if (loading && !marketData) {
    return (
      <div className="panel-container">
        <div className="panel-header">
          <h2>📊 Market Intelligence</h2>
          <p className="panel-subtitle">
            {selectedPool.pair || `${selectedPool.mainToken?.symbol}/${selectedPool.sideToken?.symbol}`}
          </p>
        </div>
        <div className="loading-state">
          <div className="pulse-animation">📊</div>
          <p>Loading market intelligence...</p>
        </div>
      </div>
    );
  }

  if (error && !marketData) {
    return (
      <div className="panel-container">
        <div className="panel-header">
          <h2>📊 Market Intelligence</h2>
          <p className="panel-subtitle">
            {selectedPool.pair || `${selectedPool.mainToken?.symbol}/${selectedPool.sideToken?.symbol}`}
          </p>
        </div>
        <div className="error-state">
          <div className="error-icon">⚠️</div>
          <p>Failed to load market data</p>
          <small>{error}</small>
          <button onClick={() => fetchMarketDataProgressive(selectedPool.mainToken.address)} className="btn-retry">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  const priceColor = marketData?.priceChange24h >= 0 ? '#00ff88' : '#ff4757';
  const formatTime = (date) => {
    if (!date) return 'Never';
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ago`;
  };

  return (
    <div className="panel-container">
      {/* Header */}
      <div className="panel-header">
        <div>
          <h2>📊 Market Intelligence</h2>
          <p className="panel-subtitle">
            {selectedPool.pair || `${selectedPool.mainToken?.symbol}/${selectedPool.sideToken?.symbol}`}
          </p>
        </div>
        <div className="market-status">
          <div className={`status-indicator ${loading ? 'loading' : 'active'}`}></div>
          <div className="status-info">
            <span>{loading ? (loadingStage || 'Loading...') : 'Live'}</span>
            {lastUpdate && (
              <span className="last-update">Updated {formatTime(lastUpdate)}</span>
            )}
            {/* Data progress indicators */}
            <div className="data-progress">
              <span className={`progress-dot ${dataProgress.basic ? 'loaded' : ''}`} title="Basic data">●</span>
              <span className={`progress-dot ${dataProgress.enhanced ? 'loaded' : ''}`} title="Enhanced data">●</span>
              <span className={`progress-dot ${dataProgress.metrics ? 'loaded' : ''}`} title="Metrics data">●</span>
            </div>
          </div>
          <button 
            onClick={() => fetchMarketDataProgressive(selectedPool.mainToken.address)} 
            disabled={loading}
            className="btn-refresh-mini"
            title="Refresh data"
          >
            🔄
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-btn ${activeTab === 'analysis' ? 'active' : ''}`}
          onClick={() => setActiveTab('analysis')}
        >
          Analysis
        </button>
        <button 
          className={`tab-btn ${activeTab === 'signals' ? 'active' : ''}`}
          onClick={() => setActiveTab('signals')}
        >
          Signals
        </button>
      </div>

      {/* Content */}
      <div className="tab-content">
        {activeTab === 'overview' && marketData && (
          <div className="overview-content">
            {/* Price Section */}
            <div className="price-section">
              <div className="current-price">
                <span className="price-value">${marketData.price?.toFixed(8) || '0.00000000'}</span>
                <span className="price-change" style={{ color: priceColor }}>
                  {formatNumber(marketData.priceChange24h, 'percentage')}
                </span>
              </div>
              <MiniChart data={marketData.priceHistory || []} color={priceColor} />
            </div>

            {/* Key Metrics */}
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-label">Volume 24h</div>
                <div className="metric-value">{formatNumber(marketData.volume24h || 0, 'currency')}</div>
                <div className={`metric-trend ${marketData.trends?.volume === 'positive' ? 'positive' : 'neutral'}`}>
                  {marketData.trends?.volume === 'positive' ? '📈' : '📊'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Market Cap</div>
                <div className="metric-value">{formatNumber(marketData.marketCap || 0, 'currency')}</div>
                <div className="metric-trend neutral">💎</div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Liquidity</div>
                <div className="metric-value">{formatNumber(marketData.liquidity || 0, 'currency')}</div>
                <div className={`metric-trend ${marketData.trends?.liquidity === 'positive' ? 'positive' : 'neutral'}`}>
                  {marketData.trends?.liquidity === 'positive' ? '💧' : '🏊'}
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-label">Holders</div>
                <div className="metric-value">{formatNumber(marketData.holders || 0)}</div>
                <div className={`metric-trend ${marketData.trends?.holders === 'positive' ? 'positive' : 'neutral'}`}>
                  {marketData.trends?.holders === 'positive' ? '👥' : '👤'}
                </div>
              </div>
            </div>

            {/* Volume Chart */}
            <div className="chart-section">
              <h4>7-Day Volume Trend</h4>
              <VolumeChart data={marketData.volumeHistory || []} />
            </div>
            
            {/* Social Metrics */}
            {marketData.socialInfo && (
              <div className="social-section">
                <h4>🌐 Social Presence</h4>
                <div className="social-links">
                  {marketData.socialInfo.hasWebsite && (
                    <a href={marketData.socialInfo.website} target="_blank" rel="noopener noreferrer" className="social-link">
                      🌐 Website
                    </a>
                  )}
                  {marketData.socialInfo.hasTwitter && (
                    <a href={marketData.socialInfo.twitter} target="_blank" rel="noopener noreferrer" className="social-link">
                      🐦 Twitter
                    </a>
                  )}
                  {marketData.socialInfo.hasTelegram && (
                    <a href={marketData.socialInfo.telegram} target="_blank" rel="noopener noreferrer" className="social-link">
                      📱 Telegram
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analysis' && marketData && (
          <div className="analysis-content">
            <div className="analysis-card">
              <div className="analysis-header">
                <span className="analysis-icon">🔍</span>
                <h4>Technical Analysis</h4>
              </div>
              <div className="analysis-item">
                <span className="indicator">RSI (14)</span>
                <span className="indicator-value">{marketData.technicalAnalysis?.rsi?.value || 'N/A'}</span>
                <span className={`indicator-status ${marketData.technicalAnalysis?.rsi?.status || 'neutral'}`}>
                  {marketData.technicalAnalysis?.rsi?.status || 'Neutral'}
                </span>
              </div>
              <div className="analysis-item">
                <span className="indicator">MACD</span>
                <span className="indicator-value">
                  {marketData.technicalAnalysis?.macd?.value > 0 ? '+' : ''}{marketData.technicalAnalysis?.macd?.value || 'N/A'}
                </span>
                <span className={`indicator-status ${marketData.technicalAnalysis?.macd?.status || 'neutral'}`}>
                  {marketData.technicalAnalysis?.macd?.status || 'Neutral'}
                </span>
              </div>
              <div className="analysis-item">
                <span className="indicator">Volume Profile</span>
                <span className="indicator-value">{marketData.technicalAnalysis?.volumeProfile?.level || 'N/A'}</span>
                <span className={`indicator-status ${marketData.technicalAnalysis?.volumeProfile?.status || 'neutral'}`}>
                  {marketData.technicalAnalysis?.volumeProfile?.status || 'Neutral'}
                </span>
              </div>
            </div>

            <div className="analysis-card">
              <div className="analysis-header">
                <span className="analysis-icon">📈</span>
                <h4>Price Levels</h4>
              </div>
              <div className="analysis-item">
                <span className="indicator">Resistance</span>
                <span className="indicator-value">${marketData.priceLevels?.resistance?.toFixed(8) || 'N/A'}</span>
                <span className="indicator-status">
                  {marketData.priceLevels?.resistanceDistance ? 
                    `${marketData.priceLevels.resistanceDistance > 0 ? '+' : ''}${marketData.priceLevels.resistanceDistance.toFixed(1)}%` 
                    : 'N/A'}
                </span>
              </div>
              <div className="analysis-item">
                <span className="indicator">Support</span>
                <span className="indicator-value">${marketData.priceLevels?.support?.toFixed(8) || 'N/A'}</span>
                <span className="indicator-status">
                  {marketData.priceLevels?.supportDistance ? 
                    `${marketData.priceLevels.supportDistance.toFixed(1)}%` 
                    : 'N/A'}
                </span>
              </div>
            </div>
            
            {/* Security Score */}
            {marketData.security && (
              <div className="analysis-card">
                <div className="analysis-header">
                  <span className="analysis-icon">🛡️</span>
                  <h4>Security Analysis</h4>
                </div>
                <div className="analysis-item">
                  <span className="indicator">DexTools Score</span>
                  <span className="indicator-value">{marketData.security.score || 'N/A'}</span>
                  <span className={`indicator-status ${marketData.security.level?.toLowerCase() || 'neutral'}`}>
                    {marketData.security.level || 'Unknown'}
                  </span>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'signals' && marketData && (
          <div className="signals-content">
            {marketData.signals && marketData.signals.length > 0 ? (
              marketData.signals.map((signal, index) => (
                <div key={index} className={`signal-card ${signal.strength || 'info'}`}>
                  <div className="signal-header">
                    <span className="signal-icon">{signal.icon}</span>
                    <span className="signal-type">{signal.type}</span>
                    <span className="signal-time">{signal.time}</span>
                  </div>
                  <p>{signal.message}</p>
                </div>
              ))
            ) : (
              <div className="no-signals">
                <div className="signal-card info">
                  <div className="signal-header">
                    <span className="signal-icon">💡</span>
                    <span className="signal-type">INFO</span>
                    <span className="signal-time">Now</span>
                  </div>
                  <p>Market monitoring active. No significant signals detected at this time.</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketIntelligencePanel;