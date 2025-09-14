import React from 'react';

const TokenDetailPanelSimple = ({ analysis, loading, error }) => {
  console.log('🪙 TokenDetailPanelSimple props:', { analysis: !!analysis, loading, error });

  if (loading) {
    return (
      <div className="token-detail-panel" style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '1.2rem', color: '#666' }}>
          ⏳ Analyzing token...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="token-detail-panel" style={{ padding: '2rem' }}>
        <div style={{ color: '#ff4757', background: '#ffe6e6', padding: '1rem', borderRadius: '8px' }}>
          <strong>Analysis Error:</strong> {error}
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="token-detail-panel" style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🪙</div>
        <p style={{ color: '#666', marginBottom: '1rem' }}>Select a token from the hot pools to see basic info</p>
        <div style={{ fontSize: '0.8rem', color: '#888' }}>
          Token analysis is available on demand to prevent timeouts
        </div>
      </div>
    );
  }

  if (!analysis.success || !analysis.data) {
    return (
      <div className="token-detail-panel" style={{ padding: '2rem' }}>
        <div style={{ color: '#ff4757', background: '#ffe6e6', padding: '1rem', borderRadius: '8px' }}>
          No token analysis data available
        </div>
      </div>
    );
  }

  const { data } = analysis;
  const info = data.info || {};
  const price = data.price || {};

  return (
    <div className="token-detail-panel" style={{ padding: '1rem' }}>
      {/* Header Simples */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '1rem', 
        marginBottom: '2rem',
        borderBottom: '1px solid #e0e0e0',
        paddingBottom: '1rem'
      }}>
        <div style={{ 
          width: '60px', 
          height: '60px', 
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
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', color: '#333' }}>
            {info.name || 'Unknown Token'}
          </h2>
          <div style={{ color: '#666', fontWeight: '600', fontSize: '1.1rem' }}>
            {info.symbol || 'N/A'}
          </div>
          <div style={{ 
            color: '#888', 
            fontSize: '0.8rem', 
            fontFamily: 'monospace',
            marginTop: '0.5rem'
          }}>
            📋 {analysis.tokenAddress ? 
              `${analysis.tokenAddress.slice(0, 6)}...${analysis.tokenAddress.slice(-6)}` 
              : 'N/A'
            }
          </div>
        </div>
      </div>

      {/* Preço e Mudanças */}
      {price.current && (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', 
          gap: '1rem',
          marginBottom: '2rem'
        }}>
          <div style={{ 
            background: 'white', 
            padding: '1rem', 
            borderRadius: '8px', 
            border: '1px solid #e0e0e0',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.5rem' }}>
              Current Price
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: '600', color: '#333' }}>
              ${parseFloat(price.current).toFixed(8)}
            </div>
          </div>

          {price.change24h !== undefined && (
            <div style={{ 
              background: 'white', 
              padding: '1rem', 
              borderRadius: '8px', 
              border: '1px solid #e0e0e0',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.5rem' }}>
                24h Change
              </div>
              <div style={{ 
                fontSize: '1.2rem', 
                fontWeight: '600', 
                color: parseFloat(price.change24h) >= 0 ? '#00ff88' : '#ff4757' 
              }}>
                {parseFloat(price.change24h) >= 0 ? '+' : ''}{parseFloat(price.change24h).toFixed(2)}%
              </div>
            </div>
          )}
        </div>
      )}

      {/* Status */}
      <div style={{ 
        background: '#f8f9fa', 
        padding: '1rem', 
        borderRadius: '8px',
        textAlign: 'center',
        color: '#666',
        fontSize: '0.9rem'
      }}>
        ✅ Token Analysis Loaded Successfully
      </div>
    </div>
  );
};

export default TokenDetailPanelSimple;