import React from 'react';
import '../styles/ticker.css';

const TickerBar = ({ positions }) => {
    if (!positions || positions.length === 0) {
        return (
            <div className="ticker-container">
                <div className="ticker-content">
                    <div className="ticker-item">
                        📊 Nenhuma posição ativa no momento...
                    </div>
                </div>
            </div>
        );
    }

    // Duplicar as posições para criar um loop infinito suave
    const duplicatedPositions = [...positions, ...positions, ...positions];

    return (
        <div className="ticker-container">
            <div className="ticker-content">
                {duplicatedPositions.map((position, index) => (
                    <div key={`${position.id}-${index}`} className="ticker-item">
                        <span className="ticker-emoji">{position.status_emoji}</span>
                        <span className="ticker-symbol">{position.symbol}</span>
                        <span className="ticker-price">${position.current_price?.toFixed(8)}</span>
                        <span className={`ticker-change ${position.pnl_percentage >= 0 ? 'positive' : 'negative'}`}>
                            {position.pnl_percentage >= 0 ? '+' : ''}{position.pnl_percentage?.toFixed(2)}%
                        </span>
                        <span className="ticker-value">${position.current_value_usd?.toFixed(2)}</span>
                        <span className="ticker-separator">•</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TickerBar;