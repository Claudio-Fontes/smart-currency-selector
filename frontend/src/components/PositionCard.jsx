import React from 'react';

const PositionCard = ({ position }) => {
    const formatPrice = (price) => {
        if (price < 0.0001) {
            return `$${price.toFixed(8)}`;
        } else if (price < 0.1) {
            return `$${price.toFixed(6)}`;
        }
        return `$${price.toFixed(4)}`;
    };

    const formatCurrency = (value) => {
        if (Math.abs(value) < 1) {
            return `$${value.toFixed(2)}`;
        }
        return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const formatTokenAmount = (amount) => {
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

    const truncateAddress = (address) => {
        if (!address) return '';
        return `${address.slice(0, 8)}...${address.slice(-8)}`;
    };

    return (
        <div className="position-card">
            <div className="position-header">
                <div className="token-info">
                    <span className="status-emoji">{position.status_emoji}</span>
                    <span className="token-symbol">{position.symbol}</span>
                    <span 
                        className="pnl-percentage" 
                        style={{ color: getPnLColor(position.pnl_percentage) }}
                    >
                        {position.pnl_percentage >= 0 ? '+' : ''}{position.pnl_percentage.toFixed(2)}%
                    </span>
                </div>
                <div className="time-held">{position.time_held_display}</div>
            </div>

            <div className="price-info">
                <div className="price-row">
                    <span>💰 Buy: {formatPrice(position.buy_price)}</span>
                    <span>→ Atual: {formatPrice(position.current_price)}</span>
                </div>
            </div>

            <div className="amount-info">
                <span>📊 {formatTokenAmount(position.tokens_amount)} tokens</span>
                <span className="decimals-info">(decimals: {position.decimals})</span>
            </div>

            <div className="value-info">
                <div className="investment-row">
                    <span>💵 Investido: {formatCurrency(position.investment_usd)}</span>
                </div>
                <div className="pnl-row">
                    <span 
                        className="pnl-amount"
                        style={{ color: getPnLColor(position.pnl_percentage) }}
                    >
                        📈 P&L: {formatCurrency(position.pnl_amount)} ({position.pnl_percentage >= 0 ? '+' : ''}{position.pnl_percentage.toFixed(2)}%)
                    </span>
                </div>
            </div>

            <div className="address-info">
                <span className="address-label">🔗 {truncateAddress(position.address)}</span>
            </div>
        </div>
    );
};

export default PositionCard;