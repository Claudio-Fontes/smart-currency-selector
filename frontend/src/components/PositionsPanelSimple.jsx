import React from 'react';
import usePositions from '../hooks/usePositions';

const PositionsPanelSimple = () => {
    console.log('🏛️ PositionsPanelSimple: Component mounted');
    const { positions, summary, loading, error, lastUpdate, refetch } = usePositions(60000); // 60 segundos
    
    console.log('🏛️ PositionsPanelSimple:', { positions: positions?.length, summary, loading, error });

    if (loading) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
                <div style={{ fontSize: '1.2rem', color: '#666', marginBottom: '1rem' }}>
                    ⏳ Loading positions...
                </div>
                <div style={{ fontSize: '0.9rem', color: '#888' }}>
                    Getting your trading positions
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
                    onClick={refetch}
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

    const formatPrice = (price) => {
        if (!price) return '$0.00';
        if (price < 0.0001) {
            return `$${price.toFixed(8)}`;
        } else if (price < 0.1) {
            return `$${price.toFixed(6)}`;
        }
        return `$${price.toFixed(4)}`;
    };

    const formatCurrency = (value) => {
        if (!value) return '$0.00';
        if (Math.abs(value) < 1) {
            return `$${value.toFixed(2)}`;
        }
        return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const formatTokenAmount = (amount) => {
        if (!amount) return '0';
        if (amount > 1000000) {
            return `${(amount / 1000000).toFixed(1)}M`;
        } else if (amount > 1000) {
            return `${(amount / 1000).toFixed(1)}K`;
        }
        return amount.toLocaleString(undefined, { maximumFractionDigits: 0 });
    };

    const getPnLColor = (percentage) => {
        if (percentage >= 20) return '#00ff88';
        if (percentage >= 10) return '#4ade80';
        if (percentage >= 0) return '#06b6d4';
        if (percentage >= -5) return '#f97316';
        return '#ef4444';
    };

    const formatTime = (date) => {
        if (!date) return '';
        return date.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
    };

    return (
        <div style={{ padding: '1rem', height: '100%' }}>
            {/* Header */}
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '1.5rem',
                paddingBottom: '1rem',
                borderBottom: '1px solid #e0e0e0'
            }}>
                <div>
                    <h2 style={{ margin: 0, fontSize: '1.3rem', color: '#333' }}>
                        📊 Trading Positions
                    </h2>
                    <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
                        {lastUpdate ? `Last update: ${formatTime(lastUpdate)}` : 'Real-time data'}
                    </div>
                </div>
                <button 
                    onClick={refetch}
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

            {/* Summary */}
            {summary && (
                <div style={{ 
                    background: 'white',
                    borderRadius: '8px',
                    padding: '1rem',
                    marginBottom: '1.5rem',
                    border: '2px solid #667eea',
                    boxShadow: '0 4px 12px rgba(102, 126, 234, 0.1)'
                }}>
                    <div style={{ 
                        fontSize: '1rem', 
                        fontWeight: '600', 
                        marginBottom: '0.75rem',
                        color: '#333'
                    }}>
                        📊 Portfolio Summary
                    </div>
                    
                    <div style={{ 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', 
                        gap: '0.75rem',
                        fontSize: '0.85rem'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ color: '#666', marginBottom: '0.25rem' }}>Invested</div>
                            <div style={{ fontWeight: '600', color: '#333' }}>
                                {formatCurrency(summary.total_investment)}
                            </div>
                        </div>
                        
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ color: '#666', marginBottom: '0.25rem' }}>Current Value</div>
                            <div style={{ fontWeight: '600', color: '#333' }}>
                                {formatCurrency(summary.total_current_value)}
                            </div>
                        </div>
                        
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ color: '#666', marginBottom: '0.25rem' }}>P&L</div>
                            <div style={{ 
                                fontWeight: '600', 
                                color: getPnLColor(summary.total_pnl_percentage)
                            }}>
                                {formatCurrency(summary.total_pnl_amount)} ({summary.total_pnl_percentage >= 0 ? '+' : ''}{summary.total_pnl_percentage.toFixed(2)}%)
                            </div>
                        </div>
                        
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ color: '#666', marginBottom: '0.25rem' }}>Win Rate</div>
                            <div style={{ fontWeight: '600', color: '#333' }}>
                                {summary.profitable_positions}/{summary.total_positions} ({summary.win_rate_pct.toFixed(1)}%)
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Positions List */}
            {positions.length === 0 ? (
                <div style={{ 
                    textAlign: 'center', 
                    padding: '3rem 1rem', 
                    color: '#666'
                }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
                    <div style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>No open positions</div>
                    <div style={{ fontSize: '0.9rem' }}>Your trading positions will appear here</div>
                </div>
            ) : (
                <>
                    <div style={{ 
                        fontSize: '1rem', 
                        fontWeight: '600', 
                        marginBottom: '1rem',
                        color: '#333'
                    }}>
                        📈 {positions.length} Open Positions:
                    </div>

                    <div style={{ 
                        maxHeight: 'calc(100vh - 400px)', 
                        overflowY: 'auto',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '0.75rem'
                    }}>
                        {positions.map((position, index) => (
                            <div
                                key={position.id}
                                style={{
                                    background: 'white',
                                    border: '1px solid #e0e0e0',
                                    borderRadius: '8px',
                                    padding: '1rem',
                                    transition: 'all 0.2s ease'
                                }}
                                onMouseEnter={(e) => {
                                    e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
                                    e.target.style.borderColor = '#667eea';
                                }}
                                onMouseLeave={(e) => {
                                    e.target.style.boxShadow = 'none';
                                    e.target.style.borderColor = '#e0e0e0';
                                }}
                            >
                                {/* Position Header */}
                                <div style={{ 
                                    display: 'flex', 
                                    justifyContent: 'space-between', 
                                    alignItems: 'center',
                                    marginBottom: '0.75rem'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ fontSize: '1.2rem' }}>{position.status_emoji}</span>
                                        <span style={{ fontWeight: '600', fontSize: '1.1rem', color: '#333' }}>
                                            {position.symbol}
                                        </span>
                                        <span style={{ 
                                            fontWeight: '600', 
                                            fontSize: '0.9rem',
                                            color: getPnLColor(position.pnl_percentage)
                                        }}>
                                            {position.pnl_percentage >= 0 ? '+' : ''}{position.pnl_percentage.toFixed(2)}%
                                        </span>
                                    </div>
                                    <span style={{ fontSize: '0.8rem', color: '#666' }}>
                                        {position.time_held_display}
                                    </span>
                                </div>

                                {/* Price Info */}
                                <div style={{ 
                                    display: 'flex', 
                                    justifyContent: 'space-between',
                                    fontSize: '0.85rem',
                                    color: '#666',
                                    marginBottom: '0.5rem'
                                }}>
                                    <span>💰 Buy: {formatPrice(position.buy_price)}</span>
                                    <span>→ Current: {formatPrice(position.current_price)}</span>
                                </div>

                                {/* Amount & Value */}
                                <div style={{ 
                                    display: 'flex', 
                                    justifyContent: 'space-between',
                                    fontSize: '0.85rem',
                                    marginBottom: '0.5rem'
                                }}>
                                    <span style={{ color: '#666' }}>
                                        📊 {formatTokenAmount(position.tokens_amount)} tokens
                                    </span>
                                    <span style={{ color: '#333', fontWeight: '500' }}>
                                        💵 {formatCurrency(position.investment_usd)} invested
                                    </span>
                                </div>

                                {/* P&L */}
                                <div style={{ 
                                    display: 'flex', 
                                    justifyContent: 'space-between',
                                    alignItems: 'center'
                                }}>
                                    <span style={{ 
                                        fontSize: '0.75rem', 
                                        color: '#666', 
                                        fontFamily: 'monospace'
                                    }}>
                                        🔗 {position.address.slice(0, 8)}...{position.address.slice(-8)}
                                    </span>
                                    <span style={{ 
                                        fontSize: '0.9rem',
                                        fontWeight: '600',
                                        color: getPnLColor(position.pnl_percentage)
                                    }}>
                                        📈 {formatCurrency(position.pnl_amount)}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}

            {/* Auto-refresh info */}
            <div style={{ 
                textAlign: 'center', 
                fontSize: '0.75rem', 
                color: '#888',
                marginTop: '1rem',
                padding: '0.5rem'
            }}>
                ⏱️ Auto-refresh every 60 seconds
            </div>
        </div>
    );
};

export default PositionsPanelSimple;