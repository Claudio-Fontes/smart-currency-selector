import React from 'react';

const PositionsSummary = ({ summary, lastUpdate }) => {
    const formatCurrency = (value) => {
        if (!value) return '$0.00';
        if (Math.abs(value) < 1) {
            return `$${value.toFixed(2)}`;
        }
        return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    };

    const getPnLColor = (percentage) => {
        if (percentage >= 10) return '#4ade80';
        if (percentage >= 0) return '#06b6d4';
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

    if (!summary) {
        return (
            <div className="positions-summary loading">
                <div className="summary-title">📊 Carregando estatísticas...</div>
            </div>
        );
    }

    return (
        <div className="positions-summary">
            <div className="summary-header">
                <div className="summary-title">📊 ESTATÍSTICAS GERAIS</div>
                {lastUpdate && (
                    <div className="last-update">
                        🕐 Atualizado: {formatTime(lastUpdate)}
                    </div>
                )}
            </div>

            <div className="summary-stats">
                <div className="stat-item">
                    <div className="stat-label">💰 Total Investido:</div>
                    <div className="stat-value">{formatCurrency(summary.total_investment)}</div>
                </div>

                <div className="stat-item">
                    <div className="stat-label">💎 Valor Atual:</div>
                    <div className="stat-value">{formatCurrency(summary.total_current_value)}</div>
                </div>

                <div className="stat-item pnl-item">
                    <div className="stat-label">📈 P&L Total:</div>
                    <div 
                        className="stat-value pnl-value"
                        style={{ color: getPnLColor(summary.total_pnl_percentage) }}
                    >
                        {formatCurrency(summary.total_pnl_amount)} ({summary.total_pnl_percentage >= 0 ? '+' : ''}{summary.total_pnl_percentage.toFixed(2)}%)
                    </div>
                </div>
            </div>

            <div className="summary-positions">
                <div className="positions-count">
                    <span className="count-label">🟢 Posições lucrativas:</span>
                    <span className="count-value">
                        {summary.profitable_positions}/{summary.total_positions} ({summary.win_rate_pct.toFixed(1)}%)
                    </span>
                </div>
            </div>

            <div className="summary-status">
                <div className="status-indicator">
                    <span className={`status-dot ${summary.total_pnl_percentage >= 0 ? 'positive' : 'negative'}`}></span>
                    <span className="status-text">
                        {summary.total_positions} posições abertas
                    </span>
                </div>
            </div>
        </div>
    );
};

export default PositionsSummary;