import React from 'react';

const HotPoolsPanelSimple = ({ pools, loading, error, onPoolSelect, selectedPool, onRefresh }) => {
  console.log('🔥 HotPoolsPanelSimple props:', { pools: pools?.length, loading, error });

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        <div style={{ fontSize: '1.2rem', color: '#666', marginBottom: '1rem' }}>
          ⏳ Loading hot pools...
        </div>
        <div style={{ fontSize: '0.9rem', color: '#888' }}>
          Getting latest Solana pool data
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={{ 
          color: '#ff4757', 
          background: '#ffe6e6', 
          padding: '1rem', 
          borderRadius: '8px',
          marginBottom: '1rem'
        }}>
          <strong>Error:</strong> {error}
        </div>
        <button 
          onClick={onRefresh}
          style={{
            background: '#667eea',
            color: 'white',
            border: 'none',
            padding: '0.5rem 1rem',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          🔄 Try Again
        </button>
      </div>
    );
  }

  const handlePoolClick = (pool) => {
    console.log('🖱️ Pool clicked:', pool.mainToken?.symbol);
    if (onPoolSelect) {
      onPoolSelect(pool);
    }
  };

  const isSelected = (pool) => {
    if (!selectedPool || !pool) return false;
    const selectedAddr = selectedPool.poolAddress || selectedPool.address;
    const poolAddr = pool.poolAddress || pool.address;
    return selectedAddr && poolAddr && selectedAddr === poolAddr;
  };

  const formatAddress = (address) => {
    if (!address || address.length < 8) return address || 'N/A';
    return `${address.slice(0, 4)}...${address.slice(-4)}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('pt-BR');
    } catch {
      return 'N/A';
    }
  };

  return (
    <div style={{ padding: '1rem', height: '100%' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '0rem',
        paddingBottom: '0.25rem',
        borderBottom: '1px solid #e0e0e0'
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.3rem', color: '#333' }}>
            🔥 Hot Pools
          </h2>
          <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
            Top {pools?.length || 0} Solana pools
          </div>
        </div>
        <button 
          onClick={onRefresh}
          disabled={loading}
          style={{
            background: loading ? '#ccc' : '#667eea',
            color: 'white',
            border: 'none',
            padding: '0.4rem 0.8rem',
            borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '0.85rem'
          }}
        >
          🔄 Refresh
        </button>
      </div>

      {/* Pools List */}
      <div style={{ 
        maxHeight: 'calc(100vh - 250px)', 
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        marginTop: '0.5rem'
      }}>
        {Array.isArray(pools) && pools.map((pool, index) => {
          if (!pool) return null;
          
          const uniqueKey = `pool-${pool.address || pool.poolAddress || pool.id || index}`;
          const isPoolSelected = isSelected(pool);
          
          return (
            <div
              key={uniqueKey}
              onClick={() => handlePoolClick(pool)}
              style={{
                padding: '0.75rem',
                background: isPoolSelected ? '#667eea' : 'white',
                border: `1px solid ${isPoolSelected ? '#667eea' : '#e0e0e0'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                color: isPoolSelected ? 'white' : '#333',
                ':hover': {
                  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                  transform: 'translateY(-2px)'
                }
              }}
              onMouseEnter={(e) => {
                if (!isPoolSelected) {
                  e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
                  e.target.style.transform = 'translateY(-2px)';
                  e.target.style.borderColor = '#667eea';
                }
              }}
              onMouseLeave={(e) => {
                if (!isPoolSelected) {
                  e.target.style.boxShadow = 'none';
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.borderColor = '#e0e0e0';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                {/* Ranking */}
                <div style={{ 
                  background: '#667eea',
                  color: 'white',
                  borderRadius: '50%',
                  width: '24px',
                  height: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.8rem',
                  fontWeight: 'bold',
                  flexShrink: 0
                }}>
                  {pool.rank || index + 1}
                </div>

                {/* Pool Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ 
                    fontWeight: '600', 
                    fontSize: '0.95rem', 
                    color: isPoolSelected ? 'white' : '#333',
                    marginBottom: '0.25rem'
                  }}>
                    {pool.pair || `${pool.mainToken?.symbol || '?'}/${pool.sideToken?.symbol || '?'}`}
                  </div>
                  
                  <div style={{ 
                    display: 'flex', 
                    gap: '1rem', 
                    fontSize: '0.75rem', 
                    color: isPoolSelected ? 'rgba(255,255,255,0.8)' : '#666',
                    flexWrap: 'wrap'
                  }}>
                    <span>🏪 {pool.exchange?.name || 'Unknown DEX'}</span>
                    <span>🏊 {formatAddress(pool.poolAddress || pool.address)}</span>
                    <span>📅 {formatDate(pool.createdAt || pool.creationTime)}</span>
                    {pool.fee > 0 && <span>💳 {pool.fee}%</span>}
                  </div>
                </div>

                {/* Selection Indicator */}
                {isPoolSelected && (
                  <div style={{ 
                    color: '#667eea', 
                    fontSize: '1.2rem',
                    flexShrink: 0
                  }}>
                    ✓
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty State */}
      {(!pools || pools.length === 0) && !loading && (
        <div style={{ 
          textAlign: 'center', 
          padding: '3rem 1rem', 
          color: '#666'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🏊‍♂️</div>
          <div style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>No hot pools found</div>
          <div style={{ fontSize: '0.9rem' }}>Try refreshing to get the latest data</div>
        </div>
      )}
    </div>
  );
};

export default HotPoolsPanelSimple;