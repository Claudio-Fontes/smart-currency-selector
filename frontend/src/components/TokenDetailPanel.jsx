import React, { useState, useEffect } from 'react';

const TokenDetailPanel = ({ analysis, loading, error }) => {
  const [imageError, setImageError] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState('');
  
  // Reset image error when analysis changes
  useEffect(() => {
    setImageError(false);
  }, [analysis]);
  if (!analysis && !loading && !error) {
    return (
      <div className="token-detail-panel empty">
        <div>
          <div className="empty-icon">🪙</div>
          <p>Select a token from the hot pools to see detailed analysis</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="token-detail-panel">
        <div className="loading">
          <div className="loading-spinner"></div>
          Analyzing token...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="token-detail-panel">
        <div className="error">
          <strong>Analysis Error:</strong> {error}
        </div>
      </div>
    );
  }

  if (!analysis || !analysis.success) {
    return (
      <div className="token-detail-panel">
        <div className="error">
          No token analysis data available
        </div>
      </div>
    );
  }

  const { data } = analysis;
  if (!data) {
    return (
      <div className="token-detail-panel">
        <div className="error">
          Token data is not available
        </div>
      </div>
    );
  }

  const info = data.info || {};
  const price = data.price || {};
  const score = data.score || {};
  const metrics = data.metrics || {};
  const audit = data.audit || {};
  const taxAnalysis = data.tax_analysis || {};

  const formatPrice = (value) => {
    if (!value || isNaN(value)) return '$0.00';
    try {
      return `$${parseFloat(value).toFixed(8)}`;
    } catch {
      return '$0.00';
    }
  };

  const formatPercentage = (value) => {
    if (value === undefined || value === null || isNaN(value)) return '0.00%';
    try {
      const num = parseFloat(value);
      const sign = num > 0 ? '+' : '';
      return `${sign}${num.toFixed(2)}%`;
    } catch {
      return '0.00%';
    }
  };

  const getPercentageClass = (value) => {
    if (!value || isNaN(value)) return '';
    return parseFloat(value) > 0 ? 'positive' : 'negative';
  };

  const formatAddress = (address) => {
    if (!address || address.length < 12) return address || 'N/A';
    return `${address.slice(0, 6)}...${address.slice(-6)}`;
  };

  const copyToClipboard = async (text, label = 'Address') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyFeedback(`${label} copied!`);
      setTimeout(() => setCopyFeedback(''), 2000);
    } catch (err) {
      // Fallback for browsers that don't support clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopyFeedback(`${label} copied!`);
      setTimeout(() => setCopyFeedback(''), 2000);
    }
  };

  const getScoreLevel = (scoreValue) => {
    const numScore = parseInt(scoreValue) || 0;
    if (numScore >= 80) return 'high';
    if (numScore >= 50) return 'medium';
    return 'low';
  };

  const getScoreText = (scoreValue) => {
    const numScore = parseInt(scoreValue) || 0;
    if (numScore >= 80) return 'Excellent';
    if (numScore >= 60) return 'Good';
    if (numScore >= 40) return 'Fair';
    return 'Poor';
  };

  const formatLargeNumber = (value) => {
    if (!value || isNaN(value)) return '0';
    const num = parseFloat(value);
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(2)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(2);
  };

  const formatUSD = (value) => {
    if (!value || isNaN(value)) return '$0.00';
    const num = parseFloat(value);
    if (num >= 1000000) return `$${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `$${(num / 1000).toFixed(2)}K`;
    return `$${num.toFixed(2)}`;
  };

  const getTaxRiskLevel = (buyTax, sellTax) => {
    const buy = buyTax === null || buyTax === undefined ? 0 : parseFloat(buyTax);
    const sell = sellTax === null || sellTax === undefined ? 0 : parseFloat(sellTax);
    const totalTax = buy + sell;
    
    if (totalTax === 0) return 'excellent';
    if (totalTax <= 5) return 'good';
    if (totalTax <= 15) return 'moderate';
    if (totalTax <= 30) return 'high';
    return 'extreme';
  };

  const getTaxRiskText = (buyTax, sellTax) => {
    const buy = buyTax === null || buyTax === undefined ? 0 : parseFloat(buyTax);
    const sell = sellTax === null || sellTax === undefined ? 0 : parseFloat(sellTax);
    const totalTax = buy + sell;
    
    if (totalTax === 0) return 'No taxes - Excellent for trading';
    if (totalTax <= 5) return `Low taxes (${totalTax}%) - Good for trading`;
    if (totalTax <= 15) return `Moderate taxes (${totalTax}%) - Acceptable`;
    if (totalTax <= 30) return `High taxes (${totalTax}%) - Be careful`;
    return `Extreme taxes (${totalTax}%) - POTENTIAL SCAM`;
  };

  const getBooleanDisplay = (value) => {
    if (value === 'yes' || value === true) return '✅ Yes';
    if (value === 'no' || value === false) return '❌ No';
    if (value === 'warning') return '⚠️ Warning';
    return '❓ Unknown';
  };

  return (
    <div className="token-detail-panel">
      {/* Token Header */}
      <div className="token-header">
        <div className="token-logo">
          {info.logo && !imageError ? (
            <img 
              src={info.logo} 
              alt={info.symbol || 'Token'} 
              style={{ width: '100%', height: '100%', borderRadius: '50%' }} 
              onError={() => setImageError(true)}
            />
          ) : (
            <div style={{ 
              width: '100%', 
              height: '100%', 
              borderRadius: '50%', 
              backgroundColor: '#667eea',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.5rem',
              fontWeight: 'bold'
            }}>
              {(info.symbol || '?').charAt(0)}
            </div>
          )}
        </div>
        <div className="token-info">
          <div className="token-basic-info">
            <h2>{info.name || 'Unknown Token'}</h2>
            <div className="token-symbol">{info.symbol || 'N/A'}</div>
            <div 
              className="token-address clickable"
              onClick={() => copyToClipboard(analysis.tokenAddress, 'Token address')}
              title="Click to copy full address"
            >
              📋 {formatAddress(analysis.tokenAddress)}
            </div>
            {copyFeedback && (
              <div className="copy-feedback">
                ✅ {copyFeedback}
              </div>
            )}
          </div>
          
          {/* Social Links in Header */}
          {info.socialInfo && typeof info.socialInfo === 'object' && 
           Object.keys(info.socialInfo).some(key => info.socialInfo[key]) && (
            <div className="social-links-header">
              {info.socialInfo.website && (
                <a href={info.socialInfo.website} target="_blank" rel="noopener noreferrer" 
                   className="social-link">
                  🌐
                </a>
              )}
              {info.socialInfo.twitter && (
                <a href={info.socialInfo.twitter} target="_blank" rel="noopener noreferrer"
                   className="social-link">
                  🐦
                </a>
              )}
              {info.socialInfo.telegram && (
                <a href={info.socialInfo.telegram} target="_blank" rel="noopener noreferrer"
                   className="social-link">
                  💬
                </a>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Price Metrics */}
      {(price.current || price.change24h !== undefined) && (
        <div className="token-metrics">
          <div className="metric-card">
            <div className="metric-label">Current Price</div>
            <div className="metric-value">{formatPrice(price.current)}</div>
          </div>
          
          <div className="metric-card">
            <div className="metric-label">24h Change</div>
            <div className={`metric-value ${getPercentageClass(price.change24h)}`}>
              {formatPercentage(price.change24h)}
            </div>
          </div>
          
          {price.change1h !== undefined && (
            <div className="metric-card">
              <div className="metric-label">1h Change</div>
              <div className={`metric-value ${getPercentageClass(price.change1h)}`}>
                {formatPercentage(price.change1h)}
              </div>
            </div>
          )}
          
          {price.change6h !== undefined && (
            <div className="metric-card">
              <div className="metric-label">6h Change</div>
              <div className={`metric-value ${getPercentageClass(price.change6h)}`}>
                {formatPercentage(price.change6h)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trading Metrics */}
      {(metrics.liquidity_usd > 0 || metrics.volume_24h_usd > 0 || metrics.volume_1h_usd > 0 || metrics.mcap > 0) && (
        <div className="token-metrics">
          {metrics.liquidity_usd > 0 && (
            <div className="metric-card">
              <div className="metric-label">💧 Liquidity</div>
              <div className="metric-value">{formatUSD(metrics.liquidity_usd)}</div>
            </div>
          )}
          
          {metrics.volume_24h_usd > 0 && (
            <div className="metric-card">
              <div className="metric-label">📊 Volume 24h</div>
              <div className="metric-value">{formatUSD(metrics.volume_24h_usd)}</div>
            </div>
          )}
          
          {metrics.volume_1h_usd > 0 && (
            <div className="metric-card">
              <div className="metric-label">📈 Volume 1h</div>
              <div className="metric-value">{formatUSD(metrics.volume_1h_usd)}</div>
            </div>
          )}
          
          {metrics.mcap > 0 && (
            <div className="metric-card">
              <div className="metric-label">🏆 Market Cap</div>
              <div className="metric-value">{formatUSD(metrics.mcap)}</div>
            </div>
          )}
          
          {metrics.fdv > 0 && metrics.fdv !== metrics.mcap && (
            <div className="metric-card">
              <div className="metric-label">💎 FDV</div>
              <div className="metric-value">{formatUSD(metrics.fdv)}</div>
            </div>
          )}
        </div>
      )}

      {/* Supply & Holders */}
      {(metrics.circulating_supply || metrics.holders_count || metrics.transactions) && (
        <div className="token-metrics">
          {metrics.circulating_supply > 0 && (
            <div className="metric-card">
              <div className="metric-label">🔄 Circulating Supply</div>
              <div className="metric-value">{formatLargeNumber(metrics.circulating_supply)}</div>
            </div>
          )}
          
          {metrics.total_supply > 0 && metrics.total_supply !== metrics.circulating_supply && (
            <div className="metric-card">
              <div className="metric-label">📦 Total Supply</div>
              <div className="metric-value">{formatLargeNumber(metrics.total_supply)}</div>
            </div>
          )}
          
          {metrics.holders_count > 0 && (
            <div className="metric-card">
              <div className="metric-label">👥 Holders</div>
              <div className="metric-value">{formatLargeNumber(metrics.holders_count)}</div>
            </div>
          )}
          
          {metrics.transactions > 0 && (
            <div className="metric-card">
              <div className="metric-label">🔄 Transactions</div>
              <div className="metric-value">{formatLargeNumber(metrics.transactions)}</div>
            </div>
          )}
        </div>
      )}

      {/* Pool & DEX Info */}
      {(metrics.pool_address || metrics.dex_info?.name) && (
        <div className="metric-card" style={{ marginBottom: '2rem' }}>
          <div className="metric-label">🏊 Pool Information</div>
          <div style={{ marginTop: '0.5rem' }}>
            {metrics.dex_info?.name && (
              <div style={{ fontSize: '0.9rem', color: '#555', marginBottom: '0.5rem' }}>
                <strong>DEX:</strong> {metrics.dex_info.name}
              </div>
            )}
            {metrics.pool_address && (
              <div style={{ fontSize: '0.8rem', color: '#666', fontFamily: 'monospace' }}>
                <strong>Pool:</strong> {formatAddress(metrics.pool_address)}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Security Score */}
      {score.total !== undefined && score.total !== null && !isNaN(score.total) && (
        <div className="metric-card" style={{ marginBottom: '2rem' }}>
          <div className="metric-label">Security Score</div>
          <div className="score-indicator">
            <div className="score-bar">
              <div 
                className={`score-fill ${getScoreLevel(score.total)}`}
                style={{ width: `${Math.max(0, Math.min(100, score.total))}%` }}
              ></div>
            </div>
            <div className="metric-value">
              {score.total}/100 ({getScoreText(score.total)})
            </div>
          </div>
          {(score.upvotes > 0 || score.downvotes > 0) && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#666' }}>
              👍 {score.upvotes || 0} upvotes • 👎 {score.downvotes || 0} downvotes
            </div>
          )}
        </div>
      )}

      {/* Tax Analysis */}
      {(taxAnalysis.buy_tax_info || taxAnalysis.sell_tax_info || audit.buy_tax || audit.sell_tax) && (
        <div className="metric-card" style={{ marginBottom: '2rem' }}>
          <div className="metric-label">💰 Tax Analysis</div>
          <div className="tax-analysis">
            {/* Tax Info */}
            <div className="token-metrics" style={{ marginTop: '0.5rem' }}>
              {(taxAnalysis.buy_tax_info || audit.buy_tax) && (
                <div className="metric-card">
                  <div className="metric-label">📈 Buy Tax</div>
                  <div className="metric-value">
                    {(() => {
                      const buyTax = taxAnalysis.buy_tax_info?.max_percent ?? audit.buy_tax?.max;
                      return buyTax !== null && buyTax !== undefined ? `${buyTax}%` : '0%';
                    })()}
                  </div>
                </div>
              )}
              
              {(taxAnalysis.sell_tax_info || audit.sell_tax) && (
                <div className="metric-card">
                  <div className="metric-label">📉 Sell Tax</div>
                  <div className="metric-value">
                    {(() => {
                      const sellTax = taxAnalysis.sell_tax_info?.max_percent ?? audit.sell_tax?.max;
                      return sellTax !== null && sellTax !== undefined ? `${sellTax}%` : '0%';
                    })()}
                  </div>
                </div>
              )}
            </div>
            
            {/* Tax Risk Assessment */}
            {(taxAnalysis.overall_assessment || audit.buy_tax || audit.sell_tax) && (
              <div style={{ marginTop: '1rem' }}>
                <div className={`tax-risk-indicator ${getTaxRiskLevel(
                  taxAnalysis.buy_tax_info?.max_percent ?? audit.buy_tax?.max,
                  taxAnalysis.sell_tax_info?.max_percent ?? audit.sell_tax?.max
                )}`}>
                  <div className="tax-risk-text">
                    {taxAnalysis.overall_assessment || getTaxRiskText(
                      taxAnalysis.buy_tax_info?.max_percent ?? audit.buy_tax?.max,
                      taxAnalysis.sell_tax_info?.max_percent ?? audit.sell_tax?.max
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Security Audit */}
      {(audit.is_honeypot !== undefined || audit.is_contract_renounced !== undefined || 
        audit.is_open_source !== undefined || audit.slippage_modifiable !== undefined) && (
        <div className="metric-card" style={{ marginBottom: '2rem' }}>
          <div className="metric-label">🔍 Security Audit</div>
          <div className="audit-info">
            {audit.is_honeypot !== undefined && (
              <div className="audit-item">
                <span className="audit-label">🍯 Honeypot:</span>
                <span className="audit-value">{getBooleanDisplay(audit.is_honeypot)}</span>
              </div>
            )}
            
            {audit.is_open_source !== undefined && (
              <div className="audit-item">
                <span className="audit-label">🔍 Open Source:</span>
                <span className="audit-value">{getBooleanDisplay(audit.is_open_source)}</span>
              </div>
            )}
            
            {audit.is_contract_renounced !== undefined && (
              <div className="audit-item">
                <span className="audit-label">🔐 Contract Renounced:</span>
                <span className="audit-value">{getBooleanDisplay(audit.is_contract_renounced)}</span>
              </div>
            )}
            
            {audit.slippage_modifiable !== undefined && (
              <div className="audit-item">
                <span className="audit-label">📊 Slippage Modifiable:</span>
                <span className="audit-value">{getBooleanDisplay(audit.slippage_modifiable)}</span>
              </div>
            )}
            
            {audit.is_mintable !== undefined && (
              <div className="audit-item">
                <span className="audit-label">🏭 Mintable:</span>
                <span className="audit-value">{getBooleanDisplay(audit.is_mintable)}</span>
              </div>
            )}
            
            {audit.is_blacklisted !== undefined && (
              <div className="audit-item">
                <span className="audit-label">🚫 Has Blacklist:</span>
                <span className="audit-value">{getBooleanDisplay(audit.is_blacklisted)}</span>
              </div>
            )}
            
            {audit.updated_at && (
              <div className="audit-item">
                <span className="audit-label">🕒 Last Updated:</span>
                <span className="audit-value" style={{ fontSize: '0.8rem' }}>
                  {new Date(audit.updated_at).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Token Info */}
      {info.description && (
        <div className="metric-card" style={{ marginBottom: '2rem' }}>
          <div className="metric-label">Description</div>
          <div style={{ fontSize: '0.9rem', lineHeight: '1.5', color: '#555' }}>
            {info.description}
          </div>
        </div>
      )}

      {/* Token Details */}
      <div className="token-metrics">
        {info.decimals && (
          <div className="metric-card">
            <div className="metric-label">Decimals</div>
            <div className="metric-value">{info.decimals}</div>
          </div>
        )}
        
        {info.createdAt && (
          <div className="metric-card">
            <div className="metric-label">Created</div>
            <div className="metric-value" style={{ fontSize: '0.9rem' }}>
              {new Date(info.createdAt).toLocaleDateString()}
            </div>
          </div>
        )}
      </div>

    </div>
  );
};

export default TokenDetailPanel;